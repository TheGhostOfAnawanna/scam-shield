"""Scam Shield CLI.

Usage:
    python -m scamshield.cli analyze <audio-path-or-url> [--json]
    python -m scamshield.cli score <transcript.json> [--json]
    python -m scamshield.cli demo           # offline demo on bundled fixture
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .engine import analyze
from .explain import explain
from .transcribe import transcribe


def _load_offline_fixture() -> dict:
    """Offline demo transcript so the engine can be exercised without API credits."""
    p = Path(__file__).parent / "fixtures" / "irs_impostor.json"
    return json.loads(p.read_text())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="scamshield", description="Scam Shield — scam call analyzer")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_an = sub.add_parser("analyze", help="transcribe + score audio (path or URL)")
    p_an.add_argument("audio")
    p_an.add_argument("--json", action="store_true", dest="as_json")

    p_sc = sub.add_parser("score", help="score an existing AssemblyAI transcript JSON")
    p_sc.add_argument("transcript")
    p_sc.add_argument("--json", action="store_true", dest="as_json")

    sub.add_parser("demo", help="offline demo on bundled fixture")

    args = ap.parse_args(argv)

    if args.cmd == "analyze":
        print("Transcribing via AssemblyAI (this can take a minute)...", file=sys.stderr)
        t = transcribe(args.audio)
    elif args.cmd == "score":
        t = json.loads(Path(args.transcript).read_text())
    else:
        t = _load_offline_fixture()

    a = analyze(t)
    a.explanation = explain(a)
    if getattr(args, "as_json", False):
        out = {
            "score": a.score,
            "verdict": a.verdict,
            "scenario": a.scenario,
            "scenario_confidence": a.scenario_confidence,
            "signals": [asdict(s) for s in a.signals],
            "negations": a.negations,
            "speakers": [{"speaker": s.speaker, "score": s.score, "role": s.role,
                          "word_count": s.word_count,
                          "hits": [asdict(h) for h in s.hits]} for s in a.speakers],
            "victim_negative_turns": a.victim_negative_turns,
            "total_negative_turns": a.total_negative_turns,
            "legit_signals": [p for p, _ in a.legit_signals],
            "explanation": a.explanation,
        }
        print(json.dumps(out, indent=2))
    else:
        print(a.explanation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
