#!/usr/bin/env python3
"""Lab 10 — video analytics on an assembled sequence of generated shots.

  1 cuts     shot boundaries from the colour-histogram distance between frames
  2 motion   camera movement per shot: Lucas-Kanade feature flow on the background,
             subject excluded, with a RANSAC-fitted global translation
  3 flicker  frame-to-frame luminance jumps inside each shot
  4 track    CAMShift on the hue back-projection of MEI's yellow raincoat,
             scored against the exact truth boxes (IoU, centroid error, jitter)
  5 drift    raincoat hue over time inside each tracked shot (identity drift)
  6 event    the first frame MEI appears (an event for the edit decision list)

Usage:
    python3 continuity.py --clip reference/generated-sequence.mp4 \
        --truth data/sequence-truth.json --config data/analytics-config.json --out out

Requires: opencv-python, numpy.
"""
import argparse
import csv
import json
import os

import cv2
import numpy as np

BANNER = 24


def iou(a, b):
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw = max(0, min(ax2, bx2) - max(a[0], b[0]))
    ih = max(0, min(ay2, by2) - max(a[1], b[1]))
    inter = iw * ih
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union else 0.0


def read_all(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"cannot open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        f[:BANNER] = 0                      # the provenance banner is not picture
        frames.append(f)
    return frames, fps


def coat_mask(hsv, cfg):
    return cv2.inRange(hsv, tuple(cfg["coat_hsv_lo"]), tuple(cfg["coat_hsv_hi"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", default="reference/generated-sequence.mp4")
    ap.add_argument("--truth", default="data/sequence-truth.json")
    ap.add_argument("--config", default="data/analytics-config.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    truth = json.load(open(args.truth))
    frames, fps = read_all(args.clip)
    n = len(frames)
    os.makedirs(args.out, exist_ok=True)
    hsvs = [cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in frames]
    # subject boxes: exact truth here; in production, the Lab 08 detector or the tracker
    boxes = {int(k): v for k, v in truth["mei_boxes"].items()}
    print(f"{n} frames at {fps:.0f} fps = {n / fps:.2f}s")

    # 1 ---- cuts: two signals must agree ---------------------------------------
    # (a) the pixel difference jumps well above its own recent level (adaptive), and
    # (b) the colour histogram changes too - a flicker changes brightness, not palette.
    grays = [cv2.cvtColor(cv2.resize(f, (320, 180)), cv2.COLOR_BGR2GRAY).astype(np.float32)
             for f in frames]
    pix = [0.0] + [float(np.abs(grays[i] - grays[i - 1]).mean()) for i in range(1, n)]
    hists = []
    for h in hsvs:
        hist = cv2.calcHist([h], [0, 1], None, [30, 32], [0, 180, 0, 256])
        hists.append(cv2.normalize(hist, hist, 1, 0, cv2.NORM_L1))
    dist = [0.0] + [cv2.compareHist(hists[i - 1], hists[i], cv2.HISTCMP_BHATTACHARYYA)
                    for i in range(1, n)]
    cuts = []
    for i in range(1, n):
        recent = np.median(pix[max(1, i - cfg["cut_window"]):i]) if i > 1 else 0.0
        if pix[i] > max(cfg["cut_min_diff"], cfg["cut_ratio"] * recent) and \
                dist[i] > cfg["cut_min_hist"]:
            cuts.append(i)
    bounds = [0] + cuts + [n]
    shots = [(bounds[k], bounds[k + 1] - 1) for k in range(len(bounds) - 1)]
    tc = truth["cuts_at_frame"]
    hit = sum(any(abs(c - t) <= 1 for c in cuts) for t in tc)
    print(f"\n1 CUTS  detected at {cuts}   truth {tc}   ->  {hit}/{len(tc)} found, "
          f"{len(cuts) - hit} false")

    # 2-3 ---- motion and flicker per shot -------------------------------------
    rows = []
    for k, (a, b) in enumerate(shots, 1):
        # camera motion = the dominant translation of BACKGROUND features: track corners
        # with Lucas-Kanade, drop those on the subject, fit a RANSAC similarity transform
        dx = []
        for i in range(a + 1, b + 1, cfg["flow_step"]):
            g0 = cv2.cvtColor(frames[i - 1], cv2.COLOR_BGR2GRAY)
            g1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            mask = np.full(g0.shape, 255, np.uint8)
            mask[:BANNER] = 0
            if (i - 1) in boxes:                            # exclude the subject
                x, y, w, h = boxes[i - 1]
                mask[max(0, y - 20):y + h + 20, max(0, x - 20):x + w + 20] = 0
            p0 = cv2.goodFeaturesToTrack(g0, 300, 0.01, 8, mask=mask)
            if p0 is None or len(p0) < cfg["min_bg_features"]:
                continue
            p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, p0, None)
            ok = st.ravel() == 1
            if ok.sum() < cfg["min_bg_features"]:
                continue
            M, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC,
                                               ransacReprojThreshold=1.5)
            if M is not None:
                dx.append(float(M[0, 2]))
        med_dx = float(np.median(dx)) if dx else 0.0
        camera = ("pan right" if med_dx < -cfg["pan_px"] else "pan left" if med_dx > cfg["pan_px"]
                  else "static")
        lum = np.array([cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)[BANNER:].mean()
                        for i in range(a, b + 1)])
        flick = float(np.abs(np.diff(lum)).mean()) if len(lum) > 1 else 0.0
        rows.append({"shot": f"S{k}", "start": a, "end": b, "seconds": round((b - a + 1) / fps, 2),
                     "median_dx_px": round(med_dx, 2), "camera": camera,
                     "flicker_index": round(flick, 2),
                     "flicker": "FLICKER" if flick > cfg["flicker_threshold"] else "ok"})
    print("\n2-3 MOTION AND FLICKER")
    for r in rows:
        print(f"  {r['shot']}  frames {r['start']:3}-{r['end']:3}  {r['seconds']:5}s  "
              f"background dx {r['median_dx_px']:+6.2f} px/frame -> {r['camera']:9}  flicker "
              f"{r['flicker_index']:5.2f} {r['flicker']}")

    # 4-6 ---- tracking, drift and events --------------------------------------
    def largest_blob(m):
        k, _, st, _ = cv2.connectedComponentsWithStats(m)
        return int(st[1:, cv2.CC_STAT_AREA].max()) if k > 1 else 0
    present = [i for i in range(n) if largest_blob(coat_mask(hsvs[i], cfg)) > cfg["appear_px"]]
    first = present[0] if present else None
    print(f"\n6 EVENT  MEI first appears at frame {first} ({first / fps:.2f}s); truth "
          f"{truth['mei_first_frame']}")
    print("\n4-5 TRACKING AND IDENTITY DRIFT")
    track_rows = []
    for r in rows:
        a, b = r["start"], r["end"]
        idx = [i for i in range(a, b + 1) if i in boxes]
        if len(idx) < 10:
            continue
        x, y, w, h = boxes[idx[0]]                    # initialise from the first truth box
        roi = hsvs[idx[0]][y:y + h, x:x + w]
        m = coat_mask(roi, cfg)
        hist = cv2.calcHist([roi], [0], m, [180], [0, 180])
        cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
        win = (x, y, w, h)
        crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
        ious, errs, cxs, hues = [], [], [], []
        for i in idx:
            bp = cv2.calcBackProject([hsvs[i]], [0], hist, [0, 180], 1)
            bp &= coat_mask(hsvs[i], {"coat_hsv_lo": [0, 120, 120], "coat_hsv_hi": [180, 255, 255]})
            rot, win = cv2.CamShift(bp, win, crit)
            tb = boxes[i]
            pts = cv2.boxPoints(rot)
            px, py = pts[:, 0].mean(), pts[:, 1].mean()
            tx, ty = tb[0] + tb[2] / 2, tb[1] + tb[3] / 2
            # the tracker follows the coat, so score the centre and the horizontal overlap
            errs.append(float(np.hypot(px - tx, 0)))
            ious.append(iou([win[0], tb[1], win[2], tb[3]], tb))
            cxs.append(px)
            cm = cv2.inRange(hsvs[i], tuple(cfg["drift_hsv_lo"]), tuple(cfg["drift_hsv_hi"])) > 0
            sub = np.zeros_like(cm)
            sub[tb[1]:tb[1] + tb[3], tb[0]:tb[0] + tb[2]] = True
            sel = hsvs[i][..., 0][cm & sub]
            hues.append(float(np.median(sel)) if sel.size else np.nan)
        jitter = float(np.std(np.diff(np.diff(cxs)))) if len(cxs) > 3 else 0.0
        hues = np.array(hues)
        ok = ~np.isnan(hues)
        slope = float(np.polyfit(np.arange(len(hues))[ok], hues[ok], 1)[0] * fps) if ok.sum() > 2 else 0.0
        drift = float(np.nanmax(hues) - np.nanmin(hues))
        tr = {"shot": r["shot"], "frames": len(idx), "mean_iou_x": round(float(np.mean(ious)), 3),
              "mean_centre_err_px": round(float(np.mean(errs)), 1),
              "centroid_jitter_px": round(jitter, 2), "coat_hue_start": round(float(hues[ok][0]), 1),
              "coat_hue_end": round(float(hues[ok][-1]), 1), "hue_slope_per_s": round(slope, 2),
              "identity": "DRIFT" if drift > cfg["hue_drift_limit"] else "stable"}
        track_rows.append(tr)
        print(f"  {tr['shot']}  {tr['frames']} frames  IoU(x) {tr['mean_iou_x']}  centre err "
              f"{tr['mean_centre_err_px']} px  jitter {tr['centroid_jitter_px']} px  coat hue "
              f"{tr['coat_hue_start']} -> {tr['coat_hue_end']} ({tr['hue_slope_per_s']:+}/s) "
              f"-> {tr['identity']}")

    for name, data in (("shot-report.csv", rows), ("tracking-report.csv", track_rows)):
        with open(os.path.join(args.out, name), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    # timeline graphic: histogram distance per frame with cuts and flagged shots
    W, H = 960, 220
    g = np.full((H, W, 3), 255, np.uint8)
    for r in rows:
        x0, x1 = int(r["start"] * W / n), int((r["end"] + 1) * W / n)
        col = (200, 200, 255) if r["flicker"] != "ok" else (235, 235, 235)
        if any(t["shot"] == r["shot"] and t["identity"] == "DRIFT" for t in track_rows):
            col = (160, 220, 255)
        cv2.rectangle(g, (x0, 30), (x1, H - 20), col, -1)
        cv2.putText(g, r["shot"], (x0 + 4, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    for i in range(1, n):
        x = int(i * W / n)
        cv2.line(g, (x, H - 20), (x, H - 20 - int(min(1.0, pix[i] / 50.0) * (H - 60))),
                 (180, 60, 0), 1)
    cv2.imwrite(os.path.join(args.out, "timeline.png"), g)
    json.dump({"cuts": cuts, "first_appearance_frame": first, "shots": rows, "tracking": track_rows},
              open(os.path.join(args.out, "continuity-report.json"), "w"), indent=2)
    print(f"\nWritten: {args.out}/shot-report.csv, tracking-report.csv, timeline.png, "
          "continuity-report.json")


if __name__ == "__main__":
    main()
