"""
app/ui/main_window.py — Main Window container assembling UI components and binding actions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import os
import sys
from typing import Dict, Any, List
from app.core.store import store
from app.core.pipeline import PipelineOrchestrator
from modules.translation.worker import TranslationWorker
from app.core.updater import AutoUpdater
from app.ui.sidebar import SidebarFrame
from app.ui.file_list import FileListFrame
from app.ui.log_panel import LogPanelFrame
from app.ui.theme import (
    BG, BG2, BG3, TXT, TXT_DIM, BORDER, ACCENT,
    FONT_LABEL, FONT_MAIN
)

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MainWindow(tk.Tk):
    """Main application window composing all view panels and controlling pipeline starts."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Matrix Tool SRT-Translator V2")
        self.geometry("1160x720")
        self.minsize(900, 600)
        self.configure(bg=BG)
        
        self._set_taskbar_icon()
        self._apply_ttk_theme()
        
        # Instantiate pipeline orchestrator
        # Factory links files running to our translation domain worker
        def worker_factory(filepath, settings, checkpoint_map):
            return TranslationWorker(filepath, settings, checkpoint_map)
            
        self.orchestrator = PipelineOrchestrator(worker_factory)
        
        self._build_ui()
        
        # Listen to state runs and updater notifications
        store.event_bus.subscribe("state_changed:is_running", self._on_running_state_changed_event)
        store.event_bus.subscribe("update_available", self._on_update_available_event)
        store.event_bus.subscribe("app_restart_requested", self._on_restart_requested_event)

        # Launch auto-updater check
        self.updater = AutoUpdater()
        self.updater.check_for_updates_async()

    def _set_taskbar_icon(self):
        """Fixes Windows taskbar icon stack and loads window icon file."""
        try:
            # Register AppUserModelID for correct Windows taskbar aggregation
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("matrix.srt_translator.v2")
        except Exception:
            pass

        try:
            ico = os.path.join(_ROOT_DIR, "assets", "icon.ico")
            if os.path.exists(ico):
                self.iconbitmap(ico)
        except Exception:
            pass

    def _apply_ttk_theme(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".",
            background=BG, foreground=TXT,
            fieldbackground=BG3, bordercolor=BORDER,
            lightcolor=BORDER, darkcolor=BORDER,
            troughcolor=BG2, insertcolor=TXT,
            selectbackground=BG3, selectforeground=ACCENT,
        )

        # Treeview
        style.configure("Files.Treeview",
            background=BG2, foreground=TXT,
            fieldbackground=BG2, rowheight=30,
            font=("Segoe UI", 10),
        )
        style.configure("Files.Treeview.Heading",
            background=BG3, foreground=TXT_DIM,
            font=("Segoe UI", 9, "bold"), relief="flat",
        )
        style.map("Files.Treeview",
            background=[("selected", BG3)],
            foreground=[("selected", ACCENT)],
        )

        # Scrollbars
        style.configure("Dark.Vertical.TScrollbar",
            background=BG3, troughcolor=BG,
            arrowcolor=TXT_DIM, bordercolor=BG,
            relief="flat", width=8,
        )
        style.map("Dark.Vertical.TScrollbar",
            background=[("active", BORDER)],
        )

        # Progressbar
        style.configure("Neon.Horizontal.TProgressbar",
            background=ACCENT, troughcolor=BG3,
            bordercolor=BG3, lightcolor=ACCENT, darkcolor=ACCENT,
        )

        # Combobox
        style.configure("Dark.TCombobox",
            fieldbackground=BG3, background=BG3,
            foreground=TXT, arrowcolor=TXT_DIM,
            bordercolor=BORDER, relief="flat",
        )
        style.map("Dark.TCombobox",
            fieldbackground=[("readonly", BG3)],
            foreground=[("readonly", TXT)],
        )

    def _build_ui(self):
        root_frame = tk.Frame(self, bg=BG)
        root_frame.pack(fill="both", expand=True)

        # Left Config Sidebar
        self.sidebar = SidebarFrame(
            root_frame,
            on_start=self._start_translation,
            on_stop=self._stop_translation
        )
        self.sidebar.pack(side="left", fill="y")

        # Right Main Panel
        main_panel = tk.Frame(root_frame, bg=BG)
        main_panel.pack(side="left", fill="both", expand=True)

        # Paned Window (Split list top and logs bottom)
        paned = tk.PanedWindow(
            main_panel, orient="vertical", bg=BG,
            sashwidth=5, sashrelief="flat",
            sashcursor="sb_v_double_arrow",
        )
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # File List panel
        self.file_list = FileListFrame(paned)
        paned.add(self.file_list, stretch="always", minsize=180)

        # Log Panel
        self.log_panel = LogPanelFrame(paned)
        paned.add(self.log_panel, stretch="always", minsize=120)

        # Resize weights
        paned.paneconfig(self.file_list, height=360)
        paned.paneconfig(self.log_panel,  height=200)

        # Resizable root grids
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    # ---- BUTTON COMMAND HANDLERS ----
    def _start_translation(self):
        settings = self.sidebar.get_settings()
        
        # Validations
        if not settings["api_keys"]:
            messagebox.showerror(
                "Thiếu API Key",
                "Vui lòng nhập ít nhất 1 API Key trong cài đặt Sidebar.\n"
                "Lấy key tại: https://api.ai-box.vn/console/token"
            )
            return

        files = store.get("files")
        selected = [(i, f) for i, f in enumerate(files) if f.get("checked", True)]
        if not selected:
            messagebox.showinfo("Thông báo", "Vui lòng thêm và chọn ít nhất 1 file phụ đề để dịch.")
            return

        # Prepare UI and log starts
        self.log_panel.clear_log()
        store.log(f"▶ Bắt đầu chạy dịch {len(selected)} file phụ đề...", "info")
        store.log(f"   Model: {settings['model']} | Workers song song: {len(settings['api_keys'])} | Batch size: {settings['batch_size']}", "dim")
        
        # Reset files status
        updated_files = list(files)
        for i, f in selected:
            updated_files[i] = dict(updated_files[i], status="⏳ Đang chờ...")
        store.set("files", updated_files)

        # Trigger orchestrator
        self.orchestrator.start(selected, settings)

    def _stop_translation(self):
        if not store.get("is_running"):
            return
        if messagebox.askyesno("Xác nhận dừng", "Bạn có chắc chắn muốn dừng tiến trình dịch đang chạy?"):
            store.set("stop_flag", True)
            store.log("⏹ Đang gửi yêu cầu dừng tới các workers...", "warn")

    # ---- STORE EVENT SUBSCRIPTIONS (routed thread-safely via self.after) ----
    def _on_running_state_changed_event(self, is_running: bool, old_val=None):
        self.after(0, lambda: self._actual_running_state_changed(is_running))

    def _actual_running_state_changed(self, is_running: bool):
        self.sidebar.set_running_state(is_running)
        if not is_running and not store.get("stop_flag"):
            # Flash window title when translation finished successfully
            self.title("✅ Dịch hoàn thành! — Matrix Tool SRT-Translator V2")
            self.after(4000, lambda: self.title("Matrix Tool SRT-Translator V2"))

    def _on_update_available_event(self, latest_version: str, download_url: str, changelog: str):
        self.after(0, lambda: self._prompt_update_popup(latest_version, download_url, changelog))

    def _prompt_update_popup(self, latest_ver: str, download_url: str, changelog: str):
        msg = f"Đã có phiên bản mới v{latest_ver}!\n\nNội dung cập nhật:\n{changelog}\n\nBạn có muốn tự động cập nhật ngay không?"
        if messagebox.askyesno("Cập nhật phần mềm", msg):
            self.updater.start_download_async(download_url)

    def _on_restart_requested_event(self):
        self.after(0, self.destroy)
