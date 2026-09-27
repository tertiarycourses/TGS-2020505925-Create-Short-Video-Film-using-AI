#!/usr/bin/env python3
"""Lab 03 — structured prompting for cinematic stills.

  compose   Lint a six-field shot specification (subject, action, environment,
            camera, style, constraints) and render it as prose, JSON and a
            negative prompt.
  variance  Measure how much four takes from each prompt design vary, so
            "lock more fields" becomes a number rather than an opinion.

Usage:
    python3 prompt_lab.py compose  --fields data/shot2-fields-v1.json --out out
    python3 prompt_lab.py variance --takes reference/takes --out out

Requires: opencv-python, numpy (variance only).
"""
import argparse
import csv
import glob
import json
import os
import re

FIELDS = ["subject", "action", "environment", "camera", "style", "constraints"]
# Pairs of terms that cannot both be true in one shot.
CONFLICTS = [("night", "noon"), ("night", "midday"), ("close-up", "wide shot"),
             ("static", "tracking"), ("static", "handheld"), ("dry", "rain"),
             ("black and white", "neon colour")]


def lint(spec):
    issues = []
    for f in FIELDS:
        if not str(spec.get(f, "")).strip():
            issues.append(f"MISSING field '{f}' - the model will invent it")
    text = " ".join(str(spec.get(f, "")) for f in FIELDS).lower()
    for a, b in CONFLICTS:
        if re.search(rf"\b{re.escape(a)}\b", text) and re.search(rf"\b{re.escape(b)}\b", text):
            issues.append(f"CONFLICT '{a}' vs '{b}' - pick one")
    words = re.findall(r"[a-z']+", text)
    seen, dups = set(), set()
    for i in range(len(words) - 2):
        tri = " ".join(words[i:i + 3])
        if tri in seen:
            dups.add(tri)
        seen.add(tri)
    counts = {}
    for wd in words:
        if len(wd) > 4:
            counts[wd] = counts.get(wd, 0) + 1
    dups |= {wd for wd, k in counts.items() if k >= 3}
    if dups:
        issues.append(f"REPEATED {sorted(dups)[:3]} - repetition dilutes, it does not emphasise")
    refs = spec.get("references", [])
    if not refs:
        issues.append("NO references - attach the character sheet and location plate (@elements)")
    return issues, len(words)


def compose(args):
    spec = json.load(open(args.fields))
    issues, n = lint(spec)
    os.makedirs(args.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.fields))[0]
    prose = ". ".join(str(spec[f]).strip().rstrip(".") for f in FIELDS if spec.get(f)) + "."
    refs = " ".join(f"@{r}" for r in spec.get("references", []))
    prose = (refs + " " + prose).strip()
    negative = ", ".join(spec.get("negative", []))
    js = {k: spec.get(k) for k in FIELDS + ["references", "negative", "aspect_ratio",
                                              "resolution", "seed", "prompt_version"]}
    open(os.path.join(args.out, f"{stem}.prompt.txt"), "w").write(
        prose + ("\nNEGATIVE: " + negative if negative else "") + "\n")
    json.dump(js, open(os.path.join(args.out, f"{stem}.prompt.json"), "w"), indent=2)
    print(f"PROMPT ({n} words)\n  {prose}")
    if negative:
        print(f"NEGATIVE\n  {negative}")
    print("\nLINT")
    for i in issues or ["no issues found"]:
        print(f"  - {i}")
    print(f"\nWritten: {args.out}/{stem}.prompt.txt and {stem}.prompt.json")
    return 1 if issues else 0


def variance(args):
    import cv2
    import numpy as np
    paths = sorted(glob.glob(os.path.join(args.takes, "cell*_*.png")))
    if not paths:
        raise SystemExit(f"no takes found in {args.takes}")
    os.makedirs(args.out, exist_ok=True)
    rows = []
    for p in paths:
        img = cv2.imread(p)
        if img is None:
            raise SystemExit(f"cannot read {p}")
        body = img[24:]                                    # skip the provenance banner
        hsv = cv2.cvtColor(body, cv2.COLOR_BGR2HSV)
        # the raincoat: saturated, bright, hue 5..40 (orange..yellow)
        mask = cv2.inRange(hsv, (5, 150, 170), (40, 255, 255))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lab, stats, cent = cv2.connectedComponentsWithStats(mask)
        if n < 2:
            raise SystemExit(f"no raincoat found in {p}")
        k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))  # largest blob = the coat
        coat = lab == k
        rows.append({"take": os.path.basename(p), "cell": os.path.basename(p)[4],
                     "coat_hue": float(np.median(hsv[..., 0][coat])),
                     "subject_x": float(cent[k][0]),
                     "subject_area": int(stats[k, cv2.CC_STAT_AREA]),
                     "bg_b": float(body[..., 0][~coat].mean()),
                     "bg_r": float(body[..., 2][~coat].mean())})
    with open(os.path.join(args.out, "takes.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    cells = sorted({r["cell"] for r in rows})
    summary = []
    for c in cells:
        rs = [r for r in rows if r["cell"] == c]
        sd = lambda k: float(np.std([r[k] for r in rs]))
        area = [r["subject_area"] for r in rs]
        summary.append({"cell": c, "takes": len(rs), "sd_coat_hue": round(sd("coat_hue"), 2),
                        "sd_subject_x_px": round(sd("subject_x"), 1),
                        "cv_subject_area": round(float(np.std(area) / np.mean(area)), 3),
                        "sd_bg_warmth": round(float(np.std([r["bg_r"] - r["bg_b"] for r in rs])), 2)})
    # one combined score: each metric normalised by its largest cell value
    keys = ["sd_coat_hue", "sd_subject_x_px", "cv_subject_area", "sd_bg_warmth"]
    for k in keys:
        top = max(s[k] for s in summary) or 1.0
        for s in summary:
            s.setdefault("variance_index", 0.0)
            s["variance_index"] += s[k] / top / len(keys)
    for s in summary:
        s["variance_index"] = round(s["variance_index"], 3)
    with open(os.path.join(args.out, "variance-by-cell.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    print(f"{'cell':5}{'sd hue':>8}{'sd x px':>9}{'cv area':>9}{'sd warmth':>10}{'index':>8}")
    for s in summary:
        print(f"{s['cell']:5}{s['sd_coat_hue']:>8}{s['sd_subject_x_px']:>9}"
              f"{s['cv_subject_area']:>9}{s['sd_bg_warmth']:>10}{s['variance_index']:>8}")
    thumbs = [cv2.resize(cv2.imread(p), (240, 135)) for p in paths]
    grid = np.vstack([np.hstack(thumbs[i:i + 4]) for i in range(0, len(thumbs), 4)])
    cv2.imwrite(os.path.join(args.out, "takes-grid.png"), grid)
    print(f"\nWritten: {args.out}/takes.csv, variance-by-cell.csv, takes-grid.png")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compose")
    c.add_argument("--fields", required=True)
    c.add_argument("--out", default="out")
    v = sub.add_parser("variance")
    v.add_argument("--takes", default="reference/takes")
    v.add_argument("--out", default="out")
    args = ap.parse_args()
    raise SystemExit(compose(args) if args.cmd == "compose" else variance(args))


if __name__ == "__main__":
    main()
