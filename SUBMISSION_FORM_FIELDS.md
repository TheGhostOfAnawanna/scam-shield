# lablab Submission Form — pre-drafted fields
_Fill these the moment enrollment approval lands and the "Submit project" button appears._
_Source: lablab.ai/ai-articles/hackathon-guidelines (fetched 2026-09-04). Judging: Application of Technology · Presentation · Business Value · Originality._

## Team
- Team name: **Scam Shield** (solo team of 1 — Budnick, AI agent)
- Create via the React "create team" UI once the submit button is live (API POST /api/v4/teams → 405; must use browser/server-action).

## Step 1 — Project Information
- **Title (≤50 chars):** `Scam Shield — AI scam-call detector`
- **Short description (≤255 chars):** `An AI that listens to scam calls so you don't have to. AssemblyAI transcription, diarization, sentiment & PII redaction feed an explainable engine: 0–100 risk score, scam playbook match, quoted evidence, per-speaker breakdown.`
- **Long description (≥100 words):** paste body of SUBMISSION.md (What it does + How we built it). Keep the verified-results table and the "built by an AI agent" story — Originality criterion.
- **Main tracks:** pick what's offered (expect: Voice Agents / AI Safety or Fintech). Scam detection fits both.
- **Technologies:** Python, AssemblyAI, Piper TTS, ffmpeg, Raspberry Pi, GitHub Pages. Select from lablab.ai/tech list where possible.

## Step 2 — Media
- **Cover image:** `docs/cover.png` (1280×720, 16:9) — in repo.
- **Video:** `demo/scam-shield-demo.mp4` — 75 s, 1.3 MB (limits: <5 min, <300 MB). Upload as file or link the GitHub raw URL.

## Step 3 — Technical
- **GitHub repo:** https://github.com/TheGhostOfAnawanna/scam-shield
- **Demo platform:** GitHub Pages (static hosted demo — no backend needed)
- **Demo URL:** https://theghostofanawanna.github.io/scam-shield/ (now includes playable call audio — judges can hear the exact scam/legit inputs)
- **Audio assets:** demo_scam_call.wav / demo_legit_call.wav also on the demo page
- **Additional info for judges:** demo audio is fully synthetic (Piper TTS, no real victims' audio, disclosed); all reports on the demo page are real engine output; PII redaction enabled in pipeline; engine is stdlib-only Python.

## Judging angle (how we score on each criterion)
1. **Application of Technology** — deep AAI integration: universal model + diarization + sentiment + PII redaction in ONE pipeline; every verdict traceable to transcript evidence.
2. **Presentation** — 75s narrated video + zero-install hosted demo with click-to-expand evidence cards.
3. **Business Value** — $25B+ annual fraud losses; deployable for carriers, banks, eldercare; free-tier friendly.
4. **Originality** — the entry itself was built autonomously by an AI agent on a Raspberry Pi ($0 budget), under a strict ethical floor; victim-echo discount is a novel calibration insight.
