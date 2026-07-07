"""
main.py — Entry point for the Action Assistant.
Fixed: AttributeError, AudioDucking logic, and Whisper Integration.
"""

import asyncio
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
import wave

# ── Project Imports ──────────────────────────────────────────────────────────
from config import (
    APP_LOG, WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE, TTS_VOICE,
    RECORDING_DUCK_LEVEL, RESPONSE_DUCK_LEVEL
)
from security import audit
from brain import run_query
from knowledge import build_index
from ui import AssistantUI

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-16s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(APP_LOG, encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")

# ════════════════════════════════════════════════════════════════════════════════
# 1. Audio Ducker (Fixed for 'Activate' Error)
# ════════════════════════════════════════════════════════════════════════════════

class AudioDucker:
    def __init__(self):
        self._original: float | None = None
        self._vol = None
        try:
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            # Fixed call for Windows Speakers
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._vol = interface.QueryInterface(IAudioEndpointVolume)
            logger.info("✅ Audio ducking ready.")
        except Exception as exc:
            logger.warning(f"⚠️ Audio ducking unavailable: {exc}")

    def _get(self) -> float:
        return self._vol.GetMasterVolumeLevelScalar() if self._vol else 1.0

    def _set(self, level: float):
        if self._vol:
            self._vol.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level)), None)

    def duck_recording(self):
        self._original = self._get()
        self._set(RECORDING_DUCK_LEVEL)

    def duck_response(self):
        if self._original is None: self._original = self._get()
        self._set(RESPONSE_DUCK_LEVEL)

    def restore(self):
        if self._original is not None:
            self._set(self._original)
            self._original = None

# ════════════════════════════════════════════════════════════════════════════════
# 2. Speech & TTS Wrappers (Synchronized)
# ════════════════════════════════════════════════════════════════════════════════

class SpeechRecognizer:
    def __init__(self):
        self._model = None
        self._audio = None
        self._stream = None
        self._frames = []
        self._active = False

    def _load(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)

    def start(self):
        self._load()
        import pyaudio
        self._frames, self._active = [], True
        self._audio = pyaudio.PyAudio()
        self._stream = self._audio.open(format=pyaudio.paInt16, channels=1, rate=16000,
                                        input=True, frames_per_buffer=1024, stream_callback=self._cb)
        self._stream.start_stream()

    def _cb(self, data, _fc, _ti, _st):
        import pyaudio
        if self._active: self._frames.append(data)
        return None, pyaudio.paContinue

    def stop(self) -> str:
        self._active = False
        if self._stream: self._stream.stop_stream(); self._stream.close()
        if self._audio: self._audio.terminate()
        if not self._frames: return ""

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh: path = fh.name
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000); wf.writeframes(b"".join(self._frames))

        segments, _ = self._model.transcribe(path, beam_size=5, vad_filter=True)
        text = " ".join(s.text for s in segments).strip()
        os.unlink(path)
        return text

class TTSEngine:
    def speak(self, text: str):
        import edge_tts
        async def _synth(path: str): await edge_tts.Communicate(text, TTS_VOICE).save(path)
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False); tmp.close()
        path = tmp.name
        try:
            asyncio.run(_synth(path))
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            f"Add-Type -AssemblyName presentationCore; $m=[System.Windows.Media.MediaPlayer]::new(); "
                            f"$m.Open([Uri]::new('{path}')); $m.Play(); Start-Sleep -Milliseconds 500; "
                            f"while ($m.NaturalDuration.HasTimeSpan -and $m.Position -lt $m.NaturalDuration.TimeSpan) "
                            f"{{ Start-Sleep -Milliseconds 100 }}; $m.Close()"], capture_output=True)
        finally:
            try: os.unlink(path)
            except: pass

# ════════════════════════════════════════════════════════════════════════════════
# 3. The Main Class (Fixed run() Method)
# ════════════════════════════════════════════════════════════════════════════════

class ActionAssistant:
    def __init__(self):
        self.ducker = AudioDucker()
        self.stt = SpeechRecognizer()
        self.tts = TTSEngine()
        self.ui = None
        self._processing = False

    def _process(self, text: str, use_voice_output: bool):
        if not text.strip():
            self._done()
            return
        self.ui.add_user_message(text)
        self.ui.set_status("◉ Thinking...", "#3b82f6")
        
        state = run_query(text)
        response = state.get("final_response", "Error processing request.")
        self.ui.add_ai_message(response)

        if use_voice_output:
            self.ui.set_status("🔊 Speaking...", "#22c55e")
            self.ducker.duck_response()
            self.tts.speak(response)
            self.ducker.restore()
        self._done()

    def _done(self):
        self._processing = False
        self.ui.set_processing(False)
        self.ui.reset_voice_button()
        self.ui.set_status("● Idle", "#22c55e")

    def on_text_submit(self, text: str):
        if self._processing: return
        self._processing = True
        self.ui.set_processing(True)
        threading.Thread(target=self._process, args=(text, False), daemon=True).start()

    def on_voice_start(self):
        self.ducker.duck_recording()
        self.stt.start()

    def on_voice_stop(self):
        if self._processing: return
        self._processing = True
        self.ui.set_processing(True)
        text = self.stt.stop()
        self.ducker.restore()
        if not text:
            self._done()
            return
        threading.Thread(target=self._process, args=(text, True), daemon=True).start()

    def on_tts_replay(self, text: str):
        threading.Thread(target=lambda: self.tts.speak(text), daemon=True).start()

    # ── THE RUN METHOD (Must be inside ActionAssistant) ─────────────────────
    def run(self):
        """Initializes the UI and starts the main loop."""
        self.ui = AssistantUI(
            on_text_submit=self.on_text_submit,
            on_voice_start=self.on_voice_start,
            on_voice_stop=self.on_voice_stop,
            on_tts_replay=self.on_tts_replay,
            on_rebuild_kb=lambda: build_index(force_rebuild=True)
        )
        logger.info("✅ UI and Logic Synchronized.")
        self.ui.run()

# ════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    ActionAssistant().run()