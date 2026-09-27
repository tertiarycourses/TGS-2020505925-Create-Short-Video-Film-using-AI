# Lab 05 — Cinematic Grading and Enhancement Measured with PSNR and SSIM

**Course:** Create Short Video Film using AI (TGS-2020505925) · **Version v12.0** · 27 September 2026  
**Topic 02:** AI Image Processing, Generation and Visual Enhancement  
**Outcome:** ELO2 · **In-class time:** 15 minutes of scheduled practical time

| Competency | Statement |
|---|---|
| Ability A2 | Apply the principles of processing, filtering and analysis methods for video data |
| Knowledge K4 | Image and video processing, filtering and transformation methods |

---

## Scenario

Raw generations arrive noisy, soft, flat or at draft resolution. Starting from the approved graded master of shot S2, you apply four typical defects, repair each with three candidate filters, and score every result with PSNR and SSIM. Then you apply the film's teal-and-orange look as a point operation.

## What you will produce

An enhancement score table (4 defects × 3 repairs + unrepaired), a before/after sheet of the best repair per defect, and a flat-versus-graded comparison with the measured shift in shadow and highlight warmth.

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

1. Apply four draft defects to the master
2. Repair each with three filters
3. Score with PSNR and SSIM
4. Apply the look as a LUT
5. Choose the repair per defect

## Files in this folder

| Path | What it is |
|---|---|
| `reference/graded-master.png` | Approved graded master of shot S2 (SIMULATED) |
| `data/degradations.json` | The four defects, their parameters and the look strength |
| `grade_lab.py` | Runnable script — see the steps below |
| `ssim.py` | Runnable script — see the steps below |
| `PROMPTS.md` / `PROMPTS.pdf` | The reusable prompt and specification pack |
| `out/` | Everything you produce (created on first run) |

**Provenance.** Every image and clip in `reference/` is either a **SIMULATED** classroom illustration of *The Last Ferry*, rendered deterministically with OpenCV and labelled on the frame, or an **AI-generated** reference copied unchanged with a `PROVENANCE.md` beside it. Nothing in this folder may be relabelled: a simulated stand-in is never presented as model output or as a photograph.

## Steps

1. Run the SSIM self-test. `cv2.quality` is contrib-only, so the course ships a NumPy SSIM.

   ```bash
   python3 ssim.py
   ```

2. Read `data/degradations.json`: sensor-like noise, soft focus, a flat log-like look and a half-resolution draft.

3. Run the lab. It degrades the master, repairs each defect three ways and scores everything against the master.

   ```bash
   python3 grade_lab.py --master reference/graded-master.png --degradations data/degradations.json --out out
   ```

4. Open `out/enhancement-scores.csv`. For noise, note that PSNR prefers the bilateral filter while SSIM prefers the Gaussian blur. Explain why: PSNR averages per-pixel error; SSIM rewards preserved local structure.

5. For soft focus, compare unsharp amount 0.8 with 2.5. The stronger one scores higher PSNR but lower SSIM: look for halos on the raincoat edge in `out/before-after.png`.

6. For the flat look, compare the two level settings. Clipping too hard (60–190) destroys structure: SSIM falls below 0.4.

7. For the half-resolution draft, compare nearest, cubic and Lanczos + unsharp. This is why you generate drafts at low resolution and upscale only the keepers.

8. Open `out/graded-look.png`. The LUT pushes shadows towards teal and highlights towards orange. Record the printed warmth shift. A LUT changes each pixel on its own value: it cannot sharpen or denoise.

9. Write `out/grade-decisions.md`: the repair you choose per defect and the metric AND visual reason for each choice.

10. Optional extension: grade one of your own stills with the same LUT and compare its warmth numbers with the master's.

## Verify

> Every repair beats the unrepaired SSIM for its defect except two you should explain: nearest-neighbour upscaling (identical to the unrepaired draft) and the over-clipped levels setting; the look shifts shadows cooler and highlights warmer.

### Expected outputs

- out/enhancement-scores.csv
- out/before-after.png
- out/graded-look.png
- out/grade-decisions.md

### Evidence checklist

Submit all of the following. Each item is something an assessor can look at.

- [ ] Score table with PSNR and SSIM for every repair
- [ ] One case where PSNR and SSIM disagree, explained by mechanism
- [ ] Flat-versus-graded image with the warmth measurements
- [ ] Chosen repair per defect with metric and visual justification

## Troubleshooting

| Symptom | What to do |
|---|---|
| ImportError: ssim | Run from inside the lab folder so ssim.py is importable. |
| fastNlMeans is slow | It is the most expensive filter; it still runs in a few seconds at 960x540. |
| PSNR is inf | The two images are identical — check you compared the repair, not the master. |
| My grade looks garish | Lower look_strength in degradations.json to 0.15 and rerun. |

## References used in this lab

- **[S9]** Roboverse, 'The Complete Guide to Making Cinematic AI Videos (2026)', YouTube, 19 Jul 2026, youtube.com/watch?v=HMVSCEh72n4 — *Chapters, 10:30*.  
  Planning the story with an LLM; developing the narrative; creating consistent assets; staging the visual scenes; cinematic visual grading for a film look before animation; refining motion and prompts; generating clips; post-production and finishing.
- **[S11]** ElevenLabs, 'How to Make Your First AI Short Film (Full Tutorial)', YouTube, 9 Aug 2026, youtube.com/watch?v=47DH_VUa67A — *Chapters, 31:13*.  
  Explore cheaply with faster image models before committing credits; prompt structure across style, subject, objects and negative prompting; a character reference sheet; generate the voiceover FIRST and build the storyboard to match it; direct delivery line by line with audio tags; still frames before video; start and end frames; generate at lower resolution and upscale only the takes you keep; background music; sound effects; edit and trim on a timeline; regenerate with a new character.
- **[S14]** A. Mewada, M. A. Ansari, S. Ahmad and N. Singh (eds), 'AI-Generated Image and Video Synthesis', IEEE Press / Wiley, 2026, ISBN 9781394403110 — *Ch.1 pp.1-11; Ch.3 pp.35-44; Ch.7 pp.94-100*.  
  Frame-based versus temporal video generation and the temporal-consistency challenge; the sensors-to-synthesis layered architecture and split computing between edge and cloud; evaluation (FID, KID, LPIPS, CLIP faithfulness, FVD plus optical-flow agreement); memory = parameters x precision, quantisation to b bits scales by b/32, diffusion latency proportional to S steps (S x F for video).
- **[S17]** OpenCV 4.13 Python package and FFmpeg, verified locally on the delivery image — *cv2 4.13.0 (opencv-python 4.13.0.92); ffmpeg/ffprobe optional*.  
  Every lab command runs on the base opencv-python wheel plus NumPy: VideoCapture / VideoWriter, cvtColor, calcHist/compareHist, Canny, ORB_create + BFMatcher, HuMoments, inpaint, CLAHE, filter2D, fastNlMeansDenoisingColored, Haar cascades from cv2.data.haarcascades, HOGDescriptor_getDefaultPeopleDetector, CamShift and calcOpticalFlowFarneback. SSIM is implemented in NumPy because cv2.quality is contrib-only. FFmpeg is used only when present, to mux audio into the final export.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
