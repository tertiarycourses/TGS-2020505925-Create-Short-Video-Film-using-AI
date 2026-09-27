# Lab 08 — Prompt and Specification Pack

**Cast-Presence Detection and Detector Evaluation**  
Create Short Video Film using AI (TGS-2020505925) · Version v12.0 · 27 September 2026

Shot-list fields that make cast verification possible, and a review prompt.

> **Currency note.** Tools and model names are examples of a technique, not endorsements, and AI video features change month to month. The prompt patterns here are tool-neutral. Before relying on a feature, clip length, resolution or price, check the provider's current documentation and terms, and record the model ID and date of every generation you keep.

---

## 1. Cast line in every shot

Every shot in the shot list states who is on screen and how many speaking faces are visible (for example: 'S5 — MEI and CAPTAIN TAN, two faces, no extras'). That line is the expected value the detector is checked against.

## 2. Negative prompt for extras

```text
Negative: extra people in the foreground, crowd faces in focus, duplicated characters.
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
