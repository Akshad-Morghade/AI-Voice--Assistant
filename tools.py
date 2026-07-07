import re, webbrowser, os, pywhatkit, logging
from datetime import datetime
from ddgs import DDGS # 2026 Library Name
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume 
from security import audit, check_path_safe

logger = logging.getLogger(__name__)

def web_search(query: str) -> str:
    """Fetches live 2026 data using regional priority for Nagpur/India."""
    try:
        audit(query, "Live Web Search")
        with DDGS() as ddgs:
            # region='in-en' ensures you get Nagpur weather and Indian news
            results = [f"Source: {r['title']}\nData: {r['body']}" for r in ddgs.text(query, region='in-en', max_results=4)]
        return "\n\n".join(results) if results else "DATA_NOT_FOUND"
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return "CONNECTION_ERROR"

def play_youtube(query: str) -> str:
    """Forces autoplay and cleans command words."""
    clean = re.sub(r'\b(play|search|open|on|youtube|video|song)\b', '', query, flags=re.IGNORECASE).strip()
    if not clean:
        webbrowser.open("https://www.youtube.com")
        return "Opened YouTube Home Page."

    try:
        # Get the video URL and force autoplay parameters
        # Note: Browser settings MUST be set to 'Allow Sound' for this to move on its own
        pywhatkit.playonyt(clean)
        audit(query, f"Direct Play: {clean}")
        return f"SUCCESS: Attempting to play '{clean}' with autoplay enabled."
    except:
        webbrowser.open(f"https://www.youtube.com/results?search_query={clean.replace(' ', '+')}&autoplay=1")
        return f"SUCCESS: Searching YouTube for '{clean}'."

def calculate(expression: str) -> str:
    """Handles power (^) conversion for Python's math engine."""
    clean = re.sub(r"[^\d\+\-\*\/\.\(\)\%\^ ]", "", expression).replace("^", "**").strip()
    try:
        result = eval(clean, {"__builtins__": None}, {})
        return f"RESULT: {result}"
    except: return "MATH_ERROR"

def open_application(name: str) -> str:
    from config import APP_MAP
    path = APP_MAP.get(name.lower().strip())
    if path and check_path_safe(path):
        try:
            os.startfile(path)
            audit(name, "App Launched")
            return f"✅ Opened {name}."
        except Exception as e: return f"❌ Error: {e}"
    return "🔒 Blocked or Unknown application."

def get_time_date() -> str:
    return f"CURRENT_TIME: {datetime.now().strftime('%I:%M %p, %A, %B %d, %Y')}"