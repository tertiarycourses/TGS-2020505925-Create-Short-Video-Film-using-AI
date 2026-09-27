# Hands-On Labs — Create Short Video Film using AI

**WSQ Course Code:** TGS-2020505925 · **Version v12.0** · 27 September 2026  
**Conducted by:** Tertiary Infotech Academy Pte Ltd (UEN 201200696W)

Twelve labs across the five delivery topics, all building one 48-second short film, *The Last Ferry* — from the need analysis and the reference sheets to the final export ladder. Every folder is independently usable: it carries its own steps, data, local media and prompt pack, and needs no network access once the Python dependencies are installed.

| Lab | Title | Topic | Outcome | A | K | In-class |
|---:|---|---|---|---|---|---|
| 01 | [Film Needs Analysis and AI Production Pipeline Specification](lab-01-film-needs-analysis/README.md) | 01 | ELO1 | A1 | K1, K2 | within LU1 facilitation |
| 02 | [Frames, Formats and Aspect Ratios for Film Delivery](lab-02-frames-formats-aspect-ratios/README.md) | 02 | ELO2 | A2 | K3 | 15 min |
| 03 | [Structured Prompting for Cinematic Stills](lab-03-structured-prompting-stills/README.md) | 02 | ELO2 | A2 | K3, K4 | 15 min |
| 04 | [State Variants, Clean-Up and Reframing with Masks](lab-04-state-variants-reframing/README.md) | 02 | ELO2 | A2 | K4 | 15 min |
| 05 | [Cinematic Grading and Enhancement Measured with PSNR and SSIM](lab-05-grading-enhancement-metrics/README.md) | 02 | ELO2 | A2 | K4 | 15 min |
| 06 | [Character Reference Sheets and Consistency Features](lab-06-character-consistency-features/README.md) | 03 | ELO3 | A4 | K5, K6 | 30 min |
| 07 | [Look Bible and Scene Continuity with Global Descriptors](lab-07-look-bible-scene-continuity/README.md) | 03 | ELO3 | A3 | K7 | 30 min |
| 08 | [Cast-Presence Detection and Detector Evaluation](lab-08-cast-detection-evaluation/README.md) | 04 | ELO4 | A5 | K8, K9 | 60 min |
| 09 | [Storyboard to Shot Prompts, Start and End Frames, and the Animatic](lab-09-storyboard-shot-prompts/README.md) | 04 | ELO4 | A5, A6 | K8, K10 | 30 min |
| 10 | [Shot, Motion and Continuity Analytics on the Assembled Sequence](lab-10-shot-motion-continuity-analytics/README.md) | 04 | ELO5 | A6 | K10 | 60 min |
| 11 | [Voiceover, Music, Captions and the Final Export Ladder](lab-11-sound-captions-final-export/README.md) | 04 | ELO4 | A5, A6 | K9, K10 | 30 min |
| 12 | [Cloud, Local and Hybrid Production Architecture Evaluation](lab-12-cloud-local-production-architecture/README.md) | 05 | ELO6 | A7, A8 | K11, K12, K13 | 60 min |

**Total scheduled practical time: 360 minutes (6 hours)** — matching the 360-minute practical allocation in the approved course proposal.

## Coverage

| Code | Statement | Labs |
|---|---|---|
| A1 | Identify the needs of vision systems technology in industrial applications | 01 |
| A2 | Apply the principles of processing, filtering and analysis methods for video data | 02, 03, 04, 05 |
| A3 | Analyse global feature descriptions | 07 |
| A4 | Design and implement feature extraction and representation methods | 06 |
| A5 | Design and apply machine-learning based methods for object detection, object tracking and activity recognition | 08, 09, 11 |
| A6 | Design and apply video analytics algorithms for high-level video analytics tasks | 09, 10, 11 |
| A7 | Design the architecture of applied vision systems | 12 |
| A8 | Design, develop and evaluate edge-based and cloud-based systems | 12 |
| K1 | Vision system concepts | 01 |
| K2 | Business applications of vision systems | 01 |
| K3 | Methods to represent image and video data | 02, 03 |
| K4 | Image and video processing, filtering and transformation methods | 03, 04, 05 |
| K5 | Feature extraction and representation techniques | 06 |
| K6 | Local feature descriptions, edge, colour, texture and motion | 06 |
| K7 | Global feature descriptions, statistical and geometrical methods | 07 |
| K8 | Deep learning concepts | 08, 09 |
| K9 | Object segmentation, detection and recognition | 08, 11 |
| K10 | Activity tracking, generative models, scene understanding and event discovery | 09, 10, 11 |
| K11 | Vision system architecture | 12 |
| K12 | Vision communication protocols | 12 |
| K13 | Real-world design constraints and solution options | 12 |

## Environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install "opencv-python>=4.10" numpy
```

No lab requires a paid service. Where a generative model can optionally be used — for stills, clips, voice or music — the lab supplies a local reference set so the deliverable can be completed offline, and asks you to record which path you took. FFmpeg is optional (Lab 11 uses it to mux audio when present).

## Provenance rules that apply to every lab

1. A **SIMULATED** asset is a deterministic OpenCV illustration. It is never described as a photograph and never as generative-model output.
2. An **AI-generated** reference is copied unchanged and travels with a `PROVENANCE.md` recording the tool, date and prompt.
3. The label travels to every derivative: a crop or reframe of a simulated clip is re-labelled on export.
4. An **ANIMATIC** is labelled on every frame and is never submitted as a generated film.
5. Anything you generate yourself is recorded with the model ID, the prompt version and the watermark expectation.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W.
