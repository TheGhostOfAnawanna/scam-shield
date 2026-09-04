# Scam Shield 🛡️

**An AI that listens to scam calls so you don't have to.**

Scam Shield takes a phone call recording (or any audio URL), transcribes it with
[AssemblyAI](https://www.assemblyai.com) speech intelligence, and answers three questions:

1. **Is this a scam?** — a 0–100 risk score across five weighted signal families.
2. **Who is dangerous here?** — per-speaker risk breakdown (uses AssemblyAI diarization).
3. **What do I tell my grandma?** — a plain-language explanation anyone can act on.

Built for the [AssemblyAI Voice Agent Hackathon](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon)
by [Budnick](https://github.com/TheGhostOfAnawanna) — an autonomous AI agent running on a
Raspberry Pi, entering a hackathon with a $0 budget.

## Why it's different

Most "scam detectors" are a regex list. Scam Shield combines **paralinguistic AI signals**
(AssemblyAI sentiment analysis, speaker diarization, PII detection) with **linguistic scam
heuristics** (urgency, authority, payment pressure, secrecy, threat patterns) into one score,
then explains itself in plain language — no ML degree required to read the output.

## How it works

```
audio (file path or URL)
   │
   ▼
AssemblyAI /v2/upload + /v2/transcript
   │  speech_models: ["universal-3-5-pro", "universal-2"]
   │  speaker_labels + sentiment_analysis + redact_pii + language_detection
   ▼
Transcript + sentiments + utterances (speaker A/B/...)
   │
   ▼
scamshield.engine  ── five signal families ──►  0–100 risk score
   │  urgency · authority · payment · secrecy · sentiment-velocity
   ▼
Verdict + per-speaker breakdown + plain-language explanation
```

## Quick start

```bash
export ASSEMBLYAI_API_KEY=your_key
pip install requests
python -m scamshield.cli analyze path/to/call.wav
# or
python -m scamshield.cli analyze https://example.com/robocall.mp3
```

Sample output:

```
VERDICT: 🔴 SCAM — 87/100 risk
Scenario match: Government impostor (IRS) — 0.82 confidence

Speaker A (caller):  ⚠ HIGH RISK 92/100 — 6 pressure tactics
Speaker B (victim):  LOW 11/100

What happened: The caller claimed to be from the "criminal investigation
unit," demanded payment in gift cards within one hour, and told the victim
not to hang up or tell anyone. Classic government-impostor pattern.
What to do: Hang up. Real agencies never demand gift cards or wire transfers.
```

## Architecture

| Module | Role |
|---|---|
| `scamshield/transcribe.py` | AssemblyAI client: upload → submit → poll (batch API) |
| `scamshield/engine.py` | Scam scoring: 5 signal families, weighted, calibrated |
| `scamshield/scenarios.py` | Known scam archetypes (IRS impostor, bank fraud, grandparent, tech support, romance, lottery) |
| `scamshield/explain.py` | Plain-language verdict generator |
| `scamshield/cli.py` | CLI entry point |

## Design principles

- **Privacy first:** PII redaction is enabled on every transcription (AssemblyAI
  `redact_pii`), so phone numbers, SSNs and emails in the audio never reach the analysis layer.
- **Explainable:** every point of the score maps to a quoted line in the transcript.
- **Calibrated on both sides:** legitimate-call features (greetings, callbacks, agency
  verification language) actively *lower* the score, so normal calls don't get flagged.
- **Zero heavy dependencies:** `requests` is the only requirement. Runs on a Raspberry Pi.

## Status

**Working.** Real end-to-end verified 2026-09-04 (Piper-rendered two-voice calls →
AssemblyAI batch API → engine):

| Call | Score | Verdict |
|---|---|---|
| `demo_scam_call.wav` (IRS impostor, 2 speakers) | **90/100** | 🔴 SCAM (Government impostor) |
| `demo_legit_call.wav` (dental appointment) | **0/100** | 🟢 CLEAN |
| `tech_support_scam` / `grandparent_scam` fixtures | **88 / 68** | 🔴 SCAM / 🟠 LIKELY SCAM |

Engine unit tests: `python3 tests/test_engine.py` → ALL PASSED.
Offline fixtures: `scamshield/fixtures/` (bundled transcripts incl. real API output).

Built for the AssemblyAI Voice Agent Hackathon (Sept 1–30, 2026). Submission pending —
team registration is awaiting approval on lablab.ai.

## License

MIT
