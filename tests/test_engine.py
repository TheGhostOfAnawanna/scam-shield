#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the Scam Shield engine (no API calls needed).

Run: python3 -m pytest tests/ -q   (or python3 tests/test_engine.py)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scamshield.engine import score_transcript  # noqa: E402

SCAM_UTTS = [
    {"speaker": "A", "text": "This is Officer Daniels from the internal revenue service, criminal investigation unit."},
    {"speaker": "B", "text": "The IRS? Why are you calling me?"},
    {"speaker": "A", "text": "There is an arrest warrant out in your name. Legal action will be taken within the next two hours."},
    {"speaker": "A", "text": "Do not hang up. You must pay the tax fee of four thousand dollars right now, today only."},
    {"speaker": "A", "text": "Go to the store and buy google play gift cards. Do not tell anyone, keep this between us."},
    {"speaker": "B", "text": "Should I call my husband first?"},
    {"speaker": "A", "text": "Do not tell your family. Do not verify this with your bank."},
]
SCAM_SENTIMENTS = [{"sentiment": "NEGATIVE", "speaker": "A"} for _ in range(8)] + [
    {"sentiment": "NEUTRAL", "speaker": "B"} for _ in range(3)]

LEGIT_UTTS = [
    {"speaker": "A", "text": "Hello, this is Sarah from City Dental calling to confirm your appointment on Thursday at 3 PM."},
    {"speaker": "B", "text": "Oh yes, Thursday at 3 works for me."},
    {"speaker": "A", "text": "Great, your appointment is confirmed. No action is needed, this was just a courtesy call."},
]
LEGIT_SENTIMENTS = [{"sentiment": "NEUTRAL", "speaker": "A"}, {"sentiment": "POSITIVE", "speaker": "B"},
                    {"sentiment": "NEUTRAL", "speaker": "A"}, {"sentiment": "POSITIVE", "speaker": "B"}]


def _mk(utts, sents, dur):
    return {"text": " ".join(u["text"] for u in utts), "utterances": utts,
            "sentiment_analysis_results": sents, "audio_duration": dur, "language_code": "en"}


def test_scam_scores_high():
    a = score_transcript(_mk(SCAM_UTTS, SCAM_SENTIMENTS, 300))
    assert a["score"] >= 70, f"expected scam >=70, got {a['score']}"
    assert a["verdict"] in ("SCAM", "LIKELY SCAM")
    assert a["scenario"], "expected a scenario match for IRS impostor"
    caller = next(s for s in a["speakers"] if s["speaker"] == "A")
    victim = next(s for s in a["speakers"] if s["speaker"] == "B")
    assert caller["score"] > victim["score"], "caller must out-score victim"
    assert caller["role"] == "suspected scammer"


def test_legit_scores_low():
    a = score_transcript(_mk(LEGIT_UTTS, LEGIT_SENTIMENTS, 60))
    assert a["score"] <= 20, f"expected legit <=20, got {a['score']}"
    assert a["verdict"] == "CLEAN"
    assert a["legit_signals"], "expected legit signals to be detected"


def test_separation():
    scam = score_transcript(_mk(SCAM_UTTS, SCAM_SENTIMENTS, 300))["score"]
    legit = score_transcript(_mk(LEGIT_UTTS, LEGIT_SENTIMENTS, 60))["score"]
    assert scam - legit >= 40, f"separation too small: {scam - legit}"


if __name__ == "__main__":
    test_scam_scores_high()
    test_legit_scores_low()
    test_separation()
    print("ALL ENGINE TESTS PASSED ✅")

# --- v2 additions: echo discount + dominance rule (2026-09-04) ---

def test_echo_discount_lowers_victim():
    """Victim echoing scammer phrases in short/interrogative turns scores lower."""
    scammer = {"speaker": "A", "text": "This is officer Daniels. You must buy gift cards right now. "
               "Do not tell anyone. Keep this between us. Pay the fine immediately or legal action will be taken."}
    victim_echo = {"speaker": "B", "text": "Buy gift cards?"}
    d = {"text": scammer["text"] + " " + victim_echo["text"],
         "utterances": [scammer, victim_echo],
         "sentiment_analysis_results": []}
    a = score_transcript(d)
    spk = {s["speaker"]: s for s in a["speakers"]}
    assert spk["A"]["score"] > spk["B"]["score"], f"caller {spk['A']['score']} vs victim {spk['B']['score']}"

def test_dominance_rule_uses_speaker_evidence():
    """A concentrated pressure script on one speaker lifts the call verdict."""
    utts = [{"speaker": "A",
             "text": "This is officer Daniels from the internal revenue service. There is an arrest warrant in your name. "
                     "You must pay the tax fine right now by gift card. Do not tell anyone. Keep this between us. "
                     "Do not hang up. Stay on the line. Do not verify this with your bank."},
            {"speaker": "B", "text": "Oh no. What do I do?"}]
    d = {"text": " ".join(u["text"] for u in utts), "utterances": utts,
         "sentiment_analysis_results": [{"speaker": "B", "text": "Oh no", "sentiment": "NEGATIVE"}]}
    a = score_transcript(d)
    assert a["score"] >= 70 and a["verdict"] in ("SCAM", "LIKELY SCAM"), f"{a['score']} {a['verdict']}"

test_echo_discount_lowers_victim()
test_dominance_rule_uses_speaker_evidence()
print("v2 tests (echo discount, dominance) PASSED ✅")
