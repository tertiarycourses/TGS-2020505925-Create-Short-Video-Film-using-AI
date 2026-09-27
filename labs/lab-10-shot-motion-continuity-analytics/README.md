# Lab 10 — Shot, Motion and Continuity Analytics on the Assembled Sequence

**Course:** Create Short Video Film using AI (TGS-2020505925) · **Version v12.0** · 27 September 2026  
**Topic 04:** AI Video Generation, Animation and Video Analytics  
**Outcome:** ELO5 · **In-class time:** 60 minutes of scheduled practical time

| Competency | Statement |
|---|---|
| Ability A6 | Design and apply video analytics algorithms for high-level video analytics tasks |
| Knowledge K10 | Activity tracking, generative models, scene understanding and event discovery |

---

## Scenario

Five generated shots have been assembled into a 16-second sequence. Somewhere in it there is a flickering shot and a character whose coat slowly changes colour. You build the analytics that find them automatically: cut detection, background camera motion, a flicker index, CAMShift tracking of MEI's raincoat, hue-drift measurement and the first-appearance event — and score each against exact truth.

## What you will produce

A shot report (boundaries, camera movement, flicker), a tracking report (IoU, centre error, jitter, hue drift), the first-appearance event, and a timeline graphic, each compared with the truth file.

**Tools:** Python 3 · opencv-python · NumPy · no network

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

1. Detect cuts with two signals
2. Estimate camera motion on the background
3. Measure flicker per shot
4. Track the subject and measure hue drift
5. Report events and continuity defects

## Files in this folder

| Path | What it is |
|---|---|
| `reference/generated-sequence.mp4` | 16-second, five-shot sequence with injected flicker and identity drift (SIMULATED clip) |
| `data/analytics-config.json` | Cut, motion, flicker, colour and drift parameters |
| `data/sequence-truth.json` | Exact cuts, defects, subject boxes and first appearance (generated with the clip) |
| `continuity.py` | Runnable script — see the steps below |
| `PROMPTS.md` / `PROMPTS.pdf` | The reusable prompt and specification pack |
| `out/` | Everything you produce (created on first run) |

**Provenance.** Every image and clip in `reference/` is either a **SIMULATED** classroom illustration of *The Last Ferry*, rendered deterministically with OpenCV and labelled on the frame, or an **AI-generated** reference copied unchanged with a `PROVENANCE.md` beside it. Nothing in this folder may be relabelled: a simulated stand-in is never presented as model output or as a photograph.

## Steps

1. Read `data/sequence-truth.json`: 384 frames at 24 fps, cuts at frames 72, 168, 216 and 312, a flicker defect in one shot and an identity-drift defect in another.

2. Read `data/analytics-config.json`. A cut needs TWO signals: a pixel-difference jump above its recent level AND a histogram change. Write down why one signal is not enough.

3. Run the analytics.

   ```bash
   python3 continuity.py --clip reference/generated-sequence.mp4 --truth data/sequence-truth.json --config data/analytics-config.json --out out
   ```

4. Check the cuts: 4/4 found, 0 false. Now set `cut_min_hist` to 0 and rerun: the flicker shot produces false cuts. Restore 0.08 and record the evidence.

5. Check camera motion. S1 is a pan right (background moves about −5 px per frame). The estimate uses corner features on the BACKGROUND only, with the subject box excluded and a RANSAC fit. Explain why including the subject would label S2 a pan.

6. Check flicker: exactly one shot (S3, the box close-up) exceeds the flicker threshold. Give the index value and the threshold.

7. Check the event: MEI first appears at frame 72 (3.00 s). This is the timecode you would put in the edit decision list for her entrance.

8. Check tracking in S2: IoU(x) about 0.8 and jitter about 1 px — a stable track, and the coat hue stays at 23.

9. Check S4: the coat hue drifts from 23 to 13 and the colour tracker collapses (large jitter). Explain why identity drift both is detected by the hue measure AND breaks a colour-based tracker.

10. Open `out/timeline.png`: the red band marks the flicker shot, the orange band the drift shot, and the spikes are cuts.

11. Write `out/continuity-notes.md` for the editor: each defect, its timecode, the measure that found it, and the fix (regenerate S4 with the reference sheet re-attached; deflicker or regenerate S3).

12. Optional extension: export your own generated clips as one file with a matching truth file of cut frames and run the same analytics.

## Verify

> Cuts 4/4 with 0 false; S1 labelled pan right; only S3 flagged FLICKER; first appearance at frame 72; S2 stable and S4 DRIFT.

### Expected outputs

- out/shot-report.csv
- out/tracking-report.csv
- out/timeline.png
- out/continuity-report.json
- out/continuity-notes.md

### Evidence checklist

Submit all of the following. Each item is something an assessor can look at.

- [ ] Cut results against truth, and the false-cut evidence with cut_min_hist = 0
- [ ] Camera-motion result per shot with the background-only explanation
- [ ] Flicker index per shot with the threshold
- [ ] Tracking and hue-drift results for S2 and S4
- [ ] Editor's continuity notes with timecodes and fixes

## Troubleshooting

| Symptom | What to do |
|---|---|
| No cuts detected | Check cut_min_diff and cut_ratio; print the per-frame pixel difference to see the spikes. |
| Camera motion reads 'static' for everything | Too few background features: lower min_bg_features or goodFeaturesToTrack quality. |
| First appearance at frame 0 | Lanterns or windows matched the colour: use the tight coat range and the largest-blob rule. |
| CamShift box explodes in S4 | Expected: the coat left the tracked hue. That is the drift evidence. |

## References used in this lab

- **[S6]** Youri van Hofwegen, 'EXACTLY How to Make an AI Short Film (Full Workflow)', YouTube, 1 Jun 2026, youtube.com/watch?v=0v534yAyhwg — *Full video, 16:49*.  
  Reference-first principle (stop giving the model freedom); three reference types — characters, locations, props; casting attributes (genre, budget, era, archetype, identity, physique, details, outfit); a second, damaged-state location made by editing the first ('change nothing else'); director controls (genre, camera movement, speed ramp, duration, aspect ratio, audio); per-character emotion and intensity; the multi-shot prompt framework with dialogue in quotation marks; video reference versus start/end frame (mood carries over); three generations for dense action shots; assembly in a timeline editor.
- **[S13]** M. Tschochohei and F. Schenker, 'Multimodal Generative AI in the Enterprise: From Pixels to Profit', Packt, June 2026, ISBN 978-1-80611-167-1 — *Ch.5 pp.56-75; Ch.7 pp.106-119; Ch.8 pp.127-143*.  
  VAE, GAN and diffusion mechanisms and failure modes; prompt structure and subject lock; binary masks (white = editable), inpainting, outpainting and mask-free editing; spatial versus temporal coherence, 3-D U-Nets and diffusion transformers over spatiotemporal patches; long-running operation polling; responsible-AI risks (voice cloning, deepfakes, likeness) and transparency (C2PA Content Credentials, invisible watermarking, model cards).
- **[S14]** A. Mewada, M. A. Ansari, S. Ahmad and N. Singh (eds), 'AI-Generated Image and Video Synthesis', IEEE Press / Wiley, 2026, ISBN 9781394403110 — *Ch.1 pp.1-11; Ch.3 pp.35-44; Ch.7 pp.94-100*.  
  Frame-based versus temporal video generation and the temporal-consistency challenge; the sensors-to-synthesis layered architecture and split computing between edge and cloud; evaluation (FID, KID, LPIPS, CLIP faithfulness, FVD plus optical-flow agreement); memory = parameters x precision, quantisation to b bits scales by b/32, diffusion latency proportional to S steps (S x F for video).
- **[S17]** OpenCV 4.13 Python package and FFmpeg, verified locally on the delivery image — *cv2 4.13.0 (opencv-python 4.13.0.92); ffmpeg/ffprobe optional*.  
  Every lab command runs on the base opencv-python wheel plus NumPy: VideoCapture / VideoWriter, cvtColor, calcHist/compareHist, Canny, ORB_create + BFMatcher, HuMoments, inpaint, CLAHE, filter2D, fastNlMeansDenoisingColored, Haar cascades from cv2.data.haarcascades, HOGDescriptor_getDefaultPeopleDetector, CamShift and calcOpticalFlowFarneback. SSIM is implemented in NumPy because cv2.quality is contrib-only. FFmpeg is used only when present, to mux audio into the final export.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
