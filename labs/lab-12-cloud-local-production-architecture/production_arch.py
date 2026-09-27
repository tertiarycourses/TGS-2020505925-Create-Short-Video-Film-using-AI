#!/usr/bin/env python3
"""Lab 12 — design and evaluate cloud, local and hybrid production architectures.

  1 MEASURED  time the local stages of the pipeline on THIS laptop (decode, QA
              analytics, grade, encode) on the bench clip
  2 MODELLED  generation time and credits for each architecture from the
              production plan: shots x takes x seconds x resolution
  3 MODELLED  upload time for the element pack (references) at your uplink speed,
              and the request/response pattern each architecture's protocol uses
  4 GATES     consent, data residency, quality, shot control, budget and deadline -
              applied BEFORE ranking
  5 MEMORY    whether an open video model fits the local GPU at FP16 / INT8 / INT4

Every number is labelled MEASURED or MODELLED. Credit prices in the data file are
ILLUSTRATIVE classroom values: replace them with the current price list before
using the result for a real quote.

Usage:
    python3 production_arch.py --plan data/production-plan.json \
        --archs data/architectures.json --constraints data/constraints.json \
        --clip reference/bench-clip.mp4 --elements reference/element-pack --out out

Requires: opencv-python, numpy.
"""
import argparse
import csv
import glob
import json
import os
import time

import cv2
import numpy as np


def measure_local(clip, out):
    """MEASURED: wall-clock per stage on this machine."""
    t = {}
    t0 = time.perf_counter()
    cap = cv2.VideoCapture(clip)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    t["decode"] = time.perf_counter() - t0
    if not frames:
        raise SystemExit(f"cannot read {clip}")
    t0 = time.perf_counter()
    prev = None
    for f in frames:                                   # QA: histogram + frame difference
        h = cv2.calcHist([cv2.cvtColor(f, cv2.COLOR_BGR2HSV)], [0, 1], None, [30, 32],
                         [0, 180, 0, 256])
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        if prev is not None:
            _ = float(np.abs(g.astype(np.int16) - prev).mean())
        prev = g.astype(np.int16)
    t["qa_analytics"] = time.perf_counter() - t0
    lut = np.clip(np.arange(256) * 1.08 - 6, 0, 255).astype(np.uint8)
    t0 = time.perf_counter()
    graded = [cv2.LUT(f, lut) for f in frames]
    t["grade_lut"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    h, w = frames[0].shape[:2]
    vw = cv2.VideoWriter(os.path.join(out, "bench-encode.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                         24, (w, h))
    for f in graded:
        vw.write(f)
    vw.release()
    t["encode"] = time.perf_counter() - t0
    secs = len(frames) / 24.0
    return {k: round(v / secs, 4) for k, v in t.items()}, len(frames), (w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="data/production-plan.json")
    ap.add_argument("--archs", default="data/architectures.json")
    ap.add_argument("--constraints", default="data/constraints.json")
    ap.add_argument("--clip", default="reference/bench-clip.mp4")
    ap.add_argument("--elements", default="reference/element-pack")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()
    plan = json.load(open(args.plan))
    archs = json.load(open(args.archs))["architectures"]
    con = json.load(open(args.constraints))
    os.makedirs(args.out, exist_ok=True)

    # 1 MEASURED ---------------------------------------------------------------
    per_s, nf, (w, h) = measure_local(args.clip, args.out)
    print(f"1 MEASURED on this machine ({nf} frames, {w}x{h}); seconds of work per second "
          "of footage:")
    for k, v in per_s.items():
        print(f"    {k:13} {v:.4f} s/s")
    post_scale = (plan["master_w"] * plan["master_h"]) / (w * h)
    local_post_s = sum(per_s.values()) * post_scale * plan["runtime_s"] * plan["post_passes"]
    print(f"    -> local post-production for the {plan['runtime_s']}s film at "
          f"{plan['master_w']}x{plan['master_h']}, {plan['post_passes']} passes: "
          f"{local_post_s:.1f} s (pixel-scaled estimate)")

    # 2-3 MODELLED ----------------------------------------------------------------
    gen_seconds = sum(s["seconds"] * s["takes"] for s in plan["shots"])
    finished = sum(s["seconds"] for s in plan["shots"])
    pack = sum(os.path.getsize(p) for p in glob.glob(os.path.join(args.elements, "*")))
    print(f"\n2 MODELLED  {len(plan['shots'])} shots, {finished}s finished, {gen_seconds}s "
          f"generated including extra takes; element pack {pack / 1e6:.2f} MB")
    rows = []
    for a in archs:
        cost = gen_seconds * a["credits_per_generated_s"] * a["sgd_per_credit"] + a["fixed_sgd"]
        gen_min = (gen_seconds * a["render_s_per_generated_s"] +
                   len(plan["shots"]) * a["queue_s_per_job"]) / 60
        upload_s = pack * 8 / (con["uplink_mbps"] * 1e6) if a["uploads_references"] else 0.0
        total_h = (gen_min * 60 + upload_s + local_post_s + plan["review_minutes"] * 60) / 3600
        gates = []
        if a["data_leaves_premises"] and con["likeness_data_must_stay_local"]:
            gates.append("likeness data must stay local")
        if a["region"] not in con["allowed_regions"]:
            gates.append(f"region {a['region']} not allowed")
        if a["quality_tier"] < con["min_quality_tier"]:
            gates.append(f"quality tier {a['quality_tier']} < required {con['min_quality_tier']}")
        if con["needs_shot_level_control"] and not a["shot_level_control"]:
            gates.append("no start/end-frame or per-shot control")
        if cost > con["budget_sgd"]:
            gates.append(f"cost S${cost:,.0f} > budget S${con['budget_sgd']:,}")
        if total_h > con["deadline_hours"]:
            gates.append(f"{total_h:.1f} h > deadline {con['deadline_hours']} h")
        vram = None
        if a.get("local_model_params_b"):
            need = {b: a["local_model_params_b"] * 1e9 * bits / 8 / 1e9 * a["activation_overhead"]
                    for b, bits in (("FP16", 16), ("INT8", 8), ("INT4", 4))}
            fits = [b for b, g in need.items() if g <= con["local_gpu_vram_gb"]]
            vram = {b: round(g, 1) for b, g in need.items()}
            if not fits:
                gates.append(f"model needs {min(need.values()):.1f} GB > {con['local_gpu_vram_gb']} GB VRAM")
        rows.append({"architecture": a["name"], "pattern": a["pattern"],
                     "protocol": a["protocol"], "generated_s": gen_seconds,
                     "cost_sgd": round(cost), "cost_per_finished_min_sgd": round(cost / (finished / 60)),
                     "generation_min": round(gen_min, 1), "upload_s": round(upload_s, 1),
                     "end_to_end_h": round(total_h, 2), "vram_gb": vram,
                     "gates": "; ".join(gates) or "PASS"})
    print(f"\n{'architecture':30}{'S$':>7}{'S$/min':>8}{'gen min':>9}{'upload s':>10}{'total h':>9}  gates")
    for r in rows:
        print(f"{r['architecture']:30}{r['cost_sgd']:>7}{r['cost_per_finished_min_sgd']:>8}"
              f"{r['generation_min']:>9}{r['upload_s']:>10}{r['end_to_end_h']:>9}  {r['gates']}")
        if r["vram_gb"]:
            print(f"{'':30}weights+activations: {r['vram_gb']} GB vs {con['local_gpu_vram_gb']} GB GPU")
    print("\n3 PROTOCOL PATTERNS")
    for a in archs:
        print(f"  {a['name']}: {a['protocol']}")
    passing = [r for r in rows if r["gates"] == "PASS"]
    if passing:
        best = min(passing, key=lambda r: (r["cost_sgd"], r["end_to_end_h"]))
        print(f"\n4 RECOMMENDATION  {best['architecture']} - cheapest architecture that passes "
              "every gate. Defend it with the numbers above, not with the ranking alone.")
    else:
        print("\n4 RECOMMENDATION  none passes every gate - change the plan (fewer takes, lower "
              "draft resolution, longer deadline) rather than relaxing a gate.")
    with open(os.path.join(args.out, "architecture-matrix.csv"), "w", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wtr.writeheader()
        wtr.writerows(rows)
    json.dump({"measured_local_s_per_s": per_s, "rows": rows},
              open(os.path.join(args.out, "architecture-report.json"), "w"), indent=2, default=str)
    print(f"Written: {args.out}/architecture-matrix.csv, architecture-report.json")


if __name__ == "__main__":
    main()
