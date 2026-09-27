# Lab 03 — Prompt and Specification Pack

**Structured Prompting for Cinematic Stills**  
Create Short Video Film using AI (TGS-2020505925) · Version v12.0 · 27 September 2026

Six-field and JSON prompt patterns. Explore on a fast, cheap draft model at low resolution; commit credits only when the still is right.

> **Currency note.** Tools and model names are examples of a technique, not endorsements, and AI video features change month to month. The prompt patterns here are tool-neutral. Before relying on a feature, clip length, resolution or price, check the provider's current documentation and terms, and record the model ID and date of every generation you keep.

---

## 1. Six-field prose template

```text
@mei_sheet_v1 @night_market_plate_v1 @red_box_v1
SUBJECT: ...
ACTION: ...
ENVIRONMENT: ...
CAMERA: shot size, angle, lens, movement
STYLE: look, light, grain
CONSTRAINTS: what must not change
NEGATIVE: extra people, text, changed wardrobe
```

## 2. JSON prompt (repeatable and versionable)

```json
{"prompt_version": "shot2-v2", "subject": "MEI ...", "action": "...", "environment": "...", "camera": {"size": "medium", "angle": "eye level", "lens": "35mm", "move": "tracking left to right"}, "style": "...", "constraints": ["..."], "references": ["mei_sheet_v1"], "seed": 4127}
```

## 3. Prompt-rewriting switch

Many tools offer automatic prompt rewriting. Leave it ON for short exploratory prompts; turn it OFF for long, structured prompts so the model follows what you wrote.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
