# Lab 11 — Voiceover, Music, Captions and the Final Export Ladder

**Course:** Create Short Video Film using AI (TGS-2020505925) · **Version v12.0** · 27 September 2026  
**Topic 04:** AI Video Generation, Animation and Video Analytics  
**Outcome:** ELO4 · **In-class time:** 30 minutes of scheduled practical time

| Competency | Statement |
|---|---|
| Ability A5 | Design and apply machine-learning based methods for object detection, object tracking and activity recognition |
| Ability A6 | Design and apply video analytics algorithms for high-level video analytics tasks |
| Knowledge K9 | Object segmentation, detection and recognition |
| Knowledge K10 | Activity tracking, generative models, scene understanding and event discovery |

---

## Scenario

The last ten seconds of The Last Ferry are picture-locked. You finish them: validate the subtitles against the house caption rules, build and measure a placeholder mix (voiceover cues, a music bed at the brief's tempo, rain and a ferry horn, with the music ducked under the voice), and export a 16:9 master, a 9:16 Reel and a 4:5 feed version that follow MEI using her raincoat's segmentation mask.

## What you will produce

A caption file that passes every rule, an audio report (peak, RMS, voice-over-music margin), and three exported masters with burned-in captions — muxed to H.264/AAC when FFmpeg is installed.

**Tools:** Python 3 · opencv-python · NumPy · optional FFmpeg · optional: a voice, music and editing tool

## Environment

Install these once, before class if you can — the lab itself needs no network access after the dependencies are present:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install "opencv-python>=4.10" numpy
python3 -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"
```

Required: `opencv-python>=4.10`, `numpy`, `ffmpeg (optional, for muxing audio)`.

> **API currency.** Everything taught here runs on the **base `opencv-python` wheel** plus NumPy — no contrib modules and no downloaded model weights. SSIM is implemented in NumPy because `cv2.quality` is contrib-only. Generative steps are optional: every lab supplies SIMULATED reference media so it can be completed offline, and asks you to record the model ID and date if you generate your own.

## Workflow

1. Validate captions against the rules
2. Fix the caption file
3. Build and measure the mix
4. Reframe and export each format
5. Verify the delivered files

## Files in this folder

| Path | What it is |
|---|---|
| `reference/picture-lock.mp4` | 10-second picture lock of the last three shots (SIMULATED clip) |
| `data/captions.srt` | Subtitle file with five deliberate faults |
| `data/caption-rules.json` | Line count, line length, reading speed, duration and gap rules |
| `data/vo-cues.json` | Voiceover cue sheet with audio tags |
| `data/music-brief.json` | Music prompt, tempo, ducking and level targets |
| `data/export-profiles.json` | 16:9, 9:16 and 4:5 profiles with safe areas |
| `finish.py` | Runnable script — see the steps below |
| `PROMPTS.md` / `PROMPTS.pdf` | The reusable prompt and specification pack |
| `out/` | Everything you produce (created on first run) |

**Provenance.** Every image and clip in `reference/` is either a **SIMULATED** classroom illustration of *The Last Ferry*, rendered deterministically with OpenCV and labelled on the frame, or an **AI-generated** reference copied unchanged with a `PROVENANCE.md` beside it. Nothing in this folder may be relabelled: a simulated stand-in is never presented as model output or as a photograph.

## Steps

1. Read `data/vo-cues.json`. Each line carries an audio tag such as [out of breath] or [stunned whisper] — that is how delivery is directed line by line.

2. Read `data/music-brief.json`: the music prompt, 86 BPM, the ducking depth, the peak ceiling and the minimum voice-over-music margin.

3. Validate the captions. The check exits with status 1 and lists five faults.

   ```bash
   python3 finish.py captions --srt data/captions.srt --rules data/caption-rules.json
   ```

4. Copy the file to `out/captions-v2.srt` and fix it: delete the stray 'Four minutes.' cue, shorten cue 3 to 'No sender. / Just a tag, folded shut.' on two lines, and renumber. Re-run the check on your file until it passes.

   ```bash
   python3 finish.py captions --srt out/captions-v2.srt --rules data/caption-rules.json
   ```

5. Build and measure the placeholder mix.

   ```bash
   python3 finish.py audio --srt out/captions-v2.srt --out out
   ```

6. Read the audio report: peak below −1 dBFS, and voice at least 6 dB above the music while the voice is active. Change `duck_db` to 0 and rerun: record the new margin, then restore 9.

7. Export everything.

   ```bash
   python3 finish.py all --srt out/captions-v2.srt --out out
   ```

8. Read the export ladder: the 9:16 Reel keeps about 31.6% of the master and follows MEI's raincoat mask; the 4:5 keeps about 45%. With FFmpeg each file is muxed to H.264 video and AAC audio.

9. Open `out/reels_9x16.mp4` (or `_final.mp4`). Check that the captions sit above the platform UI zone and that the SIMULATED label survived the crop.

10. Write `out/delivery-checklist.md`: captions pass, peak and margin, sizes and frame counts, subject in frame, provenance label present, AI-content disclosure set on upload.

11. Optional extension: replace the placeholder with a real voiceover and music track generated from the cue sheet and brief, then re-measure.

## Verify

> Your caption file passes every rule; the mix peaks at or below −1 dBFS with a voice margin of at least 6 dB; three exports are written with 240 frames each.

### Expected outputs

- out/captions-v2.srt passing the check
- out/mix-placeholder.wav and out/audio-report.json
- out/master_16x9.mp4, reels_9x16.mp4, feed_4x5.mp4 (+ _final.mp4 with FFmpeg)
- out/export-report.json and out/delivery-checklist.md

### Evidence checklist

Submit all of the following. Each item is something an assessor can look at.

- [ ] Failing caption check and your corrected caption file passing
- [ ] Audio report, and the margin with ducking switched off
- [ ] Export report with sizes, frame counts and kept percentages
- [ ] Delivery checklist including provenance and AI-content disclosure

## Troubleshooting

| Symptom | What to do |
|---|---|
| 'Fix the caption problems before exporting' | Burned-in captions cannot be edited; fix the SRT first. |
| 'ffmpeg not found: video only' | Install FFmpeg (brew install ffmpeg / winget install ffmpeg) or mux in your editor. |
| Captions overlap the platform buttons | Raise safe.bottom for that profile in export-profiles.json. |
| The vertical crop loses MEI | follow_subject must be true; check the coat colour range finds her. |

## References used in this lab

- **[S6]** Youri van Hofwegen, 'EXACTLY How to Make an AI Short Film (Full Workflow)', YouTube, 1 Jun 2026, youtube.com/watch?v=0v534yAyhwg — *Full video, 16:49*.  
  Reference-first principle (stop giving the model freedom); three reference types — characters, locations, props; casting attributes (genre, budget, era, archetype, identity, physique, details, outfit); a second, damaged-state location made by editing the first ('change nothing else'); director controls (genre, camera movement, speed ramp, duration, aspect ratio, audio); per-character emotion and intensity; the multi-shot prompt framework with dialogue in quotation marks; video reference versus start/end frame (mood carries over); three generations for dense action shots; assembly in a timeline editor.
- **[S7]** Mira AI, '6 AI Video Tools I'd Use To Make An AI Short Film', YouTube, 14 Jun 2026, youtube.com/watch?v=Whh8vCqboxQ — *Full video, 10:04*.  
  A multi-tool workflow: an LLM to plan the story shot by shot, a cinematic image model for character sheets (front, side, back, close-ups) and multi-angle environment grids, a design canvas for the storyboard with keyframe placeholders, a video model for motion, an AI music generator (instrumental, mood and tempo), and an editor; the six-point prompt framework (subject, action, environment, camera, style, constraints); timeline prompting; video extension to pass the previous clip; generations capped at about 15 seconds.
- **[S8]** Thomas Creates, 'How to Start Making AI Short Films in 2026', YouTube, 18 Sep 2026, youtube.com/watch?v=69_EJD4FEPg — *Video description and chapters, 12:42*.  
  Consistent characters, props and locations; animating cinematic shots; carrying the same lighting and look between scenes; generated narration; assembling the film.
- **[S10]** Youri van Hofwegen, 'How to Make Your First AI Movie (Full Guide)', YouTube, 11 Jun 2026, youtube.com/watch?v=fs5S867VQzg — *Video description, 17:03*.  
  Generating the story; building consistent characters and locations; JSON prompting; asset management; video references for connected scenes; editing; fixing voice continuity across clips.
- **[S11]** ElevenLabs, 'How to Make Your First AI Short Film (Full Tutorial)', YouTube, 9 Aug 2026, youtube.com/watch?v=47DH_VUa67A — *Chapters, 31:13*.  
  Explore cheaply with faster image models before committing credits; prompt structure across style, subject, objects and negative prompting; a character reference sheet; generate the voiceover FIRST and build the storyboard to match it; direct delivery line by line with audio tags; still frames before video; start and end frames; generate at lower resolution and upscale only the takes you keep; background music; sound effects; edit and trim on a timeline; regenerate with a new character.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
