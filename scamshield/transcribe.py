"""AssemblyAI batch transcription client.

Uses the verified free-tier mechanics:
- speech_models is a plural ARRAY on batch: ["universal-3-5-pro", "universal-2"]
- auth header is the RAW key, no Bearer prefix
- upload = raw bytes POST to /v2/upload (not multipart)
- poll GET /v2/transcript/{id} until completed/error
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests

BASE_URL = "https://api.assemblyai.com"


class AssemblyAIError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not key:
        raise AssemblyAIError("ASSEMBLYAI_API_KEY environment variable is not set")
    return {"authorization": key}


def _submit_url(audio: str) -> str:
    """Public URLs can be submitted directly; local paths must be uploaded first."""
    if audio.startswith(("http://", "https://")):
        return audio
    if not os.path.exists(audio):
        raise AssemblyAIError(f"audio file not found: {audio}")
    with open(audio, "rb") as fh:
        resp = requests.post(f"{BASE_URL}/v2/upload", headers=_headers(), data=fh, timeout=300)
    if resp.status_code != 200:
        raise AssemblyAIError(f"upload failed ({resp.status_code}): {resp.text[:200]}")
    return resp.json()["upload_url"]


def transcribe(
    audio: str,
    poll_interval: float = 3.0,
    timeout: float = 600.0,
    redact_pii: bool = True,
    max_speakers: int = 4,
) -> dict[str, Any]:
    """Transcribe `audio` (local path or URL) and return the full transcript object.

    Enables the signal set Scam Shield scores on: diarization, sentiment,
    PII redaction, automatic language detection.
    """
    audio_url = _submit_url(audio)
    payload = {
        "audio_url": audio_url,
        "speech_models": ["universal-3-5-pro", "universal-2"],  # plural ARRAY on batch (realtime uses singular string)
        "speaker_labels": True,
        "sentiment_analysis": True,
        "punctuate": True,
        "format_text": True,
    }
    if redact_pii:
        payload["redact_pii"] = True
        payload["redact_pii_policies"] = [
            "us_social_security_number",
            "credit_card_number",
            "credit_card_cvv",
            "credit_card_expiration",
            "phone_number",
            "email_address",
            "banking_information",
            "account_number",
            "password",
            "person_name",
            "date_of_birth",
            "medical_condition",
        ]
        payload["redact_pii_sub"] = "entity_name"

    resp = requests.post(
        f"{BASE_URL}/v2/transcript", headers=_headers() | {"Content-Type": "application/json"},
        json=payload, timeout=60,
    )
    if resp.status_code not in (200, 201):
        raise AssemblyAIError(f"submit failed ({resp.status_code}): {resp.text[:300]}")
    tid = resp.json()["id"]

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        poll = requests.get(f"{BASE_URL}/v2/transcript/{tid}", headers=_headers(), timeout=30)
        if poll.status_code != 200:
            raise AssemblyAIError(f"poll failed ({poll.status_code}): {poll.text[:200]}")
        data = poll.json()
        status = data.get("status")
        if status == "completed":
            return data
        if status == "error":
            raise AssemblyAIError(f"transcription error: {data.get('error')}")
        time.sleep(poll_interval)
    raise AssemblyAIError(f"transcription timed out after {timeout}s (id={tid})")
