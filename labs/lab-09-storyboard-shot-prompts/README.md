# Lab 09 — Storyboard to Shot Prompts, Start and End Frames, and the Animatic

**Course:** Create Short Video Film using AI (TGS-2020505925) · **Version v12.0** · 27 September 2026  
**Topic 04:** AI Video Generation, Animation and Video Analytics  
**Outcome:** ELO4 · **In-class time:** 30 minutes of scheduled practical time

| Competency | Statement |
|---|---|
| Ability A5 | Design and apply machine-learning based methods for object detection, object tracking and activity recognition |
| Ability A6 | Design and apply video analytics algorithms for high-level video analytics tasks |
| Knowledge K8 | Deep learning concepts |
| Knowledge K10 | Activity tracking, generative models, scene understanding and event discovery |

---

## Scenario

The Last Ferry is planned as six shots and six voiceover lines. Before generating a single clip, you validate the shot list against the voiceover and the model's clip cap, fix the two problems the check finds, write every shot as a six-field prose prompt, a multi-shot timeline prompt with dialogue and emotions, and JSON, and render a timed animatic from the storyboard's start and end frames.

## What you will produce

A corrected shot list that passes every check, a shot-prompt pack (prose, timeline and JSON per shot, with start/end frames and takes), and a 48-second animatic with the voiceover lines burned in.

**Tools:** Python 3 · opencv-python · NumPy · optional: any image-to-video model with start/end frames

## Environment

Install these once, before class if you can — the lab itself needs no network access after the dependencies are present:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install "opencv-python>=4.10" numpy
python3 -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"
```

Required: `opencv-python>=4.10`, `numpy`.

> **API currency.** Everything taught here runs on the **base `opencv-python` wheel** plus NumPy — no contrib modules and no downloaded model weights. SSIM is implemented in NumPy because `cv2.quality` is contrib-only. Generative steps are optional: every lab supplies SIMULATED reference media so it can be completed offline, and asks you to record the model ID and date if you generate your own.

## Workflow

1. Validate shots against VO and clip cap
2. Fix the timing and length problems
3. Write prose, timeline and JSON prompts
4. Render the start-to-end-frame animatic
5. Lock timing before generating

## Files in this folder

| Path | What it is |
|---|---|
| `reference/board/shot1_start.png … shot6_end.png` | Storyboard start and end keyframes for six shots (SIMULATED) |
| `data/film-brief.md` | One-page brief: cast, locations, prop, beats and sound |
| `data/shot-list.json` | Six shots with size, angle, movement, lens, beats, elements and takes |
| `data/vo-timing.json` | Six voiceover lines with timing, emotion and intensity |
| `storyboard.py` | Runnable script — see the steps below |
| `PROMPTS.md` / `PROMPTS.pdf` | The reusable prompt and specification pack |
| `out/` | Everything you produce (created on first run) |

**Provenance.** Every image and clip in `reference/` is either a **SIMULATED** classroom illustration of *The Last Ferry*, rendered deterministically with OpenCV and labelled on the frame, or an **AI-generated** reference copied unchanged with a `PROVENANCE.md` beside it. Nothing in this folder may be relabelled: a simulated stand-in is never presented as model output or as a photograph.

## Steps

1. Read `data/film-brief.md` and `data/shot-list.json`. Every shot references saved elements (@mei, @red_box, …) and repeats one identical continuity block.

2. Read `data/vo-timing.json`. The voiceover was generated FIRST; the storyboard is cut to it, not the other way round.

3. Validate. The check exits with status 1 and reports two problems.

   ```bash
   python3 storyboard.py check --shots data/shot-list.json --vo data/vo-timing.json
   ```

4. Problem 1: S6 is 12 s but the model caps clips at 10 s. Copy the shot list to `out/shot-list-v2.json`, set S6 to 6 s, and add S7 (6 s) with `"extends": "S6"` — a video extension that starts on S6's last frame.

5. Problem 2: the line 'No sender. Just a tag, folded shut.' ends at 22.5 s but S3 cuts at 22.0 s. Copy the VO file to `out/vo-timing-v2.json` and end the line at 21.8 s (or move the cut — record which and why).

6. Re-run the check on your v2 files until it passes.

   ```bash
   python3 storyboard.py check --shots out/shot-list-v2.json --vo out/vo-timing-v2.json
   ```

7. Write the prompt pack.

   ```bash
   python3 storyboard.py prompts --shots out/shot-list-v2.json --vo out/vo-timing-v2.json --out out
   ```

8. Read `out/shot-prompts.md`. In each timeline prompt the beats and dialogue are ordered by time, dialogue is in quotation marks and each line carries an emotion and intensity. S2 asks for three takes because it is dense action.

9. Render the animatic.

   ```bash
   python3 storyboard.py animatic --shots out/shot-list-v2.json --vo out/vo-timing-v2.json --board reference/board --out out
   ```

10. Watch `out/animatic.mp4` (48.00 s). Is any line crowded or any shot too long to hold interest? Note one timing change you would make.

11. Write `out/continuity-plan.md`: which shots use a start frame, which use start AND end frames, and which use a video reference/extension, and why each choice keeps lighting and mood across the cut.

12. Optional extension: generate S1 on an image-to-video model with its start and end frames and the timeline prompt. Record model, duration, resolution and takes.

## Verify

> Your v2 files pass every check; the prompt pack has one entry per shot; the animatic is exactly 48.00 s.

### Expected outputs

- out/shot-list-v2.json and out/vo-timing-v2.json passing the check
- out/shot-prompts.md and out/shot-prompts.json
- out/animatic.mp4 (48.00 s)
- out/continuity-plan.md

### Evidence checklist

Submit all of the following. Each item is something an assessor can look at.

- [ ] The failing check output and your two fixes
- [ ] The passing check output for the v2 files
- [ ] One shot's prose, timeline and JSON prompts, with start/end frames and takes
- [ ] The animatic and one timing change you would make
- [ ] Continuity plan: start frame, start/end frames or video extension per shot

## Troubleshooting

| Symptom | What to do |
|---|---|
| 'missing keyframes for S7' | Add "extends": "S6" to S7 so it starts on S6's last frame. |
| 'references @x, which is not a saved element' | Add the element to the film's elements list or fix the spelling. |
| 'continuity block differs' | Copy the film's continuity_block into the shot exactly — any edit invites drift. |
| The animatic will not play | Open it in VLC; mp4v is widely supported but not by every browser. |

## References used in this lab

- **[S6]** Youri van Hofwegen, 'EXACTLY How to Make an AI Short Film (Full Workflow)', YouTube, 1 Jun 2026, youtube.com/watch?v=0v534yAyhwg — *Full video, 16:49*.  
  Reference-first principle (stop giving the model freedom); three reference types — characters, locations, props; casting attributes (genre, budget, era, archetype, identity, physique, details, outfit); a second, damaged-state location made by editing the first ('change nothing else'); director controls (genre, camera movement, speed ramp, duration, aspect ratio, audio); per-character emotion and intensity; the multi-shot prompt framework with dialogue in quotation marks; video reference versus start/end frame (mood carries over); three generations for dense action shots; assembly in a timeline editor.
- **[S7]** Mira AI, '6 AI Video Tools I'd Use To Make An AI Short Film', YouTube, 14 Jun 2026, youtube.com/watch?v=Whh8vCqboxQ — *Full video, 10:04*.  
  A multi-tool workflow: an LLM to plan the story shot by shot, a cinematic image model for character sheets (front, side, back, close-ups) and multi-angle environment grids, a design canvas for the storyboard with keyframe placeholders, a video model for motion, an AI music generator (instrumental, mood and tempo), and an editor; the six-point prompt framework (subject, action, environment, camera, style, constraints); timeline prompting; video extension to pass the previous clip; generations capped at about 15 seconds.
- **[S11]** ElevenLabs, 'How to Make Your First AI Short Film (Full Tutorial)', YouTube, 9 Aug 2026, youtube.com/watch?v=47DH_VUa67A — *Chapters, 31:13*.  
  Explore cheaply with faster image models before committing credits; prompt structure across style, subject, objects and negative prompting; a character reference sheet; generate the voiceover FIRST and build the storyboard to match it; direct delivery line by line with audio tags; still frames before video; start and end frames; generate at lower resolution and upscale only the takes you keep; background music; sound effects; edit and trim on a timeline; regenerate with a new character.
- **[S16]** Google AI for Developers — Veo video generation documentation — *https://ai.google.dev/gemini-api/docs/veo (verified 6 Sep 2026)*.  
  Veo 3.1 model family with native audio; 4, 6 or 8 second clips; 16:9 or 9:16; 720p, 1080p or 4k; up to three reference images on supported models; image-to-video; first and last frame control; clip extension; asynchronous long-running operation that the client polls.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
