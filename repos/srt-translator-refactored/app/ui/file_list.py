"""
app/ui/file_list.py — File list treeview, drag-and-drop, and progress bar component.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any, Callable
from app.core.store import store
from app.ui.theme import (
    BG, BG2, BG3, TXT, TXT_DIM, BORDER, ACCENT, SUCCESS, ERR,
    FONT_LABEL, FONT_BTN, rounded_rect
)


class FileListFrame(tk.Frame):
    """File manager UI panel. Displays loaded SRT files, drag-and-drop prompt, and progress."""
    
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        
        self.files: List[Dict[str, Any]] = []
        self._build_ui()
        
        # Subscribe to store changes thread-safely
        store.event_bus.subscribe("state_changed:files", self._on_files_changed_event)
        store.event_bus.subscribe("state_changed:progress_pct", self._on_progress_pct_event)
        store.event_bus.subscribe("state_changed:progress_text", self._on_progress_text_event)
        
        self._sync_with_store()

    def _build_ui(self):
        # ---- HEADER TOOLBAR ----
        header = tk.Frame(self, bg=BG, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="Danh sách file phụ đề (.srt)",
            bg=BG, fg=TXT, font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=10, pady=10)

        btn_row = tk.Frame(header, bg=BG)
        btn_row.pack(side="right", padx=10, pady=8)

        for lbl, cmd in [
            ("＋ Thêm file",     self._browse_files),
            ("📁 Thêm folder",   self._browse_folder),
            ("✓ Chọn tất",       self._select_all),
            ("✗ Bỏ chọn tất",    self._deselect_all),
            ("🗑 Xóa danh sách", self._clear_list),
        ]:
            self._mk_btn(btn_row, lbl, cmd, bg=BG3, fg=TXT_DIM).pack(side="left", padx=2)

        # Thin separator line
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ---- CENTRAL CONTAINER ----
        self.container = tk.Frame(self, bg=BG2)
        self.container.pack(fill="both", expand=True, padx=10, pady=6)

        # Drop Zone (shown when empty)
        self.drop_frame = tk.Frame(self.container, bg=BG2)
        self.canvas = tk.Canvas(self.drop_frame, bg=BG2, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.bind("<Configure>", self._draw_drop_graphics)
        self.canvas.bind("<Button-1>", lambda e: self._browse_files())
        self.drop_frame.pack(fill="both", expand=True)

        # Native drag-and-drop binder using optional TkinterDnD2
        try:
            self.canvas.drop_target_register("DND_Files")
            self.canvas.dnd_bind("<<Drop>>", self._on_dnd_drop)
        except Exception:
            pass

        # Treeview (hidden initially)
        self.tree_frame = tk.Frame(self.container, bg=BG2)
        
        cols = ("check", "name", "size", "status")
        self.tree = ttk.Treeview(
            self.tree_frame, columns=cols, show="headings",
            style="Files.Treeview", selectmode="browse"
        )
        self.tree.heading("check",  text="☑",    anchor="center")
        self.tree.heading("name",   text="Tên file SRT",   anchor="w")
        self.tree.heading("size",   text="Kích thước",     anchor="center")
        self.tree.heading("status", text="Trạng thái",     anchor="center")

        self.tree.column("check",  width=38,  stretch=False, anchor="center")
        self.tree.column("name",   width=420, stretch=True,  anchor="w")
        self.tree.column("size",   width=100, stretch=False, anchor="center")
        self.tree.column("status", width=180, stretch=False, anchor="center")

        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview, style="Dark.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set)
        
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Button-1>", self._on_tree_click)

        # ---- BOTTOM PROGRESS BAR PANEL ----
        self.progress_frame = tk.Frame(self, bg=BG, height=28)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, variable=self.progress_var,
            maximum=100, style="Neon.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill="x", padx=10, pady=2)
        self.progress_lbl = tk.Label(self.progress_frame, text="", bg=BG, fg=TXT_DIM, font=("Segoe UI", 9))
        self.progress_lbl.pack()

    def _draw_drop_graphics(self, event=None):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 20 or h < 20:
            return
        rounded_rect(self.canvas, 12, 12, w-12, h-12, r=16, fill=BG3, outline=BORDER, width=2)
        self.canvas.create_text(w//2, h//2 - 24, text="📂", font=("Segoe UI", 36), fill=TXT_DIM)
        self.canvas.create_text(w//2, h//2 + 20, text="Kéo thả file .srt vào đây", font=("Segoe UI", 12, "bold"), fill=TXT_DIM)
        self.canvas.create_text(w//2, h//2 + 46, text="hoặc nhấn nút  ＋ Thêm file  bên trên", font=("Segoe UI", 9), fill=TXT_DIM)

    def _mk_btn(self, parent, text, command, bg=BG3, fg=TXT):
        return tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground=BORDER, activeforeground=fg,
            font=FONT_BTN, relief="flat", bd=0,
            padx=8, pady=4, cursor="hand2"
        )

    def _sync_with_store(self):
        """Pulls files list from GlobalStore to update local cache and refresh UI."""
        self.files = list(store.get("files"))
        self._refresh_tree_display()

    def _refresh_tree_display(self):
        if not self.files:
            self.tree_frame.pack_forget()
            self.progress_frame.pack_forget()
            self.drop_frame.pack(fill="both", expand=True)
            return

        self.drop_frame.pack_forget()
        self.tree_frame.pack(fill="both", expand=True)
        self.progress_frame.pack(fill="x")

        # Clear tree
        self.tree.delete(*self.tree.get_children())
        
        for i, f in enumerate(self.files):
            chk = "☑" if f.get("checked", True) else "☐"
            status = f.get("status", "Chờ dịch")
            tag = self._status_tag(status)
            self.tree.insert(
                "", "end",
                values=(chk, f["name"], f["size"], status),
                tags=(tag, f"row_{i}")
            )

        self.tree.tag_configure("done",    foreground=SUCCESS)
        self.tree.tag_configure("running", foreground=ACCENT)
        self.tree.tag_configure("error",   foreground=ERR)
        self.tree.tag_configure("skip",    foreground=TXT_DIM)
        self.tree.tag_configure("pending", foreground=TXT)

    def _status_tag(self, status: str) -> str:
        s = status.lower()
        if "hoàn thành" in s or "done" in s: return "done"
        if "đang dịch"  in s or "dịch..."  in s: return "running"
        if "lỗi"        in s or "error"    in s: return "error"
        if "bỏ qua"     in s or "skip"     in s: return "skip"
        return "pending"

    # ---- DND & CLICKS INTERACTION ----
    def _on_tree_click(self, event):
        col = self.tree.identify_column(event.x)
        iid = self.tree.identify_row(event.y)
        if not iid or col != "#1":
            return
        idx = self.tree.index(iid)
        if idx < len(self.files):
            self.files[idx]["checked"] = not self.files[idx]["checked"]
            store.set("files", self.files)  # Save back to store, triggers rewrite

    def _on_dnd_drop(self, event):
        paths = self.tk.splitlist(event.data)
        self._add_paths(paths)

    def _add_paths(self, paths: list):
        expanded = []
        for p in paths:
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        if f.lower().endswith(".srt"):
                            expanded.append(os.path.join(root, f))
            elif p.lower().endswith(".srt"):
                expanded.append(p)

        existing = {f["path"] for f in self.files}
        added = 0
        
        for p in expanded:
            if p not in existing:
                name = os.path.basename(p)
                size = os.path.getsize(p)
                size_str = f"{size/1024:.1f} KB"
                self.files.append({
                    "path": p, "name": name, "size": size_str,
                    "checked": True, "status": "Chờ dịch"
                })
                added += 1

        if added > 0:
            store.set("files", self.files)
            store.log(f"Đã thêm {added} file(s) phụ đề.", "ok")

    def _browse_files(self):
        paths = filedialog.askopenfilenames(
            title="Chọn file SRT",
            filetypes=[("SRT Subtitles", "*.srt"), ("All files", "*.*")]
        )
        if paths:
            self._add_paths(list(paths))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa file SRT")
        if folder:
            paths = []
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(".srt"):
                        paths.append(os.path.join(root, f))
            self._add_paths(paths)

    def _select_all(self):
        for f in self.files:
            f["checked"] = True
        store.set("files", self.files)

    def _deselect_all(self):
        for f in self.files:
            f["checked"] = False
        store.set("files", self.files)

    def _clear_list(self):
        if store.get("is_running"):
            messagebox.showwarning("Cảnh báo", "Dừng tiến trình trước khi xóa danh sách.")
            return
        self.files.clear()
        store.set("files", self.files)
        self.progress_var.set(0.0)
        self.progress_lbl.config(text="")

    # ---- STORE EVENT SUBSCRIPTIONS (routed thread-safely via self.after) ----
    def _on_files_changed_event(self, files_list: List[Dict[str, Any]], old_val=None):
        self.after(0, lambda: self._actual_files_changed(files_list))

    def _actual_files_changed(self, files_list: List[Dict[str, Any]]):
        self.files = list(files_list)
        self._refresh_tree_display()

    def _on_progress_pct_event(self, pct: float, old_val=None):
        self.after(0, lambda: self.progress_var.set(pct))

    def _on_progress_text_event(self, text: str, old_val=None):
        self.after(0, lambda: self.progress_lbl.config(text=text))
