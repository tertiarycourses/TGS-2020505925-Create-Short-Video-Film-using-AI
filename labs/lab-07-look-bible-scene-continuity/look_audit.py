#!/usr/bin/env python3
"""Lab 07 — audit a sequence against its look bible with GLOBAL descriptors.

Every shot is reduced to a numeric fingerprint of the whole frame:
  statistical  2-D hue/saturation histogram (Bhattacharyya distance to the master),
               mean brightness, contrast (std of V), mean saturation, warmth (R - B),
               tint (G - (R+B)/2: negative = magenta, positive = green)
  geometrical  Hu moments of the bright-practicals mask (where the light sits),
               edge density (how busy the frame is)
Shots that leave the look bible are flagged with the descriptor that moved, and the
shot-to-shot jump shows where a cut will feel like a different film.

Usage:
    python3 look_audit.py --sequence reference/sequence \
        --manifest data/sequence-manifest.csv --bible data/look-bible.json --out out

Each shot is compared with the approved master of ITS OWN location (the bible lists
one master per location): a market shot and a pier shot are allowed to differ from
each other, but not from their own approved look.

Requires: opencv-python, numpy.
"""
import argparse
import csv
import glob
import json
import math
import os

import cv2
import numpy as np

BANNER = 24


def fingerprint(img):
    img = img[BANNER:]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
    cv2.normalize(hist, hist, 1.0, 0.0, cv2.NORM_L1)
    v = hsv[..., 2].astype(np.float32)
    f = img.astype(np.float32)
    bright = (v > 220).astype(np.uint8)
    hu = cv2.HuMoments(cv2.moments(bright, binaryImage=True)).ravel()
    hu = [-math.copysign(1.0, h) * math.log10(abs(h)) if h != 0 else 0.0 for h in hu]
    edges = cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 60, 150)
    return {"hist": hist, "mean_v": float(v.mean()), "contrast": float(v.std()),
            "mean_s": float(hsv[..., 1].mean()),
            "warmth": float((f[..., 2] - f[..., 0]).mean()),
            "tint": float((f[..., 1] - (f[..., 2] + f[..., 0]) / 2).mean()),
            "hu": np.array(hu[:3]), "edge_density": float(np.count_nonzero(edges)) / edges.size}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sequence", default="reference/sequence")
    ap.add_argument("--manifest", default="data/sequence-manifest.csv")
    ap.add_argument("--bible", default="data/look-bible.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()
    bible = json.load(open(args.bible))
    lim = bible["limits"]
    masters = {}
    for loc, path in bible["masters"].items():
        img = cv2.imread(path)
        if img is None:
            raise SystemExit(f"cannot read master {path}")
        masters[loc] = fingerprint(img)
        m = masters[loc]
        print(f"MASTER {loc:7} V {m['mean_v']:.1f}  contrast {m['contrast']:.1f}  "
              f"S {m['mean_s']:.1f}  warmth {m['warmth']:.1f}  tint {m['tint']:.1f}")
    manifest = {r["shot"]: r["location"] for r in csv.DictReader(open(args.manifest))}
    paths = sorted(glob.glob(os.path.join(args.sequence, "shot_*.png")))
    if not paths:
        raise SystemExit(f"no shots in {args.sequence}")
    missing = [os.path.basename(p) for p in paths if os.path.basename(p) not in manifest]
    if missing:
        raise SystemExit(f"shots missing from the manifest: {missing}")
    os.makedirs(args.out, exist_ok=True)
    rows, prev = [], None
    for p in paths:
        f = fingerprint(cv2.imread(p))
        loc = manifest[os.path.basename(p)]
        m = masters[loc]
        r = {"shot": os.path.basename(p), "location": loc,
             "hist_dist": round(cv2.compareHist(m["hist"], f["hist"], cv2.HISTCMP_BHATTACHARYYA), 3),
             "d_mean_v": round(f["mean_v"] - m["mean_v"], 1),
             "d_contrast": round(f["contrast"] - m["contrast"], 1),
             "d_mean_s": round(f["mean_s"] - m["mean_s"], 1),
             "d_warmth": round(f["warmth"] - m["warmth"], 1),
             "d_tint": round(f["tint"] - m["tint"], 1),
             "hu_dist": round(float(np.abs(f["hu"] - m["hu"]).sum()), 2),
             "edge_density": round(f["edge_density"], 3),
             "jump_from_prev": round(cv2.compareHist(prev["hist"], f["hist"],
                                                     cv2.HISTCMP_BHATTACHARYYA), 3) if prev else ""}
        why = []
        if r["hist_dist"] > lim["max_hist_dist"]:
            why.append(f"palette ({r['hist_dist']})")
        if abs(r["d_mean_v"]) > lim["max_abs_d_mean_v"]:
            why.append(f"exposure ({r['d_mean_v']:+})")
        if abs(r["d_warmth"]) > lim["max_abs_d_warmth"]:
            why.append(f"white balance ({r['d_warmth']:+})")
        if abs(r["d_tint"]) > lim["max_abs_d_tint"]:
            why.append(f"tint ({r['d_tint']:+})")
        if abs(r["d_mean_s"]) > lim["max_abs_d_mean_s"]:
            why.append(f"saturation ({r['d_mean_s']:+})")
        r["verdict"] = "ON LOOK" if not why else "OFF LOOK: " + ", ".join(why)
        rows.append(r)
        prev = f
        print(f"{r['shot']} {loc:6}  hist {r['hist_dist']:.3f}  dV {r['d_mean_v']:+6.1f}  "
              f"dS {r['d_mean_s']:+6.1f}  dWarm {r['d_warmth']:+6.1f}  dTint {r['d_tint']:+6.1f}  hu {r['hu_dist']:5.2f}  "
              f"jump {str(r['jump_from_prev']):>5}  ->  {r['verdict']}")
    with open(os.path.join(args.out, "look-report.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    strip = []
    for p, r in zip(paths, rows):
        t = cv2.resize(cv2.imread(p), (240, 135))
        cv2.rectangle(t, (0, 0), (239, 134), (0, 170, 0) if r["verdict"] == "ON LOOK"
                      else (0, 0, 230), 5)
        strip.append(t)
    cv2.imwrite(os.path.join(args.out, "look-strip.png"),
                np.vstack([np.hstack(strip[i:i + 4]) for i in range(0, len(strip), 4)]))
    print(f"\nWritten: {args.out}/look-report.csv, look-strip.png")


if __name__ == "__main__":
    main()
