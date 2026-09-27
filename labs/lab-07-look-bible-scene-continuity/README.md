# Lab 07 — Look Bible and Scene Continuity with Global Descriptors

**Course:** Create Short Video Film using AI (TGS-2020505925) · **Version v12.0** · 27 September 2026  
**Topic 03:** AI Visual Features, Character Consistency and Scene Design  
**Outcome:** ELO3 · **In-class time:** 30 minutes of scheduled practical time

| Competency | Statement |
|---|---|
| Ability A3 | Analyse global feature descriptions |
| Knowledge K7 | Global feature descriptions, statistical and geometrical methods |

---

## Scenario

Eight shots of The Last Ferry have been generated across the NIGHT MARKET and the HARBOUR PIER. Two of them do not belong to the film's look. You analyse global descriptors — histograms, brightness, contrast, saturation, warmth, tint, Hu moments and edge density — against the approved master of each location, and write the film's numeric look bible.

## What you will produce

A look report for eight shots with the descriptor that moved for every off-look shot, a colour-coded look strip, and a look bible with the limits you would ship.

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

1. Describe the approved look in words
2. Fingerprint each location's master
3. Compare every shot with its own master
4. Name the descriptor that moved
5. Write the look bible limits

## Files in this folder

| Path | What it is |
|---|---|
| `reference/look-master-market.png` | Approved look master, NIGHT MARKET (SIMULATED) |
| `reference/look-master-pier.png` | Approved look master, HARBOUR PIER (SIMULATED) |
| `reference/sequence/shot_01.png … shot_08.png` | Eight generated shots, two off-look (SIMULATED) |
| `data/look-bible.json` | The look in words, the masters per location and the limits |
| `data/sequence-manifest.csv` | Which location each shot belongs to |
| `look_audit.py` | Runnable script — see the steps below |
| `PROMPTS.md` / `PROMPTS.pdf` | The reusable prompt and specification pack |
| `out/` | Everything you produce (created on first run) |

**Provenance.** Every image and clip in `reference/` is either a **SIMULATED** classroom illustration of *The Last Ferry*, rendered deterministically with OpenCV and labelled on the frame, or an **AI-generated** reference copied unchanged with a `PROVENANCE.md` beside it. Nothing in this folder may be relabelled: a simulated stand-in is never presented as model output or as a photograph.

## Steps

1. Read the `look` sentence in `data/look-bible.json`. Underline the parts a number could check: blue hour (brightness), teal shadows and warm practicals (warmth, tint), restrained saturation.

2. Compute one global descriptor by hand: the 2-D hue/saturation histogram of the pier master, normalised to sum to 1.

   ```bash
   python3 -c "import cv2;h=cv2.cvtColor(cv2.imread('reference/look-master-pier.png'),cv2.COLOR_BGR2HSV);H=cv2.calcHist([h],[0,1],None,[30,32],[0,180,0,256]);print(H.shape, float(H.sum()))"
   ```

3. First, try the WRONG design: temporarily set both entries of `masters` to the pier master and run the audit. Every market shot is flagged — a single master punishes legitimate differences between locations. Restore the file.

   ```bash
   python3 look_audit.py --sequence reference/sequence --manifest data/sequence-manifest.csv --bible data/look-bible.json --out out
   ```

4. Run the audit with one master per location (the restored bible).

   ```bash
   python3 look_audit.py --sequence reference/sequence --manifest data/sequence-manifest.csv --bible data/look-bible.json --out out
   ```

5. Read the verdicts. shot_05 is OFF LOOK on exposure, white balance and saturation — a 'noon' generation. shot_07 is OFF LOOK on tint and saturation — a magenta cast.

6. Explain the geometrical descriptor: Hu moments of the bright-practicals mask describe where the light sits in the frame. Which shots have the largest `hu_dist`, and is that a look problem or a composition choice?

7. Read the `jump_from_prev` column. Large jumps at location changes are expected; a large jump between two shots of the SAME location is a continuity warning.

8. Open `out/look-strip.png` (red = off look) and check it against your eye.

9. Tune one limit (for example `max_abs_d_mean_v`) so the six good shots pass with a margin and both bad shots still fail. Record the value and the margin.

10. Write `out/look-bible.md`: the look in one sentence, the per-location masters, the limits you ship, and the regrade or regenerate action for shot_05 and shot_07.

11. Optional extension: grade shot_05 with the Lab 05 LUT and levels and re-audit it. Can a grade rescue a daylight generation, or must it be regenerated?

## Verify

> Six shots are ON LOOK and exactly shot_05 and shot_07 are OFF LOOK, each with the descriptors that moved.

### Expected outputs

- out/look-report.csv
- out/look-strip.png
- out/look-bible.md

### Evidence checklist

Submit all of the following. Each item is something an assessor can look at.

- [ ] Evidence of the single-master failure and the per-location fix
- [ ] Look report with the moved descriptors named for shot_05 and shot_07
- [ ] Tuned limit with the measured margin
- [ ] Look bible with limits and a regrade-or-regenerate decision per off-look shot

## Troubleshooting

| Symptom | What to do |
|---|---|
| 'shots missing from the manifest' | Add a row for every shot file in data/sequence-manifest.csv. |
| Every shot is OFF LOOK | Check each shot is compared with the master of its own location. |
| hist_dist is high for a good shot | Framing changes the histogram; rely on exposure, warmth and tint as the tight gates. |
| cannot read master | Paths in look-bible.json are relative to the lab folder; run from there. |

## References used in this lab

- **[S8]** Thomas Creates, 'How to Start Making AI Short Films in 2026', YouTube, 18 Sep 2026, youtube.com/watch?v=69_EJD4FEPg — *Video description and chapters, 12:42*.  
  Consistent characters, props and locations; animating cinematic shots; carrying the same lighting and look between scenes; generated narration; assembling the film.
- **[S9]** Roboverse, 'The Complete Guide to Making Cinematic AI Videos (2026)', YouTube, 19 Jul 2026, youtube.com/watch?v=HMVSCEh72n4 — *Chapters, 10:30*.  
  Planning the story with an LLM; developing the narrative; creating consistent assets; staging the visual scenes; cinematic visual grading for a film look before animation; refining motion and prompts; generating clips; post-production and finishing.
- **[S14]** A. Mewada, M. A. Ansari, S. Ahmad and N. Singh (eds), 'AI-Generated Image and Video Synthesis', IEEE Press / Wiley, 2026, ISBN 9781394403110 — *Ch.1 pp.1-11; Ch.3 pp.35-44; Ch.7 pp.94-100*.  
  Frame-based versus temporal video generation and the temporal-consistency challenge; the sensors-to-synthesis layered architecture and split computing between edge and cloud; evaluation (FID, KID, LPIPS, CLIP faithfulness, FVD plus optical-flow agreement); memory = parameters x precision, quantisation to b bits scales by b/32, diffusion latency proportional to S steps (S x F for video).
- **[S17]** OpenCV 4.13 Python package and FFmpeg, verified locally on the delivery image — *cv2 4.13.0 (opencv-python 4.13.0.92); ffmpeg/ffprobe optional*.  
  Every lab command runs on the base opencv-python wheel plus NumPy: VideoCapture / VideoWriter, cvtColor, calcHist/compareHist, Canny, ORB_create + BFMatcher, HuMoments, inpaint, CLAHE, filter2D, fastNlMeansDenoisingColored, Haar cascades from cv2.data.haarcascades, HOGDescriptor_getDefaultPeopleDetector, CamShift and calcOpticalFlowFarneback. SSIM is implemented in NumPy because cv2.quality is contrib-only. FFmpeg is used only when present, to mux audio into the final export.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
