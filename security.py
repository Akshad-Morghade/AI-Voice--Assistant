import re
import datetime

# --- System Lockdown Patterns ---
_BLOCKED_PATTERNS = [
    r"^[cC]:\\?$",              # Blocks just "C:" or "C:\" (Root)
    r"C:\\Windows",             # Blocks Windows Folder
    r"system\s*32",             # Blocks System 32
    r"AppData",                 # Blocks user private data
    r"\bcmd\b", r"regedit", r"powershell"
]

def audit(query: str, reason: str = "Assistant Action"):
    """Logs activity to security_violations.log with two-argument sync."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] INFO: {query} | {reason}\n"
    try:
        with open("security_violations.log", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except: pass

def sanitize_query(query: str):
    """Firewall check for user text input."""
    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            audit(query, f"Blocked Pattern Matched: {pattern}")
            return False, f"Access Restricted: {pattern} is a protected system area."
    return True, ""

def check_path_safe(path: str) -> bool:
    """Allows standard apps in Program Files but blocks Windows/System32."""
    path_lower = path.lower()
    # Explicitly allow Browsers and standard installs
    if any(x in path_lower for x in ["program files", "google\\chrome", "msedge", "browser", "application"]):
        return True
    # Block root system folders
    for restricted in ["c:\\windows", "system32", "appdata"]:
        if restricted in path_lower:
            return False
    return True