# Lab 12 — Prompt and Specification Pack

**Cloud, Local and Hybrid Production Architecture Evaluation**  
Create Short Video Film using AI (TGS-2020505925) · Version v12.0 · 27 September 2026

Questions to ask any AI video platform before it enters the architecture.

> **Currency note.** Tools and model names are examples of a technique, not endorsements, and AI video features change month to month. The prompt patterns here are tool-neutral. Before relying on a feature, clip length, resolution or price, check the provider's current documentation and terms, and record the model ID and date of every generation you keep.

---

## 1. Vendor checklist

- Where is data processed and stored, and for how long?
- Are uploads or outputs used for training? Can we opt out?
- What are the commercial-use and likeness terms?
- Is there an API, and is it asynchronous (operation ID + polling or webhook)?
- Which provenance marks are applied (C2PA Content Credentials, invisible watermark)?
- Clip length cap, resolutions, aspect ratios and price per generated second?

## 2. Disclosure line for delivery

```text
This film was created with the help of generative AI. All characters are fictional.
```
Set the platform's AI-generated-content label on upload as well.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v12.0.
