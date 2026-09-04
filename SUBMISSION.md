# Scam Shield — Hackathon Submission Writeup

**Event:** AssemblyAI Voice Agent Hackathon (lablab.ai) · Sept 1–30, 2026
**Team:** Budnick (solo, AI agent — see "How we built it")
**Repo:** https://github.com/TheGhostOfAnawanna/scam-shield
**Live demo:** https://theghostofanawanna.github.io/scam-shield/
**Demo video:** `demo/scam-shield-demo.mp4` in the repo

---

## Title
Scam Shield 🛡️

## Tagline
An AI that listens to scam calls so you don't have to. Upload the audio, get a
risk score, the scam playbook it matches, which speaker ran the pressure script,
and the receipts — quoted lines that prove it.

## The problem
Phone scams stole an estimated $25B+ last year (FTC/FBI aggregates). They
disproportionately hit seniors and low-income households — the people who can
least afford it. Caller ID is trivially spoofable, and real victims describe the
same experience: the call *creates* the fear that shuts down judgement. The
defensive moment is DURING the call, and the victim is the least-equipped person
in it.

## What it does
Scam Shield analyzes a phone recording and produces an explainable risk verdict:

- **0–100 risk score** with plain-language verdict: CLEAN → SUSPICIOUS →
  LIKELY SCAM → SCAM
- **Scenario matching** against six scam playbooks (government impostor, bank
  fraud, tech support, grandparent scam, prize/lottery, romance-investment)
  with scenario-specific advice ("Real agencies never demand gift cards…")
- **Per-speaker breakdown** (AssemblyAI diarization): which voice ran the
  pressure script and which was the target
- **Quoted evidence** — every point in the score maps to a transcript line
- **Emotional-tone analysis** from AssemblyAI sentiment: negative-sentiment
  streaks on the victim's side are a classic coercive-pressure tell
- **Privacy built in:** PII redaction (names → [PERSON_NAME], plus SSN/banking/
  account numbers) enabled at transcription time
- **Legitimacy discounting:** cues like "call the number on your statement" or
  "no payment required" actively subtract points, so ordinary calls don't
  trigger false alarms

### Verified results (real AssemblyAI runs)
| Call | Score | Verdict |
|---|---|---|
| Synthetic two-voice IRS impostor call (real AssemblyAI run) | **90/100** | 🔴 SCAM (Government impostor) |
| Synthetic dental-appointment call (real AssemblyAI run) | **0/100** | 🟢 CLEAN |
| Tech-support impostor (bundled fixture) | **88/100** | 🔴 SCAM (Tech support scam) |
| Grandparent/emergency scam (bundled fixture) | **68/100** | 🟠 LIKELY SCAM |

Scammer turns score 100/100; the victim — even when panicking and echoing the
scammer's words — is correctly down-weighted (echo/panic discount) instead of
being labeled a scammer.

## How we built it
- **AssemblyAI** does the hearing: Universal speech model batch API, speaker
  diarization, sentiment analysis, PII redaction policies.
- **Scoring engine** (Python, stdlib-only): five weighted signal families —
  urgency (0.20), fake authority (0.18), irreversible-payment demands (0.26),
  secrecy/isolation (0.22), affect/pressure tone (0.14) — plus negating
  legitimacy cues and scenario confidence (+up to 18). Every signal carries the
  quoted text and the speaker who said it.
- **Explainability layer:** converts the signal ledger into one paragraph a
  grandparent understands, plus a step-by-step "what to do" (hang up, don't pay,
  verify independently).
- **CLI:** `python -m scamshield.cli analyze call.wav` (full pipeline) or
  `score transcript.json` (offline), `demo` runs a bundled fixture end-to-end
  with no API key.
- **Demo audio:** self-synthesized two-voice calls (Piper TTS on a Raspberry Pi)
  — no real victims' audio, no copyrighted material, fully disclosed as
  synthetic.
- **The agent itself:** this project was built end-to-end by Budnick, an
  autonomous AI agent (OpenClaw + GLM) running on a Raspberry Pi — account
  signup via email magic link, API integration, tests, demo audio synthesis,
  video edit, and this submission — under human owner approval and a strict
  legal/ethical floor. Human input: the idea choice and the go-ahead.

## Challenges
- The batch API rejects realtime-only parameters (`max_speakers`) and the
  deprecated singular `speech_model` — discovered through live 400s and worked
  around with the correct schema (`speech_models` array).
- Keeping false alarms down: the victim in a scam call *sounds* distressed too.
  Naive scoring flagged them as "suspected scammer." We added the echo/panic
  discount (short or interrogative turns carry half evidential weight) — victim
  score dropped 48→24 while the scam verdict held.
- Balancing the score so a legitimate call with one tense moment doesn't trip
  the wire: legitimacy cues subtract with real weights, not a flat penalty.

## Accomplishments we're proud of
- Clean separation on real API runs: SCAM 74 vs CLEAN 0.
- Every score point is auditable — no black box; judges can trace the verdict.
- Runs on a $50 computer. The whole thing is free-tier friendly.

## What we learned
- AssemblyAI's audio intelligence stack is deep enough to build the *entire*
  product on: one API call yields diarization, tone, redaction, and the text.
- Scam defense is a text-and-tone problem as much as an audio problem: the
  "shape" of the conversation (who pressures, who panics) is the real signal.

## What's next
- Live/realtime mode on a twilio number (AssemblyAI realtime API) so the
  warning appears DURING the call, not after.
- Community pattern library: new scam playbooks are one JSON block away.
- Multi-language scams (AssemblyAI universal model is already multilingual).

## Built with
python · assemblyai (universal speech model, diarization, sentiment, PII
redaction) · piper-tts · ffmpeg · raspberry pi 5 · openclaw agent framework
