"""
app/ui/log_panel.py — Log viewer UI component with real-time colored log streams.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Dict, Any, Callable
from app.core.store import store
from app.ui.theme import (
    BG, BG2, BORDER, TXT, TXT_DIM, ACCENT, SUCCESS, WARN, ERR,
    FONT_LABEL, FONT_MONO, FONT_BTN
)


class LogPanelFrame(tk.Frame):
    """Log view panel that listens to the store Event Bus log events."""
    
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        
        self._build_ui()
        
        # Subscribe to Event Bus logs
        store.event_bus.subscribe("log", self._on_log_event)

    def _build_ui(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", pady=(4, 2))

        tk.Label(header, text="📋  Nhật ký dịch thuật", bg=BG, fg=TXT_DIM, font=FONT_LABEL).pack(side="left")

        # Clear button
        self.clear_btn = tk.Button(
            header, text="Xóa log", command=self.clear_log,
            bg=BG2, fg=TXT_DIM, activebackground=BORDER, activeforeground=TXT_DIM,
            font=FONT_BTN, relief="flat", bd=0,
            padx=6, pady=2, cursor="hand2"
        )
        self.clear_btn.pack(side="right")

        # Log Text Area
        self.log_txt = tk.Text(
            self, bg="#060810", fg=SUCCESS,
            font=FONT_MONO, insertbackground=ACCENT,
            relief="flat", bd=0, wrap="word",
            highlightthickness=1, highlightbackground=BORDER,
            state="disabled",
        )
        self.log_txt.pack(fill="both", expand=True)

        # Style tags for levels
        self.log_txt.tag_config("info",    foreground=ACCENT)
        self.log_txt.tag_config("ok",      foreground=SUCCESS)
        self.log_txt.tag_config("warn",    foreground=WARN)
        self.log_txt.tag_config("error",   foreground=ERR)
        self.log_txt.tag_config("dim",     foreground=TXT_DIM)
        self.log_txt.tag_config("default", foreground=TXT)

        # Scrollbar
        log_sb = ttk.Scrollbar(self, orient="vertical", command=self.log_txt.yview, style="Dark.Vertical.TScrollbar")
        self.log_txt.configure(yscrollcommand=log_sb.set)

    def append_log(self, msg: str, level: str = "default") -> None:
        """Appends a new log line with timestamp to the text area."""
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {msg}\n"
        
        self.log_txt.config(state="normal")
        self.log_txt.insert("end", line, level)
        self.log_txt.see("end")
        self.log_txt.config(state="disabled")

    def clear_log(self) -> None:
        """Clears all text in the log area."""
        self.log_txt.config(state="normal")
        self.log_txt.delete("1.0", "end")
        self.log_txt.config(state="disabled")

    # ---- STORE EVENT SUBSCRIPTIONS (routed thread-safely via self.after) ----
    def _on_log_event(self, message: str, level: str = "default") -> None:
        self.after(0, lambda: self.append_log(message, level))
