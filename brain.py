import logging
from datetime import datetime
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from config import OLLAMA_MODEL, OLLAMA_TEMPERATURE, OLLAMA_BASE_URL
from security import sanitize_query
from tools import web_search, play_youtube, calculate, get_time_date, open_application

llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0.1)

class AssistantState(TypedDict):
    user_input: str; security_ok: bool; denial_message: str; intent: str
    tool_result: str; web_context: str; final_response: str

def synthesizer_node(state):
    """The Final Reasoning Node: Enforces 2026 context and Clean Text formatting."""
    now = datetime.now().strftime("%I:%M %p")
    web_data = state.get("web_context", "")
    
    # Context Assembly
    parts = []
    if web_data and web_data not in ["DATA_NOT_FOUND", "CONNECTION_ERROR"]:
        parts.append(f"### [CRITICAL LIVE 2026 WEB DATA]:\n{web_data}")
    if state.get("tool_result"):
        parts.append(f"### [SYSTEM ACTION RESULT]: {state['tool_result']}")
    
    context = "\n\n".join(parts)
    query = state['user_input'].lower()

    # The Prompt: Fixed for Text-Only outputs when typing
    prompt = (
        f"You are Akshad's Assistant. Time: {now}.\n"
        f"CONTEXT DATA:\n{context}\n\n"
        f"USER: {state['user_input']}\n\n"
        "RULES:\n"
        "1. If LIVE WEB DATA is present, USE IT for weather/stocks. NEVER say 'I don't know'.\n"
        "2. If an app was opened or math was solved, confirm it concisely.\n"
        "3. FORMATTING RULE: Provide a clean, text-optimized response. Avoid phonetic filler words.\n"
        "4. If context is empty, explain that your live servers are currently under high load.\n"
        "RESPONSE:"
    )
    return {**state, "final_response": llm.invoke(prompt).strip()}

# --- Intent Router ---
def intent_node(state):
    q = state["user_input"].lower()
    if any(w in q for w in ["youtube", "play", "video"]): i = "YOUTUBE"
    elif any(w in q for w in ["weather", "stock", "price", "news", "current"]): i = "WEB"
    elif any(w in q for w in ["open", "launch"]): i = "APP"
    elif any(w in q for w in ["calculate", "math", "^"]): i = "MATH"
    elif any(w in q for w in ["time", "date"]): i = "TIME"
    else: i = "CHAT"
    return {**state, "intent": i}

# --- Graph Assembly ---
def _build_graph():
    g = StateGraph(AssistantState)
    g.add_node("security", security_node); g.add_node("intent", intent_node)
    g.add_node("web", lambda s: {**s, "web_context": web_search(s["user_input"])})
    g.add_node("tool", tool_node_logic); g.add_node("synth", synthesizer_node)
    g.add_node("blocked", lambda s: {**s, "final_response": f"🔒 {s['denial_message']}"})

    g.set_entry_point("security")
    g.add_conditional_edges("security", lambda s: "intent" if s["security_ok"] else "blocked", {"intent": "intent", "blocked": "blocked"})
    g.add_conditional_edges("intent", lambda s: "web" if s["intent"] == "WEB" else ("tool" if s["intent"] in ["YOUTUBE", "APP", "MATH", "TIME"] else "synth"), 
                            {"web": "web", "tool": "tool", "synth": "synth"})
    g.add_edge("web", "synth"); g.add_edge("tool", "synth")
    g.add_edge("synth", END); g.add_edge("blocked", END)
    return g.compile()

def tool_node_logic(state):
    i, q = state["intent"], state["user_input"]
    if i == "YOUTUBE": res = play_youtube(q)
    elif i == "APP": res = open_application(q)
    elif i == "MATH": res = calculate(q)
    elif i == "TIME": res = get_time_date()
    else: res = ""
    return {**state, "tool_result": res}

def security_node(state):
    from security import sanitize_query
    ok, msg = sanitize_query(state["user_input"])
    return {**state, "security_ok": ok, "denial_message": msg}

app = _build_graph()
def run_query(u): return app.invoke({"user_input": u, "security_ok": True, "denial_message": "", "web_context": "", "tool_result": ""})