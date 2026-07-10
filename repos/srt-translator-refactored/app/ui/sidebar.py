"""
app/ui/sidebar.py — Sidebar UI component handling configs and controls.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, List
from app.core.store import store
from app.core.config_manager import save_config
from app.utils.srt_io import lang_to_code
from app.ui.theme import (
    SIDEBAR_BG, BG3, ACCENT, TXT, TXT_DIM, BORDER, ERR, SUCCESS,
    FONT_LABEL, FONT_MONO, FONT_MAIN, FONT_BTN
)

SUPPORTED_LANGS = [
    ("Indonesian",          "indonesian"),
    ("Thai",                "thai"),
    ("Vietnamese",          "vietnamese"),
    ("Hindi",               "hindi"),
    ("Korean",              "korean"),
    ("Spanish (LATAM)",     "spanish"),
    ("French",              "french"),
    ("German",              "german"),
    ("Portuguese (BR)",     "portuguese"),
    ("English",             "english"),
    ("Turkish",             "turkish"),
    ("Filipino/Tagalog",    "filipino"),
    ("Russian",             "russian"),
    ("Japanese",            "japanese"),
    ("Chinese (Simplified)","chinese"),
    ("Arabic",              "arabic"),
]

MODELS = [
    "deepseek-v4-flash",
    "deepseek-v4-pro",
]

CONTENT_TYPES = [
    ("Tự động nhận diện", "auto"),
    ("Film / Drama",      "film"),
    ("Anime",             "anime"),
    ("Wuxia / Cổ trang",  "wuxia"),
    ("Tin tức / News",    "news"),
    ("Tài liệu",          "documentary"),
]


class SidebarFrame(tk.Frame):
    """Sidebar view component for configurations and pipeline control."""
    
    def __init__(self, parent, on_start: Callable[[], None], on_stop: Callable[[], None]):
        super().__init__(parent, bg=SIDEBAR_BG, width=300)
        self.on_start = on_start
        self.on_stop = on_stop
        
        self.pack_propagate(False)
        self._build_ui()
        self._load_initial_values()

    def _build_ui(self):
        # Gradient top accent bar
        accent_bar = tk.Frame(self, bg=ACCENT, height=3)
        accent_bar.pack(fill="x")

        inner = tk.Frame(self, bg=SIDEBAR_BG)
        inner.pack(fill="both", expand=True, padx=18, pady=14)

        # Title
        tk.Label(inner, text="MATRIX", bg=SIDEBAR_BG, fg=ACCENT, font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(inner, text="SRT-Translator  V2", bg=SIDEBAR_BG, fg=TXT_DIM, font=("Segoe UI", 10)).pack(anchor="w")
        self._sep(inner)

        # API Keys Entry
        self._section_label(inner, "🔑  API KEYS  (mỗi dòng 1 key)")
        self.api_keys_txt = tk.Text(
            inner, height=5, bg=BG3, fg=TXT,
            font=FONT_MONO, insertbackground=ACCENT,
            relief="flat", bd=0, wrap="none",
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        self.api_keys_txt.pack(fill="x", pady=(4, 2))
        
        self.key_count_lbl = tk.Label(inner, text="0 key(s)", bg=SIDEBAR_BG, fg=TXT_DIM, font=("Segoe UI", 9))
        self.key_count_lbl.pack(anchor="e")
        self.api_keys_txt.bind("<KeyRelease>", self._update_key_count)

        self._sep(inner)

        # Target Language Combobox
        self._section_label(inner, "🌐  NGÔN NGỮ ĐÍCH")
        self.lang_var = tk.StringVar()
        self.lang_combo = ttk.Combobox(
            inner, textvariable=self.lang_var,
            values=[l[0] for l in SUPPORTED_LANGS],
            state="readonly", style="Dark.TCombobox", font=FONT_MAIN,
        )
        self.lang_combo.pack(fill="x", pady=(4, 0))

        # Content Type Combobox
        self._section_label(inner, "🎬  LOẠI NỘI DUNG")
        self.ctype_var = tk.StringVar()
        self.ctype_combo = ttk.Combobox(
            inner, textvariable=self.ctype_var,
            values=[c[0] for c in CONTENT_TYPES],
            state="readonly", style="Dark.TCombobox", font=FONT_MAIN,
        )
        self.ctype_combo.pack(fill="x", pady=(4, 0))

        # Model Combobox
        self._section_label(inner, "🤖  MODEL")
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            inner, textvariable=self.model_var,
            values=MODELS,
            style="Dark.TCombobox", font=("Segoe UI", 9),
        )
        self.model_combo.pack(fill="x", pady=(4, 0))

        # Batch Size Slider
        self._section_label(inner, "📦  BATCH SIZE  (blocks/lượt)")
        bs_row = tk.Frame(inner, bg=SIDEBAR_BG)
        bs_row.pack(fill="x", pady=(4, 0))
        
        self.batch_var = tk.IntVar(value=45)
        self.batch_scale = tk.Scale(
            bs_row, variable=self.batch_var,
            from_=10, to=100, orient="horizontal",
            bg=SIDEBAR_BG, fg=TXT, troughcolor=BG3,
            highlightthickness=0, activebackground=ACCENT,
            sliderlength=14, bd=0,
            command=lambda v: self.batch_lbl.config(text=f"{int(float(v))} blocks"),
        )
        self.batch_scale.pack(side="left", fill="x", expand=True)
        self.batch_lbl = tk.Label(bs_row, text="45 blocks", bg=SIDEBAR_BG, fg=ACCENT, font=("Segoe UI", 10, "bold"), width=10)
        self.batch_lbl.pack(side="right")

        # Glossary Text Entry
        self._section_label(inner, "📖  GLOSSARY  (Tên gốc = Tên dịch)")
        self.glossary_txt = tk.Text(
            inner, height=4, bg=BG3, fg=TXT,
            font=FONT_MONO, insertbackground=ACCENT,
            relief="flat", bd=0, wrap="none",
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        self.glossary_txt.pack(fill="x", pady=(4, 2))
        self._mk_placeholder(self.glossary_txt, "Naruto = Naruto\nKonoha = Làng Lá\nSensei = Thầy")

        self._sep(inner)

        # Control Buttons at bottom
        btn_frame = tk.Frame(inner, bg=SIDEBAR_BG)
        btn_frame.pack(side="bottom", fill="x", pady=(4, 0))

        self.save_btn = self._mk_btn(btn_frame, "💾  Lưu cấu hình", self._save_settings, bg=BG3, fg=TXT_DIM, active_bg=BORDER)
        self.save_btn.pack(fill="x", pady=(0, 6))

        self.start_btn = self._mk_btn(btn_frame, "▶   BẮT ĐẦU DỊCH", self.on_start, bg=ACCENT, fg="#0a0a0a", active_bg="#33eeff")
        self.start_btn.pack(fill="x", pady=(0, 4))

        self.stop_btn = self._mk_btn(btn_frame, "■   DỪNG DỊCH", self.on_stop, bg="#2a0a12", fg=ERR, active_bg="#3d1020")
        # stop_btn is hidden initially, only shown during translation runs
        
    def _sep(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=8)

    def _section_label(self, parent, text):
        tk.Label(parent, text=text, bg=SIDEBAR_BG, fg=TXT_DIM, font=FONT_LABEL).pack(anchor="w", pady=(6, 0))

    def _mk_btn(self, parent, text, command, bg=BG3, fg=TXT, active_bg=BORDER):
        return tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground=active_bg, activeforeground=fg,
            font=FONT_BTN, relief="flat", bd=0,
            padx=12, pady=6, cursor="hand2",
        )

    def _mk_placeholder(self, widget: tk.Text, placeholder: str):
        widget._placeholder = placeholder
        widget._has_placeholder = False

        def _show_ph(event=None):
            if not widget.get("1.0", "end").strip():
                widget._has_placeholder = True
                widget.config(fg=TXT_DIM)
                widget.delete("1.0", "end")
                widget.insert("1.0", placeholder)

        def _hide_ph(event=None):
            if widget._has_placeholder:
                widget._has_placeholder = False
                widget.delete("1.0", "end")
                widget.config(fg=TXT)

        widget.bind("<FocusIn>",  _hide_ph)
        widget.bind("<FocusOut>", _show_ph)
        _show_ph()

    def _update_key_count(self, event=None):
        keys = self._get_keys_from_input()
        n = len(keys)
        self.key_count_lbl.config(
            text=f"{n} key(s) — {n} worker(s) song song",
            fg=SUCCESS if n > 0 else ERR,
        )

    def _get_keys_from_input(self) -> List[str]:
        raw = self.api_keys_txt.get("1.0", "end").splitlines()
        return [k.strip() for k in raw if k.strip()]

    def _parse_glossary(self) -> Dict[str, str]:
        if getattr(self.glossary_txt, '_has_placeholder', False):
            return {}
        raw = self.glossary_txt.get("1.0", "end").strip()
        glossary = {}
        for line in raw.splitlines():
            if "=" in line:
                parts = line.split("=", 1)
                src = parts[0].strip()
                tgt = parts[1].strip()
                if src and tgt:
                    glossary[src] = tgt
        return glossary

    def _load_initial_values(self):
        c = store.get("config")
        if not c:
            return

        # Load API keys
        self.api_keys_txt.delete("1.0", "end")
        self.api_keys_txt.insert("1.0", "\n".join(c.get("api_keys", [])))
        self._update_key_count()

        # Load language
        lang_key = c.get("target_language", "indonesian")
        for display, key in SUPPORTED_LANGS:
            if key == lang_key:
                self.lang_var.set(display)
                break
        if not self.lang_var.get():
            self.lang_combo.current(0)

        # Load content type
        ctype_key = c.get("content_type", "auto")
        for display, key in CONTENT_TYPES:
            if key == ctype_key:
                self.ctype_var.set(display)
                break
        if not self.ctype_var.get():
            self.ctype_combo.current(0)

        # Load model
        self.model_var.set(c.get("model", MODELS[0]))

        # Load batch size
        bs = c.get("batch_size", 45)
        self.batch_var.set(bs)
        self.batch_lbl.config(text=f"{bs} blocks")

        # Load glossary
        glossary = c.get("glossary", {})
        if glossary:
            lines = [f"{k} = {v}" for k, v in glossary.items()]
            self.glossary_txt.config(fg=TXT)
            self.glossary_txt._has_placeholder = False
            self.glossary_txt.delete("1.0", "end")
            self.glossary_txt.insert("1.0", "\n".join(lines))

    def _save_settings(self):
        settings = self.get_settings()
        try:
            save_config({
                "api_keys":        settings["api_keys"],
                "model":           settings["model"],
                "target_language": settings["lang"],
                "content_type":    settings["ctype"],
                "batch_size":      settings["batch_size"],
                "glossary":        settings["glossary"],
            })
            store.log("✅ Đã lưu cấu hình thành công.", "ok")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu cấu hình: {e}")

    def get_settings(self) -> Dict[str, Any]:
        """Exposes current values from UI inputs as standard dict settings."""
        lang_display = self.lang_var.get()
        lang_key = next((k for d, k in SUPPORTED_LANGS if d == lang_display), "indonesian")
        ctype_display = self.ctype_var.get()
        ctype_key = next((k for d, k in CONTENT_TYPES if d == ctype_display), "auto")

        return {
            "api_keys":   self._get_keys_from_input(),
            "model":      self.model_var.get().strip(),
            "lang":       lang_key,
            "ctype":      ctype_key,
            "batch_size": self.batch_var.get(),
            "lang_code":  lang_to_code(lang_key),
            "glossary":   self._parse_glossary(),
            "plugin_name": "aibox"  # Default translator plugin ID
        }

    def set_running_state(self, is_running: bool) -> None:
        """Toggles sidebar display mode during running state (shows STOP instead of START)."""
        if is_running:
            self.start_btn.pack_forget()
            self.stop_btn.pack(fill="x", pady=(0, 4))
            self.save_btn.config(state="disabled")
        else:
            self.stop_btn.pack_forget()
            self.start_btn.pack(fill="x", pady=(0, 4))
            self.save_btn.config(state="normal")
