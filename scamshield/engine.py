"""Scam Shield scoring engine.

Five weighted signal families combine into a 0-100 call-level risk score.
Every point maps to quoted transcript text so the score is explainable.

Signal families
---------------
1. urgency    — time pressure, deadlines, "act now"
2. authority  — impersonated institutions, badges, case numbers
3. payment    — irreversible rails (gift cards, wire, crypto, courier cash)
4. secrecy    — isolation tactics ("don't tell anyone", "stay on the line")
5. affect     — sentiment velocity from AssemblyAI (negative runs, victim distress)

Legitimacy markers (callback offers, verification language) SUBTRACT points so
ordinary calls don't get flagged. Known scam archetypes (scenarios.py) add
confidence-weighted score when the transcript matches a playbook.

Public API
----------
- analyze(transcript) -> Analysis        (rich object; used by CLI)
- score_transcript(transcript) -> dict   (flat dict; used by tests)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any

from .scenarios import match_scenarios

# ---------------------------------------------------------------- patterns

URGENCY = [
    (r"\b(right now|immediately|asap|as soon as (?:you|we) (?:can|hang ?up))\b", 18),
    (r"\b(within (?:the next )?(?:\d+ ?(?:minutes?|hours?)|an hour|one hour|two hours))\b", 22),
    (r"\b(act now|don'?t wait|no time (?:to (?:waste|lose))|time is running out)\b", 20),
    (r"\b(today only|final notice|last chance|before (?:it'?s|is) too late)\b", 20),
    (r"\b(your (?:account|case|file|benefits|card) will be (?:closed|terminated|suspended|cancelled))\b", 22),
    (r"\b(legal action will be taken|further action will be taken)\b", 20),
]

AUTHORITY = [
    (r"\b(officer|agent|detective|inspector|investigator)\b", 12),
    (r"\b(government|federal|police department|sheriff|law enforcement)\b", 14),
    (r"\b(case number|badge number|file number|reference number)\b", 14),
    (r"\b(department of|bureau of|administration|internal revenue)\b", 12),
    (r"\b(this call is (?:being )?(?:recorded|monitored))\b", 10),
    (r"\b(arrest warrant|warrant (?:out|for|in your name)|you will be arrested)\b", 24),
]

PAYMENT = [
    (r"\b(gift card|itunes card|google play card|steam card)\b", 30),
    (r"\b(wire transfer|western union|moneygram|money gram)\b", 28),
    (r"\b(bitcoin|bitcoin atm|crypto (?:wallet|atm)|ethereum)\b", 26),
    (r"\b(cash (?:app|deposit)|venmo|zelle)\b", 18),
    (r"\b(courier (?:will|is) (?:come|coming|pick)|envelope of cash|physical cash)\b", 26),
    (r"\b(pay|paying)\b[^.;]{0,25}?\b(fee|fine|penalty|bail|tax(?:es)?|bill|amount|dues?)\b[^.;]{0,20}?\b(of|now|immediately|first|right now|today)\b", 18),
    (r"\b(buy|purchase|get)\b[^.;]{0,40}?\b(gift|itunes|google play|steam)\s+cards?\b", 26),
    (r"\b(routing number|account number|bank details|card number|last (?:four|4) digits)\b", 14),
]

SECRECY = [
    (r"\b(don'?t tell (?:anyone|your (?:family|husband|wife|parents|bank))|not (?:to )?tell anyone)\b", 30),
    (r"\b(keep this (?:between us|confidential|private)|this (?:call|conversation) is confidential)\b", 24),
    (r"\b(stay on the line|do not hang up|don'?t disconnect)\b", 18),
    (r"\b(your (?:phone|line) (?:is|may be) (?:monitored|tapped|compromised))\b", 24),
    (r"\b(do not (?:verify|call|check) (?:this|with your bank|the number))\b", 28),
    (r"\b(don'?t verify this|do not verify this)\b", 28),
]

LEGIT = [
    (r"\b(call (?:us|me) back (?:at|on) the number (?:on|printed) (?:your statement|the back of your card))\b", -18),
    (r"\b(you can (?:verify|check) (?:this|me)|feel free to (?:call|hang up and call))\b", -16),
    (r"\b(no (?:payment|purchase|fee|action) (?:is )?(?:required|needed)|courtesy call)\b", -12),
    (r"\b(we (?:will never|would never) ask (?:you )?for)\b", -20),
    (r"\b(take your time|no rush|whenever (?:you|it'?s) convenient)\b", -12),
    (r"\b(confirm|confirming) (?:your )?appointment\b", -14),
]

NEGATION = [
    (r"\b(this is not a scam|we are not scammers|this is (?:a )?legitimate call)\b", "explicit denial"),
]

FAMILY_WEIGHTS = {
    "urgency": 0.20,
    "authority": 0.18,
    "payment": 0.26,
    "secrecy": 0.22,
    "affect": 0.14,
}

VERDICT_LABELS = ((70, "SCAM"), (45, "LIKELY SCAM"), (25, "SUSPICIOUS"), (0, "CLEAN"))


def _label(score: int) -> str:
    for floor, name in VERDICT_LABELS:
        if score >= floor:
            return name
    return "CLEAN"


# ---------------------------------------------------------------- data model

@dataclass
class SignalHit:
    family: str
    pattern: str
    quote: str
    speaker: str | None = None
    points: int = 0


@dataclass
class SpeakerProfile:
    speaker: str
    word_count: int = 0
    hits: list[SignalHit] = field(default_factory=list)

    @property
    def score(self) -> int:
        if not self.word_count:
            return 0
        raw = sum(h.points for h in self.hits) / max(self.word_count / 100.0, 0.5)
        return int(min(raw, 100))

    @property
    def role(self) -> str:
        if self.score >= 45:
            return "suspected scammer"
        if self.score < 15:
            return "likely victim/caller"
        return "unknown"


# ---------------------------------------------------------------- analysis

def _sentiment_stats(transcript: dict[str, Any]):
    results = transcript.get("sentiment_analysis_results") or []
    total = len(results)
    neg = [r for r in results if r.get("sentiment") == "NEGATIVE"]
    streak = best = 0
    for r in results:
        if r.get("sentiment") == "NEGATIVE":
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return results, neg, total, best


def analyze(transcript: dict[str, Any]) -> "Analysis":
    text = transcript.get("text", "") or ""
    utterances = transcript.get("utterances") or []
    if not utterances and text:
        utterances = [{"speaker": None, "text": text}]

    hits: list[SignalHit] = []
    legit_signals: list[tuple[str, int]] = []
    negations: list[str] = []
    speakers: dict[str, SpeakerProfile] = {}

    for utt in utterances:
        speaker = utt.get("speaker")
        utt_text = (utt.get("text") or "").strip()
        utt_l = utt_text.lower()
        if speaker is not None and speaker not in speakers:
            speakers[speaker] = SpeakerProfile(str(speaker))
        if speaker is not None:
            speakers[str(speaker)].word_count += len(utt_text.split())

        for family, table in (("urgency", URGENCY), ("authority", AUTHORITY),
                              ("payment", PAYMENT), ("secrecy", SECRECY)):
            for pattern, points in table:
                if re.search(pattern, utt_l):
                    hit = SignalHit(family, pattern, utt_text[:160], str(speaker) if speaker is not None else None, points)
                    hits.append(hit)
                    if speaker is not None:
                        speakers[str(speaker)].hits.append(hit)

        for pattern, points in LEGIT:
            if re.search(pattern, utt_l):
                legit_signals.append((pattern, points))
        for pattern, tag in NEGATION:
            if re.search(pattern, utt_l):
                negations.append(tag)

    # affect family from AssemblyAI sentiments
    results, neg, total, best_streak = _sentiment_stats(transcript)
    affect_pts = 0
    if best_streak >= 5:
        affect_pts += 12
    if total and len(neg) / total > 0.45:
        affect_pts += 8
    if affect_pts:
        for r in neg[:3]:
            hits.append(SignalHit("affect", "negative-sentiment-run",
                                  (r.get("text") or "")[:160],
                                  str(r["speaker"]) if r.get("speaker") is not None else None,
                                  affect_pts))

    fam_scores: dict[str, int] = {k: 0 for k in FAMILY_WEIGHTS}
    for h in hits:
        if h.family in fam_scores:
            fam_scores[h.family] += h.points
    fam_scores["affect"] = max(fam_scores["affect"], affect_pts)

    weighted = sum(FAMILY_WEIGHTS[f] * min(pts, 100) for f, pts in fam_scores.items())

    # scenario match
    scen_matches = match_scenarios(text)
    scenario, scen_conf, _ = scen_matches[0] if scen_matches else (None, 0.0, [])
    if scenario:
        weighted += 18 * scen_conf

    # legit discount using actual point values
    for _, pts in legit_signals:
        weighted += pts

    score = int(min(max(round(weighted), 0), 100))
    verdict = _label(score)

    return Analysis(
        score=score,
        verdict=verdict,
        scenario=scenario.name if scenario else None,
        scenario_confidence=round(scen_conf, 2),
        scenario_advice=scenario.advice if scenario else None,
        signals=hits,
        negations=negations,
        speakers=sorted(speakers.values(), key=lambda s: -s.score),
        victim_negative_turns=len([r for r in neg if r.get("speaker") is not None
                                   and str(r.get("speaker")) in {s.speaker for s in speakers.values() if s.score < 45}]),
        total_negative_turns=len(neg),
        legit_signals=legit_signals,
        best_negative_streak=best_streak,
    )


@dataclass
class Analysis:
    score: int
    verdict: str
    scenario: str | None
    scenario_confidence: float
    scenario_advice: str | None
    signals: list[SignalHit]
    negations: list[str]
    speakers: list[SpeakerProfile]
    victim_negative_turns: int
    total_negative_turns: int
    legit_signals: list[str]
    best_negative_streak: int
    explanation: str = ""

def score_transcript(transcript: dict[str, Any]) -> dict[str, Any]:
    """Flat-dict API (tests + simple callers)."""
    a = analyze(transcript)
    return {
        "score": a.score,
        "verdict": a.verdict,
        "scenario": a.scenario,
        "scenario_confidence": a.scenario_confidence,
        "signals": [asdict(s) for s in a.signals],
        "negations": a.negations,
        "speakers": [{"speaker": s.speaker, "score": s.score, "role": s.role,
                      "word_count": s.word_count, "hits": [asdict(h) for h in s.hits]}
                     for s in a.speakers],
        "victim_negative_turns": a.victim_negative_turns,
        "total_negative_turns": a.total_negative_turns,
        "legit_signals": [p for p, _ in a.legit_signals],
        "explanation": a.explanation,
    }
