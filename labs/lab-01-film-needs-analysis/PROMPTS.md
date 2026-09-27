# Lab 01 — Prompt and Specification Pack

**Film Needs Analysis and AI Production Pipeline Specification**  
Create Short Video Film using AI (TGS-2020505925) · Version v12.0 · 27 September 2026

Planning prompts for the need analysis and for turning the selected project into a production plan. An LLM is a planning assistant: it does not apply your gates unless you tell it to, and you still sign the decision.

> **Currency note.** Tools and model names are examples of a technique, not endorsements, and AI video features change month to month. The prompt patterns here are tool-neutral. Before relying on a feature, clip length, resolution or price, check the provider's current documentation and terms, and record the model ID and date of every generation you keep.

---

## 1. Need-analysis assistant

```text
You are a production lead. Here are six candidate film projects (CSV) and our need criteria (JSON). Apply the three gates FIRST (ai_appropriate, rights_cleared, likeness_consent); any FAIL is REJECT and any UNKNOWN is HOLD. Then score the six criteria 0-5 using the rules exactly, compute the weighted total and compare with the 3.6 threshold. Show your arithmetic for every project. Do not invent data that is not in the files.
```

## 2. Story planning prompt (for The Last Ferry)

```text
Write a 48-second short film plan titled 'The Last Ferry'. Logline: a young courier races through a rain-soaked night market to deliver a red lacquered box to the last ferry - and discovers the box is addressed to her. Give me: (1) a character list with age, build, face and wardrobe for MEI and CAPTAIN TAN; (2) the locations and every story state of each location; (3) the props; (4) a shot list of 6-7 shots with duration, shot size, camera angle, camera movement and action; (5) every line of dialogue; (6) colour-grading direction. Keep every shot under 10 seconds.
```

## 3. All-in-one agent prompt formula

```text
Create a cinematic short drama about [premise].
Main character: use my uploaded image as the protagonist.
Scene style: [3-5 visual keywords].
Story structure:
1. [beat]
2. [beat]
3. [beat]
4. [ending]
Include voiceover narration, [mood] music and subtitles.
```
Review the agent's output for face consistency, scene continuity, camera movement, voice quality and music timing before accepting it.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
