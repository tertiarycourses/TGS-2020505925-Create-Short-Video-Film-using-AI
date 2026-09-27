#!/usr/bin/env python3
"""Lab 02 — read a still and a rough cut the way the machine does, then plan the
delivery formats: frame arrays, channel order, frame rate, duration, bitrate, and
what each aspect-ratio reframe keeps or throws away.

Usage:
    python3 inspect_clip.py --still reference/keyframe-shot2.png \
        --clip reference/rough-cut.mp4 --specs data/delivery-specs.json --out out

Requires: opencv-python, numpy.
"""
import argparse
import json
import math
import os

import cv2
import numpy as np


def aspect_label(w, h):
    g = math.gcd(w, h)
    return f"{w // g}:{h // g}"


def centre_crop_box(w, h, target_w, target_h):
    """Largest centre crop of a w x h frame that has the target aspect ratio."""
    ta = target_w / target_h
    if w / h > ta:                      # source is wider: keep full height
        cw, ch = int(round(h * ta)), h
    else:                               # source is taller: keep full width
        cw, ch = w, int(round(w / ta))
    return (w - cw) // 2, (h - ch) // 2, cw, ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", default="reference/keyframe-shot2.png")
    ap.add_argument("--clip", default="reference/rough-cut.mp4")
    ap.add_argument("--specs", default="data/delivery-specs.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    specs = json.load(open(args.specs))
    report = {}

    # ---- 1. a still is a typed 3-D array --------------------------------------
    img = cv2.imread(args.still, cv2.IMREAD_COLOR)
    if img is None:                     # imread returns None; it does not raise
        raise SystemExit(f"cannot read {args.still}")
    h, w, c = img.shape
    print(f"STILL  shape={img.shape} (H, W, C)  dtype={img.dtype}  bytes={img.nbytes:,}")
    chips = {}
    for k, name in enumerate(["blue", "green", "red", "white"]):
        x, y = 12 + k * 26 + 9, h - 34 + 9          # centre of each calibration chip
        bgr = [int(v) for v in img[y, x]]            # index is [row, col] = [y, x]
        rgb = bgr[::-1]
        hsv = [int(v) for v in cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0, 0]]
        chips[name] = {"xy": [x, y], "BGR": bgr, "RGB": rgb, "HSV": hsv}
        print(f"  chip {name:5} at (x={x}, y={y})  BGR={bgr}  RGB={rgb}  HSV={hsv}")
    report["still"] = {"shape": [h, w, c], "dtype": str(img.dtype), "bytes": int(img.nbytes),
                       "chips": chips}

    # ---- 2. a clip is frames plus a clock ------------------------------------
    cap = cv2.VideoCapture(args.clip)
    if not cap.isOpened():
        raise SystemExit(f"cannot open {args.clip}")
    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    declared = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    counted = len(frames)
    duration = counted / fps if fps else 0.0
    size = os.path.getsize(args.clip)
    bitrate = size * 8 / duration if duration else 0.0
    raw = fw * fh * 3 * fps                         # bytes per second, uncompressed
    clip = {"width": fw, "height": fh, "aspect": aspect_label(fw, fh), "fps": round(fps, 3),
            "frames_declared": declared, "frames_counted": counted,
            "duration_s": round(duration, 3), "file_bytes": size,
            "bitrate_kbps": round(bitrate / 1000, 1),
            "uncompressed_MB_per_s": round(raw / 1e6, 2),
            "compression_ratio": round(raw * 8 / bitrate, 1) if bitrate else None}
    report["clip"] = clip
    print(f"\nCLIP   {fw}x{fh} ({clip['aspect']})  {fps:.2f} fps  "
          f"{counted} frames counted ({declared} declared)  {duration:.2f} s")
    print(f"       file {size:,} bytes -> {clip['bitrate_kbps']} kbps;  uncompressed "
          f"{clip['uncompressed_MB_per_s']} MB/s;  compression about {clip['compression_ratio']}:1")

    # contact sheet: one frame per second
    thumbs = [cv2.resize(frames[i], (192, 108)) for i in range(0, counted, int(round(fps)))]
    while len(thumbs) % 6:
        thumbs.append(np.zeros_like(thumbs[0]))
    rows = [np.hstack(thumbs[i:i + 6]) for i in range(0, len(thumbs), 6)]
    cv2.imwrite(os.path.join(args.out, "contact-sheet.png"), np.vstack(rows))

    # ---- 3. delivery formats: what each reframe keeps --------------------------
    probe_t = specs.get("probe_second", 6.0)
    frame = frames[min(counted - 1, int(probe_t * fps))]
    print(f"\nDELIVERY PLAN (probe frame at {probe_t}s)")
    report["deliveries"] = []
    for d in specs["deliveries"]:
        x, y, cw, ch = centre_crop_box(fw, fh, d["w"], d["h"])
        kept = (cw * ch) / (fw * fh)
        crop = cv2.resize(frame[y:y + ch, x:x + cw], (d["w"] // 4, d["h"] // 4),
                          interpolation=cv2.INTER_AREA)
        sa = d.get("ui_safe", {"top": 0.05, "bottom": 0.05, "sides": 0.05})
        th, tw = crop.shape[:2]
        cv2.rectangle(crop, (int(tw * sa["sides"]), int(th * sa["top"])),
                      (int(tw * (1 - sa["sides"])), int(th * (1 - sa["bottom"]))),
                      (0, 255, 255), 1)
        cv2.imwrite(os.path.join(args.out, f"reframe_{d['name']}.png"), crop)
        upscale = d["h"] / ch
        row = {"name": d["name"], "target": f"{d['w']}x{d['h']}",
               "aspect": aspect_label(d["w"], d["h"]), "crop_box": [x, y, cw, ch],
               "pixels_kept_pct": round(100 * kept, 1),
               "upscale_needed": round(upscale, 2),
               "max_duration_s": d.get("max_s")}
        report["deliveries"].append(row)
        flag = "  <-- generate natively or keep action in the centre third" if kept < 0.5 else ""
        print(f"  {d['name']:14} {row['aspect']:5} crop {cw}x{ch} keeps "
              f"{row['pixels_kept_pct']:5.1f}% of the master, then x{row['upscale_needed']} "
              f"to {row['target']}{flag}")

    with open(os.path.join(args.out, "clip-report.json"), "w") as fh_:
        json.dump(report, fh_, indent=2)
    print(f"\nWritten: {args.out}/clip-report.json, contact-sheet.png, reframe_*.png")


if __name__ == "__main__":
    main()
