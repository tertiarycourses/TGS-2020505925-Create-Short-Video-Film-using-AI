#!/usr/bin/env python3
"""Lab 11 — sound, captions and the final export ladder.

  captions  Validate subtitles against the caption rules (reading speed, line
            length, line count, duration, gaps, overlaps).
  audio     Build a SIMULATED placeholder mix from the VO cue sheet and the music
            brief (tone bursts for each VO line, a chord bed at the brief's tempo,
            rain noise and a ferry horn), duck the music under the voice, and
            measure peak and RMS levels against the delivery targets.
  export    Reframe the picture lock for each delivery profile (subject-centred
            crop for vertical formats using the raincoat segmentation mask), burn
            captions inside the safe area, write each master, and - if FFmpeg is
            installed - mux the mix into an H.264/AAC file and verify it.
  all       Run the three steps in order.

Usage:
    python3 finish.py all --clip reference/picture-lock.mp4 --srt data/captions.srt \
        --vo data/vo-cues.json --music data/music-brief.json \
        --profiles data/export-profiles.json --rules data/caption-rules.json --out out

Requires: opencv-python, numpy. Optional: ffmpeg/ffprobe on PATH.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import wave

import numpy as np

SR = 48000


# ---------------------------------------------------------------- captions
def parse_srt(path):
    blocks = re.split(r"\n\s*\n", open(path, encoding="utf-8").read().strip())
    cues = []
    ts = lambda t: sum(float(x) * m for x, m in zip(t.replace(",", ".").split(":"), (3600, 60, 1)))
    for b in blocks:
        lines = b.strip().splitlines()
        a, z = [ts(x.strip()) for x in lines[1].split("-->")]
        cues.append({"n": int(lines[0]), "start": a, "end": z, "lines": lines[2:]})
    return cues


def check_captions(cues, rules):
    problems = []
    for i, c in enumerate(cues):
        dur = c["end"] - c["start"]
        text = " ".join(c["lines"])
        cps = len(text) / dur if dur > 0 else 99
        if len(c["lines"]) > rules["max_lines"]:
            problems.append(f"#{c['n']}: {len(c['lines'])} lines (max {rules['max_lines']})")
        for ln in c["lines"]:
            if len(ln) > rules["max_chars_per_line"]:
                problems.append(f"#{c['n']}: line of {len(ln)} chars (max {rules['max_chars_per_line']})")
        if dur < rules["min_duration_s"]:
            problems.append(f"#{c['n']}: on screen {dur:.2f}s (min {rules['min_duration_s']}s)")
        if dur > rules["max_duration_s"]:
            problems.append(f"#{c['n']}: on screen {dur:.2f}s (max {rules['max_duration_s']}s)")
        if cps > rules["max_chars_per_second"]:
            problems.append(f"#{c['n']}: {cps:.1f} chars/s (max {rules['max_chars_per_second']})")
        if i and c["start"] < cues[i - 1]["end"] + rules["min_gap_s"] - 1e-9:
            problems.append(f"#{c['n']}: overlaps or crowds #{cues[i - 1]['n']}")
    return problems


def captions(args):
    cues = parse_srt(args.srt)
    rules = json.load(open(args.rules))
    problems = check_captions(cues, rules)
    print(f"CAPTIONS  {len(cues)} cues checked against {os.path.basename(args.rules)}")
    for p in problems or ["all cues pass"]:
        print(f"  - {p}")
    return cues, problems


# ---------------------------------------------------------------- audio
def db(x):
    return 20 * np.log10(max(float(x), 1e-9))


def audio(args, duration):
    vo = json.load(open(args.vo))["cues"]
    brief = json.load(open(args.music))
    n = int(duration * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(3)
    voice = np.zeros(n)
    for c in vo:                                    # placeholder "speech": gated tone bursts
        a, z = int(c["start"] * SR), int(c["end"] * SR)
        seg = t[a:z]
        env = (np.sin(2 * np.pi * 4.0 * seg) > -0.3).astype(float)
        voice[a:z] += 0.5 * env * np.sin(2 * np.pi * c.get("pitch_hz", 190) * seg)
    beat = 60.0 / brief["bpm"]
    music = np.zeros(n)
    chords = brief["chord_roots_hz"]
    for k, start in enumerate(np.arange(0, duration, 4 * beat)):
        a = int(start * SR)
        z = min(n, int((start + 4 * beat) * SR))
        seg = t[a:z] - start
        root = chords[k % len(chords)]
        tone = sum(np.sin(2 * np.pi * root * r * seg) for r in (1.0, 1.26, 1.5))
        music[a:z] += 0.18 * tone * np.exp(-seg / (4 * beat))
    sfx = 0.03 * rng.normal(0, 1, n)                 # rain bed
    for h in brief.get("horn_at_s", []):
        a, z = int(h * SR), min(n, int((h + 1.5) * SR))
        sfx[a:z] += 0.35 * np.sin(2 * np.pi * 110 * t[a:z]) * np.hanning(z - a)
    # ducking: music drops by duck_db wherever the voice is active
    active = np.convolve(np.abs(voice) > 0.01, np.ones(int(0.05 * SR)) / int(0.05 * SR), "same") > 0
    gain = np.where(active, 10 ** (-brief["duck_db"] / 20), 1.0)
    gain = np.convolve(gain, np.ones(int(0.1 * SR)) / int(0.1 * SR), "same")
    mix = voice + music * gain + sfx
    peak = np.abs(mix).max()
    target = 10 ** (brief["target_peak_dbfs"] / 20)
    mix *= target / peak
    voice_s, music_s = voice * target / peak, music * gain * target / peak
    vo_rms = np.sqrt(np.mean(voice_s[active] ** 2)) if active.any() else 0
    mu_rms = np.sqrt(np.mean(music_s[active] ** 2)) if active.any() else 0
    report = {"duration_s": round(duration, 2), "peak_dbfs": round(db(np.abs(mix).max()), 2),
              "mix_rms_dbfs": round(db(np.sqrt(np.mean(mix ** 2))), 2),
              "voice_over_music_db": round(db(vo_rms) - db(mu_rms), 1)}
    ok_peak = report["peak_dbfs"] <= brief["max_peak_dbfs"]
    ok_vo = report["voice_over_music_db"] >= brief["min_voice_over_music_db"]
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "mix-placeholder.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"\nAUDIO  SIMULATED placeholder mix, {report['duration_s']}s at {SR} Hz")
    print(f"  peak {report['peak_dbfs']} dBFS (max {brief['max_peak_dbfs']}) "
          f"{'ok' if ok_peak else 'TOO HOT'};  mix RMS {report['mix_rms_dbfs']} dBFS;  "
          f"voice over music {report['voice_over_music_db']} dB (min "
          f"{brief['min_voice_over_music_db']}) {'ok' if ok_vo else 'VOICE BURIED'}")
    json.dump(report, open(os.path.join(args.out, "audio-report.json"), "w"), indent=2)
    return path


# ---------------------------------------------------------------- export
def export(args, cues, wav):
    import cv2
    profiles = json.load(open(args.profiles))
    cap = cv2.VideoCapture(args.clip)
    if not cap.isOpened():
        raise SystemExit(f"cannot open {args.clip}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    H, W = frames[0].shape[:2]
    # subject centre per frame from the raincoat segmentation mask, smoothed over time
    cx = []
    for f in frames:
        m = cv2.inRange(cv2.cvtColor(f, cv2.COLOR_BGR2HSV), (18, 195, 235), (28, 255, 255))
        mo = cv2.moments(m, binaryImage=True)
        cx.append(mo["m10"] / mo["m00"] if mo["m00"] > 2000 else np.nan)
    cx = np.array(cx)
    cx[np.isnan(cx)] = W / 2 if np.isnan(cx).all() else np.nanmean(cx)
    cx = np.convolve(np.pad(cx, 12, mode="edge"), np.ones(25) / 25, "valid")
    results = []
    for p in profiles["profiles"]:
        tw, th = p["w"], p["h"]
        ta = tw / th
        cw, ch = (int(H * ta), H) if W / H > ta else (W, int(W / ta))
        path = os.path.join(args.out, f"{p['name']}.mp4")
        vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (tw, th))
        sa = p["safe"]
        for i, f in enumerate(frames):
            x0 = int(np.clip(cx[i] - cw / 2, 0, W - cw)) if p.get("follow_subject") else (W - cw) // 2
            y0 = (H - ch) // 2
            out = cv2.resize(f[y0:y0 + ch, x0:x0 + cw], (tw, th), interpolation=cv2.INTER_AREA)
            # a crop can cut the provenance banner: the label must travel to every derivative
            cv2.rectangle(out, (0, 0), (tw, 22), (28, 28, 34), -1)
            cv2.putText(out, "SIMULATED CLIP - classroom derivative", (6, 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (235, 235, 235), 1, cv2.LINE_AA)
            t = i / fps
            for c in cues:
                if c["start"] <= t < c["end"]:
                    scale = p["caption_scale"]
                    ys = int(th * (1 - sa["bottom"])) - 10
                    for ln in reversed(c["lines"]):
                        (tw_, th_), _ = cv2.getTextSize(ln, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
                        tw_ = min(tw_, int(tw * (1 - 2 * sa["sides"])))
                        x = (tw - tw_) // 2
                        cv2.rectangle(out, (x - 8, ys - th_ - 8), (x + tw_ + 8, ys + 8), (0, 0, 0), -1)
                        cv2.putText(out, ln, (x, ys), cv2.FONT_HERSHEY_SIMPLEX, scale,
                                    (255, 255, 255), 2, cv2.LINE_AA)
                        ys -= th_ + 18
            vw.write(out)
        vw.release()
        chk = cv2.VideoCapture(path)
        got = (int(chk.get(cv2.CAP_PROP_FRAME_WIDTH)), int(chk.get(cv2.CAP_PROP_FRAME_HEIGHT)),
               int(chk.get(cv2.CAP_PROP_FRAME_COUNT)))
        chk.release()
        row = {"profile": p["name"], "size": f"{got[0]}x{got[1]}", "frames": got[2],
               "crop": f"{cw}x{ch}", "kept_pct": round(100 * cw * ch / (W * H), 1),
               "subject_follow": bool(p.get("follow_subject")), "muxed": None}
        if shutil.which("ffmpeg") and wav:
            final = os.path.join(args.out, f"{p['name']}_final.mp4")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-i", wav,
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            "-shortest", "-movflags", "+faststart", final], check=True)
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                    "stream=codec_type,codec_name,width,height", "-of", "json", final],
                                   capture_output=True, text=True, check=True)
            row["muxed"] = [f"{s['codec_type']}:{s['codec_name']}"
                            for s in json.loads(probe.stdout)["streams"]]
        results.append(row)
    print("\nEXPORT LADDER")
    for r in results:
        print(f"  {r['profile']:14} {r['size']:>10}  {r['frames']} frames  crop {r['crop']} "
              f"({r['kept_pct']}% kept){'  subject-follow' if r['subject_follow'] else ''}"
              f"{'  muxed ' + str(r['muxed']) if r['muxed'] else '  (ffmpeg not found: video only)'}")
    json.dump(results, open(os.path.join(args.out, "export-report.json"), "w"), indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["captions", "audio", "export", "all"])
    ap.add_argument("--clip", default="reference/picture-lock.mp4")
    ap.add_argument("--srt", default="data/captions.srt")
    ap.add_argument("--rules", default="data/caption-rules.json")
    ap.add_argument("--vo", default="data/vo-cues.json")
    ap.add_argument("--music", default="data/music-brief.json")
    ap.add_argument("--profiles", default="data/export-profiles.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    cues, problems = captions(args)
    if args.cmd == "captions":
        raise SystemExit(1 if problems else 0)
    import cv2
    cap = cv2.VideoCapture(args.clip)
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    wav = audio(args, duration) if args.cmd in ("audio", "all") else None
    if args.cmd in ("export", "all"):
        if problems:
            print("\nFix the caption problems before exporting - burned-in captions cannot be edited.")
            raise SystemExit(1)
        export(args, cues, wav)


if __name__ == "__main__":
    main()
