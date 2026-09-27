#!/usr/bin/env python3
"""Lab 05 — grading and enhancement, measured against the approved master.

Four typical defects of a raw generation (noise, soft focus, a flat 'log-like'
look, a half-resolution draft) are applied to the graded master. Each defect is
then repaired with several candidate filters and every result is scored with
PSNR and SSIM against the master. A separate step shows grading as a POINT
operation: a teal-and-orange look applied with a lookup table.

Usage:
    python3 grade_lab.py --master reference/graded-master.png \
        --degradations data/degradations.json --out out

Requires: opencv-python, numpy; ssim.py in the same folder.
"""
import argparse
import csv
import json
import os

import cv2
import numpy as np

from ssim import psnr, ssim

BANNER = 24


def degrade(img, d):
    rng = np.random.default_rng(d.get("seed", 7))
    if d["kind"] == "noise":
        n = rng.normal(0, d["sigma"], img.shape)
        return np.clip(img + n, 0, 255).astype(np.uint8)
    if d["kind"] == "blur":
        return cv2.GaussianBlur(img, (0, 0), d["sigma"])
    if d["kind"] == "flat":
        f = img.astype(np.float32) * d["contrast"] + d["lift"]
        return np.clip(f, 0, 255).astype(np.uint8)
    if d["kind"] == "halfres":
        h, w = img.shape[:2]
        return cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    raise ValueError(d["kind"])


def unsharp(img, sigma=1.5, amount=1.0):
    blur = cv2.GaussianBlur(img, (0, 0), sigma)
    return cv2.addWeighted(img, 1 + amount, blur, -amount, 0)


def clahe_l(img, clip=2.0):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    lab[..., 0] = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8)).apply(lab[..., 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def levels(img, black, white):
    lut = np.clip((np.arange(256) - black) * 255.0 / (white - black), 0, 255).astype(np.uint8)
    return cv2.LUT(img, lut)


def candidates(kind, x, full_size):
    w, h = full_size
    if kind == "noise":
        return {"gaussian_blur_s1.0": cv2.GaussianBlur(x, (0, 0), 1.0),
                "bilateral_d7": cv2.bilateralFilter(x, 7, 40, 7),
                "nlmeans_h8": cv2.fastNlMeansDenoisingColored(x, None, 8, 8, 7, 21)}
    if kind == "blur":
        return {"unsharp_a0.8": unsharp(x, 1.5, 0.8), "unsharp_a2.5": unsharp(x, 1.5, 2.5),
                "laplacian_kernel": cv2.filter2D(x, -1, np.array([[0, -1, 0], [-1, 5, -1],
                                                                  [0, -1, 0]], np.float32))}
    if kind == "flat":
        return {"clahe_L": clahe_l(x), "levels_36_214": levels(x, 36, 214),
                "levels_60_190": levels(x, 60, 190)}
    if kind == "halfres":
        return {"nearest_x2": cv2.resize(x, (w, h), interpolation=cv2.INTER_NEAREST),
                "cubic_x2": cv2.resize(x, (w, h), interpolation=cv2.INTER_CUBIC),
                "lanczos_x2+unsharp": unsharp(cv2.resize(x, (w, h),
                                                         interpolation=cv2.INTER_LANCZOS4), 1.0, 0.5)}
    raise ValueError(kind)


def teal_orange_lut(strength=0.35):
    """Point operation: shadows pushed to teal, highlights to orange (per channel LUT)."""
    v = np.arange(256, dtype=np.float32) / 255.0
    shadow = (1 - v) ** 2
    high = v ** 2
    b = np.clip(v + strength * (0.35 * shadow - 0.25 * high), 0, 1)
    g = np.clip(v + strength * (0.15 * shadow - 0.02 * high), 0, 1)
    r = np.clip(v + strength * (-0.30 * shadow + 0.30 * high), 0, 1)
    return [(c * 255).astype(np.uint8) for c in (b, g, r)]


def warmth(img):
    """Mean red minus mean blue in the shadows and in the highlights."""
    y = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sh, hi = y < 70, y > 170
    f = img.astype(np.float32)
    return (round(float((f[..., 2] - f[..., 0])[sh].mean()), 1),
            round(float((f[..., 2] - f[..., 0])[hi].mean()), 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="reference/graded-master.png")
    ap.add_argument("--degradations", default="data/degradations.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()
    master = cv2.imread(args.master)
    if master is None:
        raise SystemExit(f"cannot read {args.master}")
    master = master[BANNER:]                 # measure picture, not the label banner
    h, w = master.shape[:2]
    master = master[: h - h % 2, : w - w % 2]
    h, w = master.shape[:2]
    cfg = json.load(open(args.degradations))
    os.makedirs(args.out, exist_ok=True)

    rows, tiles = [], []
    for d in cfg["degradations"]:
        x = degrade(master, d)
        base = x if d["kind"] != "halfres" else cv2.resize(x, (w, h), interpolation=cv2.INTER_NEAREST)
        rows.append({"defect": d["name"], "method": "(unrepaired)",
                     "psnr_db": round(psnr(master, base), 2), "ssim": round(ssim(master, base), 4)})
        best = None
        for name, y in candidates(d["kind"], x, (w, h)).items():
            r = {"defect": d["name"], "method": name,
                 "psnr_db": round(psnr(master, y), 2), "ssim": round(ssim(master, y), 4)}
            rows.append(r)
            if best is None or r["ssim"] > best[0]["ssim"]:
                best = (r, y)
        tiles.append(np.hstack([cv2.resize(base, (320, 172)), cv2.resize(best[1], (320, 172))]))
        print(f"{d['name']:22} unrepaired SSIM {rows[-4]['ssim']:.4f}  ->  best "
              f"{best[0]['method']:20} SSIM {best[0]['ssim']:.4f}  PSNR {best[0]['psnr_db']} dB")

    with open(os.path.join(args.out, "enhancement-scores.csv"), "w", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wtr.writeheader()
        wtr.writerows(rows)
    cv2.imwrite(os.path.join(args.out, "before-after.png"), np.vstack(tiles))

    # grading as a point operation
    flat = degrade(master, {"kind": "flat", "contrast": 0.7, "lift": 30})
    lut = teal_orange_lut(cfg.get("look_strength", 0.35))
    graded = cv2.merge([cv2.LUT(c, l) for c, l in zip(cv2.split(levels(flat, 30, 208)), lut)])
    cv2.imwrite(os.path.join(args.out, "graded-look.png"), np.hstack([flat, graded]))
    print(f"\nLOOK (red minus blue: shadows, highlights)  flat {warmth(flat)}  ->  "
          f"graded {warmth(graded)}")
    print("A LUT maps every pixel on its own value: it cannot sharpen or denoise.")
    print(f"Written: {args.out}/enhancement-scores.csv, before-after.png, graded-look.png")


if __name__ == "__main__":
    main()
