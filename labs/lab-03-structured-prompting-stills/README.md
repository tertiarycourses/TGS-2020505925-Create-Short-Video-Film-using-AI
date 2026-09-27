# Lab 03 — Structured Prompting for Cinematic Stills

**Course:** Create Short Video Film using AI (TGS-2020505925) · **Version v12.0** · 27 September 2026  
**Topic 02:** AI Image Processing, Generation and Visual Enhancement  
**Outcome:** ELO2 · **In-class time:** 15 minutes of scheduled practical time

| Competency | Statement |
|---|---|
| Ability A2 | Apply the principles of processing, filtering and analysis methods for video data |
| Knowledge K3 | Methods to represent image and video data |
| Knowledge K4 | Image and video processing, filtering and transformation methods |

---

## Scenario

Shot S2 — MEI runs through the night market — keeps coming back different: the coat changes colour, she jumps around the frame, the look shifts. You lint a weak six-field prompt, rewrite it, and measure four prompt designs (A: free prose → D: subject, look, camera and constraints locked) on four takes each.

## What you will produce

A linted v1 prompt with its problems listed, your corrected v2 prompt in prose and JSON, and a variance table showing how much each prompt design reduced wardrobe, blocking, framing and look drift.

**Tools:** Python 3 · opencv-python · NumPy · optional: any image generator for your own takes

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

1. Lint the v1 prompt
2. Rewrite it as a six-field v2
3. Render it as prose, JSON and negative prompt
4. Measure variance across four designs
5. Record which field locks mattered most

## Files in this folder

| Path | What it is |
|---|---|
| `reference/takes/cellA_01.png … cellD_04.png` | 16 takes of shot S2: four prompt designs × four takes (SIMULATED, designed spread) |
| `data/shot2-fields-v1.json` | A weak six-field prompt with deliberate problems |
| `data/shot2-fields-v2-template.json` | The v2 template with the subject and references filled in |
| `data/prompt-factors.json` | What each design A-D locks, and what each measure means |
| `prompt_lab.py` | Runnable script — see the steps below |
| `PROMPTS.md` / `PROMPTS.pdf` | The reusable prompt and specification pack |
| `out/` | Everything you produce (created on first run) |

**Provenance.** Every image and clip in `reference/` is either a **SIMULATED** classroom illustration of *The Last Ferry*, rendered deterministically with OpenCV and labelled on the frame, or an **AI-generated** reference copied unchanged with a `PROVENANCE.md` beside it. Nothing in this folder may be relabelled: a simulated stand-in is never presented as model output or as a photograph.

## Steps

1. Read `data/prompt-factors.json`: the six fields are subject, action, environment, camera, style and constraints. Each design A→D locks more of them.

2. Lint the v1 prompt. It exits with status 1 and lists every problem: a missing constraints field, 'night' vs 'noon', 'close-up' vs 'wide shot', a repeated word and no references.

   ```bash
   python3 prompt_lab.py compose --fields data/shot2-fields-v1.json --out out
   ```

3. Copy `data/shot2-fields-v2-template.json` to `out/shot2-fields-v2.json`. Fill `action`, `environment`, `camera`, `style` and `constraints`. Use one camera description only (for example: medium shot, eye level, 35mm, tracking left to right).

4. Put the constraints in plain words: 'keep coat and scarf colours exactly as the reference sheet; no extra people in the foreground; subject stays in the centre third'.

5. Lint your v2 until it exits cleanly (status 0). Read the prose and JSON versions it writes and check the @element references come first.

   ```bash
   python3 prompt_lab.py compose --fields out/shot2-fields-v2.json --out out
   ```

6. Measure the 16 supplied takes. The script finds the raincoat by colour in every take and measures its hue, position, size and the background warmth.

   ```bash
   python3 prompt_lab.py variance --takes reference/takes --out out
   ```

7. Read `out/variance-by-cell.csv`. The variance index should fall from A (1.0) to D. Record which single step (A→B, B→C, C→D) removed the most of each kind of drift.

8. Open `out/takes-grid.png` and confirm the numbers match what you see row by row.

9. Write `out/prompt-notes.md`: which fields you will always lock for The Last Ferry, and which you will leave free for variety (for example crowd and steam).

10. Optional extension: generate four takes of your v2 prompt on a fast, cheap draft model at 1K, save them as `cellE_01.png` … into `reference/takes/` and rerun the variance command. Record the model ID and date.

## Verify

> v1 exits with status 1 and at least four problems; your v2 exits with status 0; the variance index falls in the order A > B > C > D.

### Expected outputs

- out/shot2-fields-v1.prompt.txt and .json with the lint report
- out/shot2-fields-v2.json, .prompt.txt and .prompt.json
- out/takes.csv, out/variance-by-cell.csv, out/takes-grid.png
- out/prompt-notes.md

### Evidence checklist

Submit all of the following. Each item is something an assessor can look at.

- [ ] Lint output for v1 and the clean lint output for your v2
- [ ] Your v2 prompt in prose and JSON with @element references
- [ ] Variance table for designs A-D with your reading of it
- [ ] Written list of always-locked and deliberately-free fields

## Troubleshooting

| Symptom | What to do |
|---|---|
| 'no raincoat found' | The take has no saturated yellow region: check the file is one of the supplied takes or a real generation of MEI. |
| My v2 still reports a CONFLICT | Remove one of the two terms; describe the camera once. |
| Lint says REPEATED | Say it once. Repetition dilutes a prompt; it does not emphasise it. |
| My own generated takes vary more than cell A | Expected: the supplied takes are a designed simulation. Lock the reference images first. |

## References used in this lab

- **[S7]** Mira AI, '6 AI Video Tools I'd Use To Make An AI Short Film', YouTube, 14 Jun 2026, youtube.com/watch?v=Whh8vCqboxQ — *Full video, 10:04*.  
  A multi-tool workflow: an LLM to plan the story shot by shot, a cinematic image model for character sheets (front, side, back, close-ups) and multi-angle environment grids, a design canvas for the storyboard with keyframe placeholders, a video model for motion, an AI music generator (instrumental, mood and tempo), and an editor; the six-point prompt framework (subject, action, environment, camera, style, constraints); timeline prompting; video extension to pass the previous clip; generations capped at about 15 seconds.
- **[S10]** Youri van Hofwegen, 'How to Make Your First AI Movie (Full Guide)', YouTube, 11 Jun 2026, youtube.com/watch?v=fs5S867VQzg — *Video description, 17:03*.  
  Generating the story; building consistent characters and locations; JSON prompting; asset management; video references for connected scenes; editing; fixing voice continuity across clips.
- **[S11]** ElevenLabs, 'How to Make Your First AI Short Film (Full Tutorial)', YouTube, 9 Aug 2026, youtube.com/watch?v=47DH_VUa67A — *Chapters, 31:13*.  
  Explore cheaply with faster image models before committing credits; prompt structure across style, subject, objects and negative prompting; a character reference sheet; generate the voiceover FIRST and build the storyboard to match it; direct delivery line by line with audio tags; still frames before video; start and end frames; generate at lower resolution and upscale only the takes you keep; background music; sound effects; edit and trim on a timeline; regenerate with a new character.
- **[S13]** M. Tschochohei and F. Schenker, 'Multimodal Generative AI in the Enterprise: From Pixels to Profit', Packt, June 2026, ISBN 978-1-80611-167-1 — *Ch.5 pp.56-75; Ch.7 pp.106-119; Ch.8 pp.127-143*.  
  VAE, GAN and diffusion mechanisms and failure modes; prompt structure and subject lock; binary masks (white = editable), inpainting, outpainting and mask-free editing; spatial versus temporal coherence, 3-D U-Nets and diffusion transformers over spatiotemporal patches; long-running operation polling; responsible-AI risks (voice cloning, deepfakes, likeness) and transparency (C2PA Content Credentials, invisible watermarking, model cards).
- **[S15]** Google AI for Developers — Gemini API image generation documentation — *https://ai.google.dev/gemini-api/docs/image-generation (verified 6 Sep 2026)*.  
  Native image models for text-to-image and conversational image editing; supported aspect ratios including 16:9, 9:16, 4:5 and 21:9; output sizes up to 4K by model; every generated image carries a SynthID watermark.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
