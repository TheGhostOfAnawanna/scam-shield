"""Plain-language verdict rendering for humans (and grandmas).

explain(analysis_or_dict) -> str  — the CLI contract.
render(...) -> str               — pretty multi-line report.
"""

from __future__ import annotations

from typing import Any

from .engine import Analysis

ICON = {"CLEAN": "🟢", "SUSPICIOUS": "🟡", "LIKELY SCAM": "🟠", "SCAM": "🔴"}

FAMILY_NAMES = {
    "urgency": "time pressure",
    "authority": "fake authority",
    "payment": "irreversible payment demands",
    "secrecy": "isolation tactics",
    "affect": "aggressive emotional tone",
}

_NEXT_STEPS = {
    "SCAM": "Do not pay anything and do not share codes, PINs or account numbers. Hang up.",
    "LIKELY SCAM": "Do not act on anything this caller says. Hang up and verify independently.",
    "SUSPICIOUS": "Stay cautious: don't share personal info, and verify the caller via an official number.",
    "CLEAN": "No strong scam pressure patterns detected in this call.",
}


def explain(a: Any) -> str:
    """One-paragraph human explanation."""
    if isinstance(a, Analysis):
        score, verdict = a.score, a.verdict
        scenario, conf = a.scenario, a.scenario_confidence
        fams: dict[str, int] = {}
        for s in a.signals:
            fams[s.family] = fams.get(s.family, 0) + s.points
        speakers = a.speakers
    else:  # flat dict from score_transcript
        score, verdict = a["score"], a["verdict"]
        scenario, conf = a.get("scenario"), a.get("scenario_confidence", 0.0)
        fams = {}
        for s in a.get("signals", []):
            fams[s["family"]] = fams.get(s["family"], 0) + s["points"]
        speakers = a.get("speakers", [])

    parts: list[str] = []
    if verdict in ("CLEAN",):
        parts.append("This call reads as routine: normal rhythm, no pressure tactics, no unusual payment demands.")
        return " ".join(parts)

    if scenario and conf >= 0.4:
        parts.append(f"This matches the known scam pattern '{scenario}' ({int(conf * 100)}% confidence).")
    top = sorted(fams.items(), key=lambda kv: -kv[1])[:2]
    if top and top[0][1] > 0:
        parts.append("Main red flags: " + " and ".join(FAMILY_NAMES.get(f, f) for f, _ in top) + ".")
    if speakers:
        worst = speakers[0] if isinstance(speakers[0], dict) else speakers[0]
        w_score = worst["score"] if isinstance(worst, dict) else worst.score
        w_id = worst["speaker"] if isinstance(worst, dict) else worst.speaker
        if w_score >= 45:
            parts.append(f"Speaker {w_id} is running a pressure script ({w_score}/100).")
    parts.append(_NEXT_STEPS.get(verdict, ""))
    return " ".join(p for p in parts if p)


def render(a: Any) -> str:
    if isinstance(a, Analysis):
        d = {
            "score": a.score, "verdict": a.verdict, "scenario": a.scenario,
            "scenario_confidence": a.scenario_confidence,
            "scenario_advice": a.scenario_advice,
            "speakers": [{"speaker": s.speaker, "score": s.score, "role": s.role,
                          "hits_count": len(s.hits)} for s in a.speakers],
            "signals": [asdict if False else {"family": s.family, "quote": s.quote,
                                              "points": s.points, "speaker": s.speaker}
                        for s in a.signals],
            "explanation": a.explanation,
        }
    else:
        d = a
    lines = [f"VERDICT: {ICON.get(d['verdict'], '⚪')} {d['verdict']} — {d['score']}/100 risk"]
    if d.get("scenario"):
        lines.append(f"Scenario match: {d['scenario']} ({int(d.get('scenario_confidence', 0) * 100)}%)")
    if d.get("speakers"):
        lines.append("")
        lines.append("Per-speaker risk:")
        for sp in d["speakers"]:
            lines.append(f"  Speaker {sp['speaker']}: {sp['score']}/100 ({sp.get('role', 'unknown')}) — "
                         f"{sp.get('hits_count', len(sp.get('hits', [])))} pressure tactic(s)")
    lines.append("")
    lines.append("What happened: " + (d.get("explanation") or ""))
    if d.get("scenario_advice"):
        lines.append("What to do: " + d["scenario_advice"])
    elif d.get("verdict"):
        lines.append("What to do: " + _NEXT_STEPS.get(d["verdict"], ""))
    if d.get("signals"):
        lines.append("")
        lines.append("Evidence:")
        for s in d["signals"][:8]:
            q = s.get("quote", "")
            lines.append(f"  • [{s.get('family')}]{' (spk ' + str(s.get('speaker')) + ')' if s.get('speaker') else ''} {q}")
    return "\n".join(lines)
