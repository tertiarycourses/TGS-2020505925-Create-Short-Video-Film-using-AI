#!/usr/bin/env python3
"""Lab 04 — state variants, clean-up and reframing, verified with pixel evidence.

  inpaint   Remove a stray object (the orange cone) inside a mask and prove that
            nothing outside the mask moved.
  verify    Compare a location plate with its "same place, new story state" edit
            and find every region that changed OUTSIDE the permitted edit zone.
  reframe   Build the 9:16 canvas and the outpaint mask (white = generate) a
            generative-expand model needs, with a classical placeholder fill.

Mask convention in this course: WHITE (255) = editable, BLACK (0) = preserve.

Usage:
    python3 edit_lab.py inpaint --image reference/pier-docked.png --jobs data/edit-jobs.json
    python3 edit_lab.py verify  --before reference/pier-docked.png \
                                --after reference/pier-leaving-edit.png --jobs data/edit-jobs.json
    python3 edit_lab.py reframe --image reference/pier-docked.png --target 9:16

Requires: opencv-python, numpy.
"""
import argparse
import json
import os

import cv2
import numpy as np

BANNER = 24


def read(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"cannot read {path}")
    return img


def box_mask(shape, box, dilate=0):
    m = np.zeros(shape[:2], np.uint8)
    x, y, w, h = box
    m[y:y + h, x:x + w] = 255
    if dilate:
        m = cv2.dilate(m, np.ones((2 * dilate + 1, 2 * dilate + 1), np.uint8))
    return m


def inpaint(args, jobs):
    img = read(args.image)
    job = jobs["inpaint"]
    mask = box_mask(img.shape, job["box"], job.get("dilate_px", 0))
    os.makedirs(args.out, exist_ok=True)
    cv2.imwrite(os.path.join(args.out, "cone-mask.png"), mask)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lo, hi = tuple(job["target_hsv_lo"]), tuple(job["target_hsv_hi"])
    before = int(np.count_nonzero(cv2.inRange(hsv, lo, hi) & mask))
    print(f"target pixels inside the mask before: {before}")
    for name, flag in (("telea", cv2.INPAINT_TELEA), ("ns", cv2.INPAINT_NS)):
        out = cv2.inpaint(img, mask, job.get("radius", 5), flag)
        after = int(np.count_nonzero(cv2.inRange(cv2.cvtColor(out, cv2.COLOR_BGR2HSV), lo, hi)
                                     & mask))
        outside = mask == 0
        leak = float(np.abs(out.astype(int) - img.astype(int))[outside].max())
        cv2.imwrite(os.path.join(args.out, f"inpaint_{name}.png"), out)
        print(f"  {name:5}: target pixels left {after:5d}   max change OUTSIDE mask {leak:.0f} "
              f"({'preserved' if leak == 0 else 'LEAKED'})")
    print("Classical inpainting diffuses neighbouring pixels: fine for a cone on planks, "
          "wrong for a face. A generative inpaint uses the same mask contract.")


def verify(args, jobs):
    a, b = read(args.before), read(args.after)
    if a.shape != b.shape:
        raise SystemExit("before/after sizes differ - an edit must not resize the plate")
    job = jobs["verify"]
    allowed = box_mask(a.shape, job["allowed_box"])
    allowed[:BANNER] = 255                              # ignore the label banner
    diff = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
    diff = cv2.GaussianBlur(diff.astype(np.uint8), (5, 5), 0)
    # rain streaks are re-rendered in every frame; they are noise, not an edit
    changed = (diff > job["pixel_threshold"]).astype(np.uint8) * 255
    changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    inside = int(np.count_nonzero(changed & allowed))
    outside_mask = cv2.bitwise_not(allowed)
    out_px = changed & outside_mask
    outside = int(np.count_nonzero(out_px))
    frac = outside / max(1, int(np.count_nonzero(outside_mask)))
    n, _, stats, _ = cv2.connectedComponentsWithStats(out_px)
    regions = [[int(v) for v in stats[i, :4]] for i in range(1, n)
               if stats[i, cv2.CC_STAT_AREA] >= job["min_region_px"]]
    os.makedirs(args.out, exist_ok=True)
    heat = cv2.applyColorMap(cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX), cv2.COLORMAP_JET)
    x, y, w, h = job["allowed_box"]
    cv2.rectangle(heat, (x, y), (x + w, y + h), (255, 255, 255), 2)
    for rx, ry, rw, rh in regions:
        cv2.rectangle(heat, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 3)
    cv2.imwrite(os.path.join(args.out, "edit-heatmap.png"), heat)
    verdict = "ACCEPT" if frac <= job["max_outside_fraction"] and not regions else \
        "REGENERATE - the edit changed pixels it was told to preserve"
    print(f"changed pixels inside the permitted zone : {inside}")
    print(f"changed pixels outside it               : {outside} ({100 * frac:.3f}% of preserved area)")
    print(f"unrequested regions (>= {job['min_region_px']} px): {regions}")
    print(f"VERDICT: {verdict}")
    json.dump({"inside_px": inside, "outside_px": outside, "outside_fraction": frac,
               "regions": regions, "verdict": verdict},
              open(os.path.join(args.out, "edit-verify.json"), "w"), indent=2)


def reframe(args, jobs):
    img = read(args.image)[BANNER:]                     # the banner is not picture
    h, w = img.shape[:2]
    tw, th = (int(v) for v in args.target.split(":"))
    # A) centre crop: nothing generated, most of the frame lost
    cw = int(round(h * tw / th))
    x0 = (w - cw) // 2
    crop = img[:, x0:x0 + cw]
    # B) outpaint canvas: keep the full width, extend top and bottom
    ch = int(round(w * th / tw))
    pad = (ch - h) // 2
    canvas = cv2.copyMakeBorder(img, pad, ch - h - pad, 0, 0, cv2.BORDER_REFLECT)
    mask = np.zeros(canvas.shape[:2], np.uint8)
    mask[:pad] = 255
    mask[pad + h:] = 255
    blurred = cv2.GaussianBlur(canvas, (0, 0), 25)       # placeholder, clearly not detail
    filled = np.where(mask[..., None] == 255, blurred, canvas)
    os.makedirs(args.out, exist_ok=True)
    cv2.imwrite(os.path.join(args.out, "reframe_crop.png"), crop)
    cv2.imwrite(os.path.join(args.out, "outpaint_mask.png"), mask)
    cv2.imwrite(os.path.join(args.out, "outpaint_placeholder.png"), filled)
    kept = cw / w
    gen = np.count_nonzero(mask) / mask.size
    print(f"source {w}x{h}  target {tw}:{th}")
    print(f"  A centre crop  : {cw}x{h}, keeps {100 * kept:.1f}% of the width, generates 0%")
    print(f"  B outpaint     : {w}x{ch} canvas, keeps 100% of the source, must GENERATE "
          f"{100 * gen:.1f}% of the pixels (white in outpaint_mask.png)")
    print("Send outpaint_mask.png + the canvas to a generative-expand model; the blurred "
          "fill is only a placeholder so you can judge the composition.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("inpaint", "verify", "reframe"):
        p = sub.add_parser(name)
        p.add_argument("--jobs", default="data/edit-jobs.json")
        p.add_argument("--out", default="out")
        if name in ("inpaint", "reframe"):
            p.add_argument("--image", default="reference/pier-docked.png")
        if name == "verify":
            p.add_argument("--before", default="reference/pier-docked.png")
            p.add_argument("--after", default="reference/pier-leaving-edit.png")
        if name == "reframe":
            p.add_argument("--target", default="9:16")
    args = ap.parse_args()
    jobs = json.load(open(args.jobs))
    {"inpaint": inpaint, "verify": verify, "reframe": reframe}[args.cmd](args, jobs)


if __name__ == "__main__":
    main()
