"""
ui.py — Dark-mode Tkinter GUI for the Action Assistant.

Public surface used by main.py:
    ui = AssistantUI(on_text_submit, on_voice_start, on_voice_stop, on_tts_replay)
    ui.add_user_message(text)
    ui.add_ai_message(text)
    ui.show_dym_panel(suggestion)
    ui.hide_dym_panel()
    ui.set_status(text, color)
    ui.reset_voice_button()
    ui.update_kb_status(chunk_count)
    ui.run()          # blocks — starts mainloop
"""

import threading
import tkinter as tk
from tkinter import font, scrolledtext
from typing import Callable

# ── Colour palette ─────────────────────────────────────────────────────────────
C = {
    "bg":           "#0d0d0f",
    "surface":      "#18181b",
    "surface2":     "#27272a",
    "border":       "#3f3f46",
    "accent":       "#7c3aed",
    "accent_dim":   "#6d28d9",
    "green":        "#22c55e",
    "blue":         "#3b82f6",
    "yellow":       "#eab308",
    "red":          "#ef4444",
    "text":         "#f4f4f5",
    "muted":        "#a1a1aa",
    "user_bg":      "#1e1b4b",
    "ai_bg":        "#111113",
}


class AssistantUI:
    # ── Init ──────────────────────────────────────────────────────────────────
    def __init__(
        self,
        on_text_submit:  Callable[[str], None],
        on_voice_start:  Callable[[], None],
        on_voice_stop:   Callable[[], None],
        on_tts_replay:   Callable[[str], None],
        on_rebuild_kb:   Callable[[], None] = None,
    ):
        self.on_text_submit  = on_text_submit
        self.on_voice_start  = on_voice_start
        self.on_voice_stop   = on_voice_stop
        self.on_tts_replay   = on_tts_replay
        self.on_rebuild_kb   = on_rebuild_kb or (lambda: None)

        self.voice_mode         = False
        self._placeholder_active = False
        self._processing        = False

        self._build_window()

    # ── Window construction ───────────────────────────────────────────────────
    def _build_window(self):
        self.root = tk.Tk()
        self.root.title("⚡ Action Assistant")
        self.root.geometry("940x720")
        self.root.minsize(720, 520)
        self.root.configure(bg=C["bg"])

        self._fonts()
        self._header()
        self._chat_area()
        self._dym_panel()
        self._input_area()
        self._status_bar()

        self._greet()

    def _fonts(self):
        self.f_title  = font.Font(family="Segoe UI", size=13, weight="bold")
        self.f_body   = font.Font(family="Segoe UI", size=11)
        self.f_small  = font.Font(family="Segoe UI", size=9)
        self.f_bold   = font.Font(family="Segoe UI", size=11, weight="bold")
        self.f_mono   = font.Font(family="Consolas",  size=10)
        self.f_emoji  = font.Font(family="Segoe UI Emoji", size=15)

    # ── Header ────────────────────────────────────────────────────────────────
    def _header(self):
        bar = tk.Frame(self.root, bg=C["surface"], height=58)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Left — icon + title
        left = tk.Frame(bar, bg=C["surface"])
        left.pack(side="left", padx=16, pady=6)
        tk.Label(left, text="⚡", font=("Segoe UI Emoji", 22),
                 bg=C["surface"], fg=C["accent"]).pack(side="left")
        info = tk.Frame(left, bg=C["surface"])
        info.pack(side="left", padx=8)
        tk.Label(info, text="Action Assistant",
                 font=self.f_title, bg=C["surface"], fg=C["text"]).pack(anchor="w")
        tk.Label(info, text="llama3.2:3b  •  faster-whisper  •  ChromaDB",
                 font=self.f_small, bg=C["surface"], fg=C["muted"]).pack(anchor="w")

        # Right — status dot + rebuild button
        right = tk.Frame(bar, bg=C["surface"])
        right.pack(side="right", padx=16)
        self._dot = tk.Label(right, text="●", font=("Segoe UI", 13),
                             bg=C["surface"], fg=C["green"])
        self._dot.pack(side="left", padx=(0, 10))
        rb = tk.Button(right, text="🔄  Rebuild KB",
                       font=self.f_small, bg=C["surface2"], fg=C["muted"],
                       relief="flat", bd=0, padx=10, pady=5, cursor="hand2",
                       command=self._trigger_rebuild)
        rb.pack(side="left")
        self._hover(rb, C["border"], C["surface2"])

    # ── Chat area ─────────────────────────────────────────────────────────────
    def _chat_area(self):
        frame = tk.Frame(self.root, bg=C["bg"])
        frame.pack(fill="both", expand=True, padx=14, pady=(10, 0))

        self.chat = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, state="disabled", cursor="arrow",
            bg=C["bg"], fg=C["text"], font=self.f_body,
            relief="flat", padx=14, pady=14, spacing3=8,
        )
        self.chat.pack(fill="both", expand=True)

        # Text tags
        self.chat.tag_config("u_name",  foreground=C["accent"],  font=self.f_bold)
        self.chat.tag_config("u_text",  foreground=C["text"],     background=C["user_bg"],
                             lmargin1=6, lmargin2=6, rmargin=6)
        self.chat.tag_config("a_name",  foreground=C["green"],    font=self.f_bold)
        self.chat.tag_config("a_text",  foreground=C["text"],     background=C["ai_bg"])
        self.chat.tag_config("muted",   foreground=C["muted"],    font=self.f_small)
        self.chat.tag_config("gap",     spacing3=14)

    # ── "Did You Mean?" panel ─────────────────────────────────────────────────
    def _dym_panel(self):
        self._dym = tk.Frame(self.root, bg=C["surface2"])
        # Not packed yet — shown on demand

        tk.Label(self._dym, text="💡  Did you mean?",
                 bg=C["surface2"], fg=C["text"], font=self.f_bold
                 ).pack(side="left", padx=14, pady=8)

        self._dym_var = tk.StringVar()
        lbl = tk.Label(self._dym, textvariable=self._dym_var,
                       bg=C["surface2"], fg=C["accent"],
                       font=self.f_body, cursor="hand2")
        lbl.pack(side="left", padx=4)
        lbl.bind("<Button-1>", self._on_dym_click)

        tk.Button(self._dym, text="✕", bg=C["surface2"], fg=C["muted"],
                  relief="flat", bd=0, font=self.f_small, cursor="hand2",
                  command=self.hide_dym_panel).pack(side="right", padx=10)

    # ── Input area ────────────────────────────────────────────────────────────
    def _input_area(self):
        outer = tk.Frame(self.root, bg=C["surface"], pady=12)
        outer.pack(fill="x", side="bottom")
        inner = tk.Frame(outer, bg=C["surface"])
        inner.pack(fill="x", padx=16)

        # Entry box with highlight border
        entry_wrap = tk.Frame(inner, bg=C["surface2"], highlightthickness=2,
                              highlightbackground=C["border"],
                              highlightcolor=C["accent"])
        entry_wrap.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.entry = tk.Text(
            entry_wrap, height=2, bg=C["surface2"], fg=C["text"],
            font=self.f_body, relief="flat",
            insertbackground=C["accent"], wrap=tk.WORD, padx=12, pady=8,
        )
        self.entry.pack(fill="x", expand=True)
        self.entry.bind("<Return>",       self._on_enter)
        self.entry.bind("<Shift-Return>", lambda e: None)
        self.entry.bind("<FocusIn>",      self._clear_placeholder)
        self.entry.bind("<FocusOut>",     self._restore_placeholder)
        self._set_placeholder()

        # Buttons
        btn_frame = tk.Frame(inner, bg=C["surface"])
        btn_frame.pack(side="right")

        self.send_btn = tk.Button(
            btn_frame, text="Send  ➤", font=self.f_bold,
            bg=C["accent"], fg="white", relief="flat", bd=0,
            padx=18, pady=10, cursor="hand2",
            command=self._on_send,
        )
        self.send_btn.pack(side="left", padx=(0, 8))
        self._hover(self.send_btn, C["accent_dim"], C["accent"])

        self.mic_btn = tk.Button(
            btn_frame, text="🎤", font=("Segoe UI Emoji", 16),
            bg=C["surface2"], fg=C["text"],
            relief="flat", bd=0, padx=12, pady=6,
            cursor="hand2", width=3,
        )
        self.mic_btn.pack(side="left")
        self.mic_btn.bind("<ButtonPress-1>",   self._on_mic_press)
        self.mic_btn.bind("<ButtonRelease-1>", self._on_mic_release)

    # ── Status bar ────────────────────────────────────────────────────────────
    def _status_bar(self):
        bar = tk.Frame(self.root, bg=C["surface2"], height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status_var = tk.StringVar(value="● Idle")
        self._status_lbl = tk.Label(
            bar, textvariable=self._status_var,
            bg=C["surface2"], fg=C["muted"], font=self.f_small, anchor="w",
        )
        self._status_lbl.pack(side="left", padx=12)

        self._kb_var = tk.StringVar(value="")
        tk.Label(bar, textvariable=self._kb_var,
                 bg=C["surface2"], fg=C["muted"], font=self.f_small
                 ).pack(side="right", padx=12)

    # ── Greeting ──────────────────────────────────────────────────────────────
    def _greet(self):
        self.add_ai_message(
            "Hello! 👋  I'm your Action Assistant.\n\n"
            "I can help you with:\n"
            "  🔍  Web search & general questions\n"
            "  📂  Opening apps  (Notepad, Chrome, Spotify …)\n"
            "  🎵  Playing music on Spotify\n"
            "  📚  Answering from your knowledge base\n"
            "  🧮  Calculations & current time/date\n\n"
            "Type a message below, or hold  🎤  to speak."
        )

    # ── Placeholder helpers ───────────────────────────────────────────────────
    def _set_placeholder(self):
        self.entry.insert("1.0", "Type your message or hold 🎤 to speak …")
        self.entry.config(fg=C["muted"])
        self._placeholder_active = True

    def _clear_placeholder(self, _=None):
        if self._placeholder_active:
            self.entry.delete("1.0", tk.END)
            self.entry.config(fg=C["text"])
            self._placeholder_active = False

    def _restore_placeholder(self, _=None):
        if not self.entry.get("1.0", tk.END).strip():
            self._set_placeholder()

    # ── Event handlers ────────────────────────────────────────────────────────
    def _on_enter(self, event):
        self._on_send()
        return "break"

    def _on_send(self):
        if self._placeholder_active or self._processing:
            return
        text = self.entry.get("1.0", tk.END).strip()
        if not text:
            return
        self.entry.delete("1.0", tk.END)
        self._restore_placeholder()
        self.voice_mode = False
        threading.Thread(target=self.on_text_submit, args=(text,), daemon=True).start()

    def _on_mic_press(self, _=None):
        if self._processing:
            return
        self.voice_mode = True
        self.mic_btn.config(bg=C["green"], fg="white")
        self.set_status("🔴  Recording …", C["green"])
        threading.Thread(target=self.on_voice_start, daemon=True).start()

    def _on_mic_release(self, _=None):
        self.mic_btn.config(bg=C["blue"], fg="white")
        self.set_status("◉  Thinking …", C["blue"])
        threading.Thread(target=self.on_voice_stop, daemon=True).start()

    def _on_dym_click(self, _=None):
        suggestion = self._dym_var.get()
        self.hide_dym_panel()
        if suggestion:
            threading.Thread(
                target=self.on_text_submit, args=(suggestion,), daemon=True
            ).start()

    def _trigger_rebuild(self):
        self.set_status("◉  Rebuilding knowledge base …", C["yellow"])
        self._kb_var.set("🔄  Indexing …")
        threading.Thread(target=self.on_rebuild_kb, daemon=True).start()

    # ── Public chat methods ───────────────────────────────────────────────────
    def add_user_message(self, text: str):
        self.root.after(0, self._append_user, text)

    def add_ai_message(self, text: str):
        self.root.after(0, self._append_ai, text)

    def _append_user(self, text: str):
        self.chat.config(state="normal")
        self.chat.insert(tk.END, "\n", "gap")
        self.chat.insert(tk.END, "You\n",    "u_name")
        self.chat.insert(tk.END, f"{text}\n", "u_text")
        self.chat.config(state="disabled")
        self.chat.see(tk.END)

    def _append_ai(self, text: str):
        self.chat.config(state="normal")
        self.chat.insert(tk.END, "\n", "gap")
        self.chat.insert(tk.END, "⚡ Assistant  ", "a_name")

        # Clickable 🔊 speaker icon — unique tag per message
        tag = f"spk_{id(text)}"
        self.chat.insert(tk.END, "🔊\n", tag)
        self.chat.tag_config(tag, foreground=C["muted"], font=self.f_small)
        self.chat.tag_bind(
            tag, "<Button-1>",
            lambda _e, t=text: threading.Thread(
                target=self.on_tts_replay, args=(t,), daemon=True
            ).start(),
        )
        self.chat.tag_bind(tag, "<Enter>", lambda _: self.chat.config(cursor="hand2"))
        self.chat.tag_bind(tag, "<Leave>", lambda _: self.chat.config(cursor="arrow"))

        self.chat.insert(tk.END, f"{text}\n", "a_text")
        self.chat.config(state="disabled")
        self.chat.see(tk.END)

    # ── DYM panel ────────────────────────────────────────────────────────────
    def show_dym_panel(self, suggestion: str):
        self._dym_var.set(suggestion)
        if not self._dym.winfo_ismapped():
            # Insert above the input area
            self._dym.pack(fill="x", padx=14, pady=(0, 2), before=self.root.winfo_children()[-2])

    def hide_dym_panel(self):
        if self._dym.winfo_ismapped():
            self._dym.pack_forget()

    # ── Status helpers ────────────────────────────────────────────────────────
    def set_status(self, text: str, color: str = None):
        self._status_var.set(text)
        self._status_lbl.config(fg=color or C["muted"])
        # Mirror colour on header dot
        self._dot.config(fg=color or C["green"])

    def reset_voice_button(self):
        self.root.after(
            0, lambda: self.mic_btn.config(bg=C["surface2"], fg=C["text"])
        )

    def update_kb_status(self, count: int):
        self.root.after(0, lambda: self._kb_var.set(f"📚  {count} chunks indexed"))

    def set_processing(self, flag: bool):
        self._processing = flag

    # ── Hover helper ──────────────────────────────────────────────────────────
    def _hover(self, w, on_color, off_color):
        w.bind("<Enter>", lambda _: w.config(bg=on_color))
        w.bind("<Leave>", lambda _: w.config(bg=off_color))

    # ── Start ─────────────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()
