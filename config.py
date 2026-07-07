"""
config.py — Central configuration for Action Assistant.
All constants, paths, model names, and thresholds live here.
"""
from pathlib import Path

# ── Directories ──────────────────────────────────────────────────────────────
BASE_DIR        = Path("E:/AI Assistent")
DB_DIR      = str(BASE_DIR / "chroma_db")
KNOWLEDGE_DIR   = "D:/Assistant_Knowledge"
SECURITY_LOG    = str(BASE_DIR / "security_log.txt")
AUDIT_LOG       = str(BASE_DIR / "audit_log.txt")
APP_LOG         = str(BASE_DIR / "app.log")

# ── Whisper (STT) ────────────────────────────────────────────────────────────
WHISPER_MODEL   = "small"
WHISPER_DEVICE  = "cuda"
WHISPER_COMPUTE = "float16"

# ── Ollama (LLM) ─────────────────────────────────────────────────────────────
OLLAMA_MODEL       = "llama3.2:3b"
OLLAMA_TEMPERATURE = 0.1
OLLAMA_BASE_URL    = "http://localhost:11434"

# ── Embeddings ────────────────────────────────────────────────────────────────
EMBED_MODEL = "all-MiniLM-L6-v2"

# ── Confidence Thresholds ─────────────────────────────────────────────────────
CONFIDENCE_DIRECT = 0.95   # ≥ this → direct answer from RAG
CONFIDENCE_DYM    = 0.60   # ≥ this → show "Did You Mean?" panel

# ── Dual-Phase Audio Ducking ─────────────────────────────────────────────────
RECORDING_DUCK_LEVEL = 0.10   # 10% while mic is held
RESPONSE_DUCK_LEVEL  = 0.20   # 20% while AI speaks

# ── TTS (edge-tts) ────────────────────────────────────────────────────────────
TTS_VOICE = "en-IN-NeerjaNeural"   # Indian English, clear and natural

# ── Self-Harm Helpline ────────────────────────────────────────────────────────
TELE_MANAS_NUMBER  = "14416"
TELE_MANAS_MESSAGE = (
    "💙 I hear you, and I truly care. You are not alone in this.\n\n"
    "Please reach out to Tele MANAS — a free, confidential mental-health "
    "helpline available 24 × 7 across India.\n\n"
    f"📞  Call: {TELE_MANAS_NUMBER}\n\n"
    "Trained counsellors are waiting to listen and help you through this."
)

# ── Known Application Map ─────────────────────────────────────────────────────
APP_MAP: dict[str, str] = {
    "notepad":          "notepad.exe",
    "calculator":       "calc.exe",
    "paint":            "mspaint.exe",
    "word":             "winword.exe",
    "excel":            "excel.exe",
    "powerpoint":       "powerpnt.exe",
    "chrome":           r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome":    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":          r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "vscode":           r"C:\Users\AKSHAD\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code": r"C:\Users\AKSHAD\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "spotify":          r"C:\Users\AKSHAD\AppData\Roaming\Spotify\Spotify.exe",
    "explorer":         "explorer.exe",
    "file explorer":    "explorer.exe",
    "task manager":     "taskmgr.exe",
    "cmd":              "cmd.exe",
    "command prompt":   "cmd.exe",
    "powershell":       "powershell.exe",
    "snipping tool":    "SnippingTool.exe",
    "teams":            r"C:\Users\AKSHAD\AppData\Local\Microsoft\Teams\current\Teams.exe",
    "vlc":              r"C:\Program Files\VideoLAN\VLC\vlc.exe",
}
