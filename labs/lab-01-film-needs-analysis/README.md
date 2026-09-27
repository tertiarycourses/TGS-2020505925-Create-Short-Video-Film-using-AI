# Lab 01 — Film Needs Analysis and AI Production Pipeline Specification

**Course:** Create Short Video Film using AI (TGS-2020505925) · **Version v12.0** · 27 September 2026  
**Topic 01:** AI Vision and Generative AI for Short Film Creation  
**Outcome:** ELO1 · **In-class time:** facilitated within LU1 classroom facilitation (no separate practical minutes)

| Competency | Statement |
|---|---|
| Ability A1 | Identify the needs of vision systems technology in industrial applications |
| Knowledge K1 | Vision system concepts |
| Knowledge K2 | Business applications of vision systems |

---

## Scenario

Harbourline Ferries (a fictional ferry operator) turns 50. Six departments have each asked the studio for 'AI video'. You are the production lead: score the six film ideas against measurable need criteria, apply the likeness, rights and authenticity gates, choose a workflow pattern for each project you select, and specify the five-stage production pipeline for the anniversary film The Last Ferry — the film you will build in every later lab.

## What you will produce

A scored shortlist with a written rationale for every rejected or held project, a workflow-pattern choice per selected project, and a five-stage pipeline specification for The Last Ferry listing the references it needs.

**Tools:** Spreadsheet or text editor · Python 3 (optional baseline scorer) · no paid service required

## Environment

Install these once, before class if you can — the lab itself needs no network access after the dependencies are present:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install "opencv-python>=4.10" numpy
python3 -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"
```

Required: `python3 (optional — the baseline scorer uses the standard library only)`.

> **API currency.** Everything taught here runs on the **base `opencv-python` wheel** plus NumPy — no contrib modules and no downloaded model weights. SSIM is implemented in NumPy because `cv2.quality` is contrib-only. Generative steps are optional: every lab supplies SIMULATED reference media so it can be completed offline, and asks you to record the model ID and date if you generate your own.

## Workflow

1. Read the brief and the six film ideas
2. Score six need criteria per project
3. Apply the likeness, rights and authenticity gates
4. Choose a workflow pattern per selected project
5. Specify the five-stage pipeline for The Last Ferry

## Files in this folder

| Path | What it is |
|---|---|
| `reference/key-art-concept.png` | Concept key art for The Last Ferry (SIMULATED flat illustration, not AI output) |
| `brief/studio-brief.md` | The client brief with four hard constraints |
| `data/candidate-projects.csv` | Six candidate film projects with volume, turnaround, review, likeness, cost and rights fields |
| `data/need-criteria.json` | Weights, scoring rules, the three gates, the accept threshold and the three workflow patterns |
| `score_projects.py` | Runnable script — see the steps below |
| `PROMPTS.md` / `PROMPTS.pdf` | The reusable prompt and specification pack |
| `out/` | Everything you produce (created on first run) |

**Provenance.** Every image and clip in `reference/` is either a **SIMULATED** classroom illustration of *The Last Ferry*, rendered deterministically with OpenCV and labelled on the frame, or an **AI-generated** reference copied unchanged with a `PROVENANCE.md` beside it. Nothing in this folder may be relabelled: a simulated stand-in is never presented as model output or as a photograph.

## Steps

1. Create an `out/` folder inside this lab folder. Open `brief/studio-brief.md` and write down the four hard constraints in your own words: likeness and consent, rights, authenticity, and the 30% cost-reduction floor.

2. Open `data/candidate-projects.csv`. Confirm there are six projects and read every column, including `notes`. Nothing is scored yet.

   ```bash
   python3 -c "import csv;r=list(csv.DictReader(open('data/candidate-projects.csv')));print(len(r), list(r[0]))"
   ```

3. Open `data/need-criteria.json`. Note the six criteria (volume, repeatability, speed_value, review_tolerance, likeness_risk, cost_gap), their weights (which sum to 1.0), the accept threshold of 3.6 and the three gates.

4. Create `out/manual-scores.csv` with the headers project_id, volume, repeatability, speed_value, review_tolerance, likeness_risk, cost_gap, weighted_total, verdict. Score P1 (The Last Ferry) BY HAND first: finished minutes per quarter = episodes × seconds ÷ 60 = 7 × 30 ÷ 60 = 3.5 min, which scores 3 on volume.

5. Finish P1: cost gap = (38000 − 9000) ÷ 38000 = 0.76, which scores 5. Multiply each score by its weight and add them. You should reach 3.9. Show the arithmetic in the file.

6. Score the other five projects by hand in the same way. Then run the baseline scorer and compare. Reconcile every difference in one sentence — do not change a score just to match the baseline.

   ```bash
   python3 score_projects.py --csv data/candidate-projects.csv --criteria data/need-criteria.json --out out
   ```

7. Apply the gates BEFORE the threshold. P4 scores 3.8 but uses passenger faces without consent: REJECT. P5 is a factual statement by a real executive: AI is not appropriate, REJECT. P3 scores 4.1 but regulator approval is `pending`: HOLD, and name the evidence that would release it.

8. Write `out/decision.md`. For every rejected or held project, give one sentence that names the failed gate or criterion AND the number, e.g. 'P4 — likeness gate FAIL: 400 auto-sent videos a quarter built from unconsented passenger selfies'.

9. For each selected project (P1, P2, P6), choose a workflow pattern from `workflow_patterns` in the criteria file — all-in-one agent, multi-tool pipeline or hybrid/local — and justify it in one line using volume, control and review needs.

10. Specify the five-stage pipeline for The Last Ferry in `out/pipeline-spec.md`. SENSE: the inputs (brief, script, cast/location/prop references, voiceover). REPRESENT: master format 16:9, 24 fps, 1920×1080, plus the 9:16 cut-down.

11. Continue the specification. ANALYSE: the measurements every shot must pass (character consistency, look match, cast count, continuity). DECIDE: the approve / regenerate / re-edit rule and who signs off. SYNTHESISE: which generators produce stills, clips, voice and music.

12. List the references the film needs before any video is generated: two character sheets (MEI, CAPTAIN TAN), two locations (NIGHT MARKET, HARBOUR PIER in two states) and one prop (RED BOX). Explain in one sentence why reference-first reduces rerolls.

13. Optional extension (outside class time): paste the brief into an LLM with the planning prompt in `PROMPTS.md` and compare its shortlist with yours. Record where it ignored a gate.

## Verify

> Your shortlist selects P1, P2 and P6; holds P3 on an UNKNOWN gate; rejects P4 and P5 on gates; and every rejection names the criterion or gate and the number.

### Expected outputs

- out/manual-scores.csv with six rows and your arithmetic for P1
- out/baseline-scores.csv from the scorer, reconciled against your scores
- out/decision.md with a rationale for P3, P4 and P5 and a workflow pattern for P1, P2 and P6
- out/pipeline-spec.md with five stages and the reference list for The Last Ferry

### Evidence checklist

Submit all of the following. Each item is something an assessor can look at.

- [ ] Manual score sheet with the P1 calculation shown
- [ ] Written reconciliation of any difference with the baseline scorer
- [ ] One-sentence gate or criterion rationale per rejected or held project
- [ ] Workflow-pattern choice with a justification for each selected project
- [ ] Five-stage pipeline specification and reference list for The Last Ferry

## Troubleshooting

| Symptom | What to do |
|---|---|
| My total differs from the baseline by 0.1–0.3 | Check the band edges: 3.5 minutes is volume 3 (3–<10), a 0.3 cost gap is 3 not 1. |
| P4 passes on score — should I select it? | No. Gates are applied first; a failed likeness gate rejects the project whatever the score. |
| P3 has the second-highest score | It is HOLD, not SELECT: the regulator gate is UNKNOWN. Name the evidence needed. |
| python3 is not installed | Complete the lab by hand in a spreadsheet; the scorer is only a baseline. |

## References used in this lab

- **[S5]** Tertiary Courses public registration page and LMS-TMS course record — *https://www.tertiarycourses.com.sg/wsq-create-short-video-film-using-ai.html (checked 27 Sep 2026)*.  
  Registered title 'Create Short Video Film using AI', TGS code, the five delivery topics, the six learning outcomes, the course description (concept, storyline, script, characters, storyboard, text-to-image, image-to-video, text-to-video, cinematic shots, voiceover, music, sound effects, captions, final edit), 2-day/16-hour duration and target learners.
- **[S6]** Youri van Hofwegen, 'EXACTLY How to Make an AI Short Film (Full Workflow)', YouTube, 1 Jun 2026, youtube.com/watch?v=0v534yAyhwg — *Full video, 16:49*.  
  Reference-first principle (stop giving the model freedom); three reference types — characters, locations, props; casting attributes (genre, budget, era, archetype, identity, physique, details, outfit); a second, damaged-state location made by editing the first ('change nothing else'); director controls (genre, camera movement, speed ramp, duration, aspect ratio, audio); per-character emotion and intensity; the multi-shot prompt framework with dialogue in quotation marks; video reference versus start/end frame (mood carries over); three generations for dense action shots; assembly in a timeline editor.
- **[S7]** Mira AI, '6 AI Video Tools I'd Use To Make An AI Short Film', YouTube, 14 Jun 2026, youtube.com/watch?v=Whh8vCqboxQ — *Full video, 10:04*.  
  A multi-tool workflow: an LLM to plan the story shot by shot, a cinematic image model for character sheets (front, side, back, close-ups) and multi-angle environment grids, a design canvas for the storyboard with keyframe placeholders, a video model for motion, an AI music generator (instrumental, mood and tempo), and an editor; the six-point prompt framework (subject, action, environment, camera, style, constraints); timeline prompting; video extension to pass the previous clip; generations capped at about 15 seconds.
- **[S9]** Roboverse, 'The Complete Guide to Making Cinematic AI Videos (2026)', YouTube, 19 Jul 2026, youtube.com/watch?v=HMVSCEh72n4 — *Chapters, 10:30*.  
  Planning the story with an LLM; developing the narrative; creating consistent assets; staging the visual scenes; cinematic visual grading for a film look before animation; refining motion and prompts; generating clips; post-production and finishing.
- **[S12]** Sanky, 'How I Made an AI Short Drama in under 10 Minutes with ZooClaw + Seedance2', YouTube, 2 Jun 2026, youtube.com/watch?v=q8z5iK5Pm_s — *Chapters and description, 7:47*.  
  An all-in-one drama agent: upload one photo as the protagonist, describe the story, and the agent produces character-consistent shots, voiceover, music, storyboard and video; the prompt formula (premise, main character, scene style, numbered story beats, 'include voiceover, music and subtitles'); trade-off against node-based workflows.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
