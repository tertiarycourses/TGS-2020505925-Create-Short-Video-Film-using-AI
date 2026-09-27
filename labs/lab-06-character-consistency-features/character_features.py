#!/usr/bin/env python3
"""Lab 06 — design and run a character-consistency check with local features.

For the character crop in every shot, and for the approved reference sheet:
  colour   median raincoat hue, red-scarf coverage, k-means dominant colours
  edge     Canny edge density of the silhouette
  texture  Laplacian variance (fine detail energy)
  keypoint ORB keypoints matched to the sheet with Hamming distance + ratio test
and for the prop: brass coverage inside the clasp window, and ORB matches to the sheet prop.

Each shot passes or fails against data/identity-thresholds.json, with the
reason printed, so a drifted generation is caught before it reaches the edit.

Usage:
    python3 character_features.py --sheet reference/mei-reference-sheet.png \
        --shots reference/shots --crops data/crops.json \
        --thresholds data/identity-thresholds.json --out out

Requires: opencv-python, numpy.
"""
import argparse
import csv
import json
import os

import cv2
import numpy as np


def crop(img, box):
    x, y, w, h = box
    H, W = img.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    return img[y0:min(H, y + h), x0:min(W, x + w)]


def colour_features(c, t):
    hsv = cv2.cvtColor(c, cv2.COLOR_BGR2HSV)
    coat = cv2.inRange(hsv, tuple(t["coat_hsv_lo"]), tuple(t["coat_hsv_hi"])) > 0
    red = (cv2.inRange(hsv, (0, 120, 90), (8, 255, 255)) |
           cv2.inRange(hsv, (172, 120, 90), (180, 255, 255))) > 0
    top = slice(0, int(c.shape[0] * 0.45))              # scarf sits in the upper body
    coat_hue = float(np.median(hsv[..., 0][coat])) if coat.any() else float("nan")
    return {"coat_hue": round(coat_hue, 1),
            "coat_cover": round(float(coat.mean()), 3),
            "scarf_red_cover": round(float(red[top].mean()), 3)}


def dominant(c, k=4):
    z = c.reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centres = cv2.kmeans(z, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    share = np.bincount(labels.ravel(), minlength=k) / len(labels)
    order = np.argsort(-share)
    return [("#%02x%02x%02x" % tuple(int(v) for v in centres[i][::-1]), round(float(share[i]), 2))
            for i in order]


def orb_matches(a, b, orb, ratio):
    ga, gb = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    # bring both crops to the same height so scale is comparable
    s = 320.0 / ga.shape[0]
    ga = cv2.resize(ga, None, fx=s, fy=s)
    gb = cv2.resize(gb, None, fx=320.0 / gb.shape[0], fy=320.0 / gb.shape[0])
    ka, da = orb.detectAndCompute(ga, None)
    kb, db = orb.detectAndCompute(gb, None)
    if da is None or db is None or len(kb) < 2:
        return 0, len(ka or []), len(kb or [])
    pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(da, db, k=2)
    good = [m for m, *n in pairs if n and m.distance < ratio * n[0].distance]
    return len(good), len(ka), len(kb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default="reference/mei-reference-sheet.png")
    ap.add_argument("--shots", default="reference/shots")
    ap.add_argument("--crops", default="data/crops.json")
    ap.add_argument("--thresholds", default="data/identity-thresholds.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()
    t = json.load(open(args.thresholds))
    crops = json.load(open(args.crops))["crops"]
    sheet = cv2.imread(args.sheet)
    if sheet is None:
        raise SystemExit(f"cannot read {args.sheet}")
    orb = cv2.ORB_create(nfeatures=t["orb_nfeatures"])
    ref_c = crop(sheet, crops["sheet"]["character"])
    ref_p = crop(sheet, crops["sheet"]["prop"])
    ref = colour_features(ref_c, t)
    print(f"REFERENCE SHEET  coat hue {ref['coat_hue']}  scarf red {ref['scarf_red_cover']}  "
          f"dominant {dominant(ref_c)[:3]}")
    os.makedirs(args.out, exist_ok=True)
    rows = []
    for name in sorted(k for k in crops if k != "sheet"):
        img = cv2.imread(os.path.join(args.shots, name))
        if img is None:
            raise SystemExit(f"cannot read {name}")
        c, p = crop(img, crops[name]["character"]), crop(img, crops[name]["prop"])
        f = colour_features(c, t)
        g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(g, t["canny_low"], t["canny_high"])
        good, ka, kb = orb_matches(ref_c, c, orb, t["ratio"])
        pgood, _, _ = orb_matches(ref_p, p, orb, t["ratio"])
        # the clasp window only: the raincoat shares the brass hue, so a whole-prop
        # measure would be contaminated by the coat behind the box
        k = crop(img, crops[name]["clasp"])
        brass = cv2.inRange(cv2.cvtColor(k, cv2.COLOR_BGR2HSV), tuple(t["brass_hsv_lo"]),
                            tuple(t["brass_hsv_hi"]))
        r = {"shot": name, **f,
             "edge_density": round(float(np.count_nonzero(edges)) / edges.size, 3),
             "texture_lapvar": round(float(cv2.Laplacian(g, cv2.CV_64F).var()), 1),
             "orb_good_matches": good, "prop_orb_matches": pgood,
             "clasp_brass_cover": round(float(np.count_nonzero(brass)) / brass.size, 3)}
        reasons = []
        if r["coat_hue"] != r["coat_hue"]:                  # NaN: no coat pixels at all
            reasons.append("coat colour not found in the crop - wardrobe changed or wrong range")
        elif abs(r["coat_hue"] - ref["coat_hue"]) > t["coat_hue_tolerance"]:
            reasons.append(f"coat hue {r['coat_hue']} vs sheet {ref['coat_hue']}")
        if r["scarf_red_cover"] < t["min_scarf_red_cover"]:
            reasons.append(f"scarf red cover {r['scarf_red_cover']} < {t['min_scarf_red_cover']}")
        if r["orb_good_matches"] < t["min_orb_matches"]:
            reasons.append(f"only {good} ORB matches to the sheet")
        if r["clasp_brass_cover"] < t["min_clasp_brass_cover"]:
            reasons.append(f"clasp brass cover {r['clasp_brass_cover']} - clasp missing?")
        r["verdict"] = "CONSISTENT" if not reasons else "DRIFT: " + "; ".join(reasons)
        rows.append(r)
        print(f"{name}  hue {r['coat_hue']:>5}  scarf {r['scarf_red_cover']:.3f}  "
              f"ORB {good:>3}  brass {r['clasp_brass_cover']:.3f}  ->  {r['verdict']}")
    with open(os.path.join(args.out, "identity-report.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    # visual evidence: sheet crop beside every shot crop
    tiles = [cv2.resize(ref_c, (110, 330))]
    for r in rows:
        c = crop(cv2.imread(os.path.join(args.shots, r["shot"])), crops[r["shot"]]["character"])
        tile = cv2.resize(c, (110, 330))
        col = (0, 170, 0) if r["verdict"] == "CONSISTENT" else (0, 0, 230)
        cv2.rectangle(tile, (0, 0), (109, 329), col, 4)
        tiles.append(tile)
    cv2.imwrite(os.path.join(args.out, "identity-strip.png"), np.hstack(tiles))
    print(f"\nWritten: {args.out}/identity-report.csv, identity-strip.png")


if __name__ == "__main__":
    main()
