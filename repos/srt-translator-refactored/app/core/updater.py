"""
app/core/updater.py — Hệ thống kiểm tra phiên bản và tự động cập nhật phần mềm.
Được tách biệt hoàn toàn khỏi giao diện đồ họa. Sử dụng Event Bus để thông báo cho UI.
"""

import os
import sys
import json
import re
import urllib.request
import shutil
import subprocess
import threading
from typing import Dict, Any, Optional
from app.core.store import store

APP_VERSION = "1.0.0"
VERSION_URL = "https://raw.githubusercontent.com/duc1408/SRT-Translator/main/version.json"


class AutoUpdater:
    """Quản lý các tiến trình kiểm tra phiên bản, tải bản cập nhật và cài đặt tự động."""
    
    def __init__(self):
        self._is_checking = False
        self._is_downloading = False

    def check_for_updates_async(self) -> None:
        """Kiểm tra bản cập nhật trong một luồng chạy ngầm để tránh block UI."""
        # Chỉ tự động cập nhật khi ứng dụng đang chạy dưới dạng file thực thi (.exe) đã build
        if not getattr(sys, 'frozen', False):
            return
            
        if self._is_checking:
            return
            
        threading.Thread(target=self._check_for_updates, daemon=True).start()

    def _check_for_updates(self) -> None:
        self._is_checking = True
        try:
            req = urllib.request.Request(VERSION_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                
            latest_version = data.get("version", "1.0.0")
            download_url = data.get("url")
            changelog = data.get("changelog", "")

            # Hàm nhỏ phân tích chuỗi version "1.0.0" -> [1, 0, 0] để so sánh số học
            def parse_ver(v):
                return [int(x) for x in re.sub(r'[^\d.]', '', v).split('.')]

            if parse_ver(latest_version) > parse_ver(APP_VERSION):
                # Phát hiện bản cập nhật mới! Phát sự kiện báo cho UI biết để hiện hộp thoại hỏi người dùng
                store.event_bus.emit(
                    "update_available",
                    latest_version=latest_version,
                    download_url=download_url,
                    changelog=changelog
                )
        except Exception as e:
            # Bỏ qua lỗi cập nhật nếu mất mạng nhưng vẫn in ra console để gỡ lỗi
            print(f"Lỗi kiểm tra phiên bản mới: {e}")
        finally:
            self._is_checking = False

    def start_download_async(self, download_url: str) -> None:
        """Tải bản cập nhật ngầm."""
        if self._is_downloading:
            return
        threading.Thread(target=self._download_update, args=(download_url,), daemon=True).start()

    def _download_update(self, download_url: str) -> None:
        self._is_downloading = True
        store.log("Đang tải bản cập nhật mới...", "warn")
        
        exe_dir = os.path.dirname(sys.executable)
        new_exe_path = os.path.join(exe_dir, "SRT-Translator_new.exe")
        old_exe_path = os.path.join(exe_dir, "SRT-Translator.exe")
        bat_path = os.path.join(exe_dir, "update.bat")

        try:
            # 1. Tải file build .exe mới
            req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as response, open(new_exe_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

            # 2. Tạo kịch bản script batch `.bat` tự động thay thế file .exe cũ
            # (Vì Windows không cho phép xóa file .exe đang chạy, ta cần tắt app rồi chạy batch để đè file)
            bat_content = f"""@echo off
timeout /t 1 /nobreak >nul
del /f /q "{old_exe_path}"
rename "{new_exe_path}" "SRT-Translator.exe"
start "" "SRT-Translator.exe"
del "%~f0"
"""
            with open(bat_path, "w", encoding="ascii") as f:
                f.write(bat_content)

            store.log("Tải hoàn tất! Đang khởi động lại ứng dụng để cập nhật...", "ok")
            store.event_bus.emit("update_ready", bat_path=bat_path)
            
            # 3. Khởi chạy file update.bat dưới dạng tiến trình độc lập (detached process)
            subprocess.Popen(
                ["cmd.exe", "/c", bat_path],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            # Yêu cầu cửa sổ chính đóng tiến trình Python hiện tại
            store.event_bus.emit("app_restart_requested")
            
        except Exception as e:
            store.log(f"Lỗi tải bản cập nhật: {e}", "error")
            store.event_bus.emit("update_failed", error=str(e))
        finally:
            self._is_downloading = False
