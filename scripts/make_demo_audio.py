#!/usr/bin/env python3
"""Render demo audio for Scam Shield: a synthetic scam call + a legit call.

Two piper voices: lessac = scammer (Speaker A), amy = victim (Speaker B).
Output: demo_scam_call.wav, demo_legit_call.wav (16 kHz mono PCM16 — AAI-friendly).
"""
import subprocess, sys, os, glob

VOICE_A = os.path.expanduser("~/.openclaw/workspace/en_US-lessac-medium.onnx")
VOICE_B = os.path.expanduser("~/.openclaw/workspace/en_US-amy-medium.onnx")

SCAM = [
    ("A", "Hello? This is officer Daniels, calling from the internal revenue service, criminal investigation unit. Badge number four, four seven one."),
    ("B", "The I R S? Oh no, why are you calling me?"),
    ("A", "There is an arrest warrant out in your name for unpaid back taxes. Legal action will be taken within the next two hours. This is your last warning."),
    ("B", "An arrest warrant? What do I do?"),
    ("A", "Listen carefully. Do not hang up. Stay on the line until we resolve this. You must pay the tax fee of four thousand dollars right now, today only."),
    ("B", "I don't have that kind of money in my checking account."),
    ("A", "Then go to the store and buy google play gift cards. Read me the numbers on the back. Do not tell anyone. Keep this between us."),
    ("B", "Should I call my husband first?"),
    ("A", "Do not tell your family. If you disconnect this call, the police will be at your door in thirty minutes. Do not verify this with your bank. The clock is running."),
]
LEGIT = [
    ("A", "Hello, this is Sarah from City Dental. I'm calling to remind you of your appointment on Thursday at three P M."),
    ("B", "Oh yes, Thursday at three works for me. See you then!"),
    ("A", "Wonderful. Your appointment is confirmed. No payment is needed today, and no action is required. Thank you for choosing City Dental. Have a great day!"),
]

def render(lines, out):
    wavs = []
    for i, (who, text) in enumerate(lines):
        voice = VOICE_A if who == "A" else VOICE_B
        tmp = f"/tmp/ss_{i:02d}.wav"
        subprocess.run([sys.executable, "-m", "piper", "--model", voice, "--output-file", tmp, "--data-dir", os.path.dirname(voice) or "."],
                       input=text.encode(), check=True, capture_output=True)
        wavs.append(tmp)
    # concat with 500ms silence between turns
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono", "-t", "0.5", "/tmp/ss_sil.wav"],
                   check=True, capture_output=True)
    with open("/tmp/ss_concat.txt", "w") as f:
        for w in wavs:
            f.write(f"file '{w}'\nfile '/tmp/ss_sil.wav'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
                    "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", out], check=True, capture_output=True)
    print("wrote", out)

render(SCAM, "demo_scam_call.wav")
render(LEGIT, "demo_legit_call.wav")
