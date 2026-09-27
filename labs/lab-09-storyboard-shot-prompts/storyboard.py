#!/usr/bin/env python3
"""Lab 09 — from shot list to generation-ready prompts and a timed animatic.

  check     Validate the shot list against the voiceover: total runtime, the clip
            length cap, every VO line inside one shot, speaking pace, every
            @element defined, and an identical continuity block in every shot.
  prompts   Write each shot three ways: six-field prose, a multi-shot / timeline
            prompt with dialogue in quotation marks, and JSON.
  animatic  Render the storyboard keyframes into a timed animatic (start frame ->
            end frame per shot) with the VO lines burned in, to lock timing
            before any generation credits are spent.

Usage:
    python3 storyboard.py check    --shots data/shot-list.json --vo data/vo-timing.json
    python3 storyboard.py prompts  --shots data/shot-list.json --vo data/vo-timing.json
    python3 storyboard.py animatic --shots data/shot-list.json --vo data/vo-timing.json \
                                   --board reference/board

Requires: Python 3 (check, prompts); opencv-python and numpy (animatic).
"""
import argparse
import json
import os
import re


def load(args):
    film = json.load(open(args.shots))
    vo = json.load(open(args.vo))["lines"]
    t = 0.0
    for s in film["shots"]:
        s["start"], s["end"] = t, t + s["duration_s"]
        t = s["end"]
    return film, vo


def check(film, vo, quiet=False):
    problems = []
    total = sum(s["duration_s"] for s in film["shots"])
    if abs(total - film["runtime_s"]) > 1e-6:
        problems.append(f"shots sum to {total}s but the runtime is {film['runtime_s']}s")
    cap = film["clip_cap_s"]
    for s in film["shots"]:
        if s["duration_s"] > cap:
            problems.append(f"{s['id']} is {s['duration_s']}s; the model caps clips at {cap}s - "
                            "split it or plan an extension")
        for ref in s["elements"] + re.findall(r"@(\w+)", json.dumps(s)):
            if ref not in film["elements"]:
                problems.append(f"{s['id']} references @{ref}, which is not a saved element")
        if s.get("continuity") != film["continuity_block"]:
            problems.append(f"{s['id']} continuity block differs from the film's - wardrobe will drift")
    for ln in vo:
        home = [s for s in film["shots"] if s["start"] <= ln["start"] < s["end"]]
        if not home:
            problems.append(f"VO '{ln['text'][:30]}' starts outside every shot")
            continue
        s = home[0]
        if ln["end"] > s["end"] + 1e-6:
            problems.append(f"VO '{ln['text'][:30]}...' ends at {ln['end']}s but {s['id']} cuts at "
                            f"{s['end']}s - move the line or the cut")
        words = len(re.findall(r"[A-Za-z']+", ln["text"]))
        pace = words / (ln["end"] - ln["start"])
        if pace > film["max_words_per_s"]:
            problems.append(f"VO '{ln['text'][:30]}' is {pace:.1f} words/s - too fast to read or say")
    if not quiet:
        print(f"{film['title']}: {len(film['shots'])} shots, {total}s (target {film['runtime_s']}s), "
              f"clip cap {cap}s, {len(vo)} VO lines")
        for s in film["shots"]:
            print(f"  {s['id']}  {s['start']:5.1f}-{s['end']:5.1f}s  {s['size']:10} {s['camera_move']:12} "
                  f"{s['action'][:48]}")
        print("\nCHECK")
        for p in problems or ["all checks passed"]:
            print(f"  - {p}")
    return problems


def prompts(film, vo, out):
    os.makedirs(out, exist_ok=True)
    md, js = [f"# {film['title']} — shot prompts ({film['prompt_version']})", ""], []
    for s in film["shots"]:
        lines = [ln for ln in vo if s["start"] <= ln["start"] < s["end"]]
        refs = " ".join(f"@{r}" for r in s["elements"])
        prose = (f"{refs} {s['subject']} {s['action']}. {s['environment']}. "
                 f"{s['size']}, {s['angle']}, {s['camera_move']}, {s['lens']}. "
                 f"{film['style']}. {film['continuity_block']} {s.get('constraints', '')}").strip()
        beats = [(s["start"] + b["at"], b["beat"]) for b in s["beats"]]
        for ln in lines:
            beats.append((ln["start"], f"{ln['speaker']} ({ln['emotion']}, intensity "
                                       f"{ln['intensity']}): \"{ln['text']}\""))
        timeline = (f"SHOT {s['id']} ({s['duration_s']}s, {film['aspect']}) — " +
                    " ".join(f"[{t:.1f}s] {txt}" for t, txt in sorted(beats)))
        rec = {"id": s["id"], "duration_s": s["duration_s"], "elements": s["elements"],
               "start_frame": (f"last frame of {s['extends']} (video extension)" if s.get("extends")
                               else f"reference/board/shot{s['id'][1:]}_start.png"),
               "end_frame": f"reference/board/shot{s['id'][1:]}_end.png",
               "prose": prose, "timeline": timeline,
               "dialogue": [{k: ln[k] for k in ("speaker", "text", "emotion", "intensity")}
                            for ln in lines],
               "takes": s.get("takes", 1), "negative": film["negative"]}
        js.append(rec)
        md += [f"## {s['id']} — {s['size']} · {s['duration_s']} s · takes: {rec['takes']}", "",
               f"**Prose (six-field):** {prose}", "", f"**Timeline / multi-shot:** {timeline}", "",
               f"**Start / end frame:** `{rec['start_frame']}` → `{rec['end_frame']}`", "",
               f"**Negative:** {', '.join(film['negative'])}", ""]
    open(os.path.join(out, "shot-prompts.md"), "w").write("\n".join(md) + "\n")
    json.dump(js, open(os.path.join(out, "shot-prompts.json"), "w"), indent=2)
    print(f"Written: {out}/shot-prompts.md and shot-prompts.json ({len(js)} shots)")


def animatic(film, vo, board, out, fps=24):
    import cv2
    import numpy as np
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "animatic.mp4")
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (960, 540))
    if not vw.isOpened():
        raise SystemExit("VideoWriter failed")
    n, prev_end = 0, None
    for s in film["shots"]:
        pa = os.path.join(board, f"shot{s['id'][1:]}_start.png")
        pb = os.path.join(board, f"shot{s['id'][1:]}_end.png")
        a = cv2.imread(pa) if os.path.exists(pa) else None
        b = cv2.imread(pb) if os.path.exists(pb) else None
        if s.get("extends"):
            # an extension continues the previous clip: it starts on that clip's last frame
            a = prev_end if a is None else a
            b = a if b is None else b
        if a is None or b is None:
            raise SystemExit(f"missing keyframes for {s['id']} in {board}")
        prev_end = b
        frames = int(round(s["duration_s"] * fps))
        for i in range(frames):
            t = s["start"] + i / fps
            f = cv2.addWeighted(a, 1 - i / max(1, frames - 1), b, i / max(1, frames - 1), 0)
            cv2.rectangle(f, (0, 0), (960, 24), (20, 20, 20), -1)
            cv2.putText(f, f"ANIMATIC - timing only - {s['id']} {t:5.1f}s", (8, 17),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1, cv2.LINE_AA)
            for ln in vo:
                if ln["start"] <= t < ln["end"]:
                    txt = f"{ln['speaker']}: {ln['text']}"
                    cv2.rectangle(f, (40, 470), (920, 510), (0, 0, 0), -1)
                    cv2.putText(f, txt[:78], (52, 497), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                                (255, 255, 255), 1, cv2.LINE_AA)
            vw.write(f)
            n += 1
    vw.release()
    print(f"Written: {path}  {n} frames = {n / fps:.2f}s at {fps} fps")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "prompts", "animatic"])
    ap.add_argument("--shots", default="data/shot-list.json")
    ap.add_argument("--vo", default="data/vo-timing.json")
    ap.add_argument("--board", default="reference/board")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()
    film, vo = load(args)
    problems = check(film, vo, quiet=args.cmd != "check")
    if args.cmd == "check":
        raise SystemExit(1 if problems else 0)
    if problems:
        print("Fix these before generating:\n  - " + "\n  - ".join(problems))
        raise SystemExit(1)
    prompts(film, vo, args.out) if args.cmd == "prompts" else animatic(film, vo, args.board, args.out)


if __name__ == "__main__":
    main()
