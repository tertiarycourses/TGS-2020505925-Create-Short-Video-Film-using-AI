#!/usr/bin/env python3
"""Lab 01 — score candidate film projects against the need criteria and the gates.

The scorer produces a deterministic BASELINE. It never overrides your judgement:
reconcile every difference between your manual scores and this output in writing.

Usage:
    python3 score_projects.py --csv data/candidate-projects.csv \
                              --criteria data/need-criteria.json --out out

Requires: Python 3 standard library only.
"""
import argparse
import csv
import json
import os


def band(value, bands):
    """bands = [[threshold, score], ...] in descending threshold order."""
    for threshold, score in bands:
        if value >= threshold:
            return score
    return bands[-1][1]


def score_row(r, crit):
    s = {}
    minutes = int(r["episodes_per_quarter"]) * float(r["finished_seconds_each"]) / 60.0
    s["volume"] = band(minutes, crit["rules"]["volume_minutes"])
    s["repeatability"] = crit["rules"]["repeatability"][r["repeatability"]]
    days = int(r["turnaround_days_required"])
    s["speed_value"] = 5 if days <= 5 else (3 if days <= 15 else 1)
    s["review_tolerance"] = crit["rules"]["review_tolerance"][r["review_tolerance"]]
    s["likeness_risk"] = crit["rules"]["likeness_risk"][r["likeness_risk"]]
    cur = float(r["current_cost_sgd_per_quarter"])
    ai = float(r["estimated_ai_cost_sgd_per_quarter"])
    gap = (cur - ai) / cur if cur > 0 else 0.0
    s["cost_gap"] = band(gap, crit["rules"]["cost_gap"])
    total = sum(s[k] * w for k, w in crit["weights"].items())
    return s, round(total, 2), round(minutes, 2), round(gap, 3)


def gates(r, crit):
    """Each gate returns PASS, FAIL or UNKNOWN. Anything but PASS blocks selection."""
    g = {}
    g["ai_appropriate"] = {"yes": "PASS", "no": "FAIL"}.get(r["ai_appropriate"], "UNKNOWN")
    g["rights_cleared"] = {"cleared": "PASS", "not_applicable": "PASS",
                           "refused": "FAIL"}.get(r["rights_status"], "UNKNOWN")
    g["likeness_consent"] = "FAIL" if r["likeness_risk"] in crit["gate_fail_likeness"] else "PASS"
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/candidate-projects.csv")
    ap.add_argument("--criteria", default="data/need-criteria.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    crit = json.load(open(args.criteria))
    if abs(sum(crit["weights"].values()) - 1.0) > 1e-9:
        raise SystemExit("weights in need-criteria.json must sum to 1.0")
    rows = list(csv.DictReader(open(args.csv, newline="")))
    if not rows:
        raise SystemExit("no candidate projects found")
    os.makedirs(args.out, exist_ok=True)

    out_rows = []
    for r in rows:
        s, total, minutes, gap = score_row(r, crit)
        g = gates(r, crit)
        if "FAIL" in g.values():
            verdict = "REJECT (gate)"
        elif "UNKNOWN" in g.values():
            verdict = "HOLD (gate unknown)"
        elif total >= crit["accept_threshold"]:
            verdict = "SELECT"
        else:
            verdict = "REJECT (score)"
        out_rows.append({"project_id": r["project_id"], "name": r["name"],
                         "finished_min_per_qtr": minutes, "cost_gap": gap, **s,
                         "weighted_total": total, **{f"gate_{k}": v for k, v in g.items()},
                         "verdict": verdict})

    path = os.path.join(args.out, "baseline-scores.csv")
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)

    print(f"{'ID':4} {'Project':44} {'Total':>5}  Verdict")
    for r in sorted(out_rows, key=lambda x: -x["weighted_total"]):
        print(f"{r['project_id']:4} {r['name'][:44]:44} {r['weighted_total']:>5}  {r['verdict']}")
    print(f"\nAccept threshold: {crit['accept_threshold']} (weighted, 0-5 scale)")
    print("Gates are applied BEFORE the threshold: a high score never rescues a failed gate.")
    print(f"Written: {path}")


if __name__ == "__main__":
    main()
