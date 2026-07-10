"""
app/main.py — Điểm khởi chạy chính của ứng dụng dịch phụ đề SRT-Translator.
Quản lý khóa chạy duy nhất (Single Instance Lock) và nạp cấu hình hệ thống.
"""

import sys
import os
import socket

# ---------------------------------------------------------------------------
# Cơ chế Khóa Thực Thể Duy Nhất (Single Instance Lock)
# Ngăn chặn người dùng mở nhiều cửa sổ ứng dụng cùng lúc gây tranh chấp cổng/config
# ---------------------------------------------------------------------------
try:
    # Sử dụng cổng 54321 làm cổng bind duy nhất trên localhost của app này
    _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _lock_socket.bind(('127.0.0.1', 54321))
except socket.error:
    # Nếu cổng đã bị chiếm (tức là app đã chạy trước đó), thoát im lặng ngay lập tức
    sys.exit(0)

# Đảm bảo đường dẫn gốc của dự án luôn nằm trong sys.path để python nạp được module
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from app.core.config_manager import load_config
from app.ui.main_window import MainWindow


def main():
    # 1. Nạp cấu hình từ file config.json vào GlobalStore
    load_config()

    # 2. Khởi tạo và chạy giao diện chính Tkinter mainloop
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
