"""
app/core/config_manager.py — Quản lý đọc/ghi và đồng bộ hóa tệp cấu hình config.json.
"""

import os
import sys
import json
from typing import Dict, Any
from app.core.store import store

# Xác định vị trí tệp cấu hình tùy thuộc vào việc chạy bằng file script Python thô hay file .exe đã build
IS_FROZEN = getattr(sys, 'frozen', False)
if IS_FROZEN:
    # Nếu chạy bằng file .exe, config.json nằm cùng thư mục chứa file .exe
    _CONFIG_DIR = os.path.dirname(sys.executable)
else:
    # Nếu chạy bằng code script, config.json nằm ở thư mục gốc của dự án
    _CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.json")


def get_default_config() -> Dict[str, Any]:
    """Trả về cấu hình mặc định ban đầu của ứng dụng."""
    return {
        "api_keys": [],
        "model": "deepseek-v4-flash",
        "target_language": "indonesian",
        "content_type": "auto",
        "batch_size": 45,
        "glossary": {}
    }


def load_config() -> Dict[str, Any]:
    """
    Đọc cấu hình từ config.json. Nếu không tìm thấy, trả về cấu hình mặc định.
    Sau khi nạp xong sẽ ghi đè lên biến 'config' trong GlobalStore để UI đồng bộ.
    """
    config = get_default_config()
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Cập nhật đè dữ liệu đọc được vào khung mặc định để tránh thiếu key
            config.update(data)
    except Exception as e:
        print(f"Lỗi nạp cấu hình từ {CONFIG_PATH}: {e}")
        
    # Lưu vào Store tập trung
    store.set("config", config, emit_change=True)
    return config


def save_config(config_data: Dict[str, Any]) -> None:
    """
    Ghi cấu hình mới xuống tệp config.json và cập nhật lại Store.
    """
    current_config = get_default_config()
    current_config.update(config_data)
    
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(current_config, fh, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Lỗi ghi cấu hình xuống {CONFIG_PATH}: {e}")
        raise e
        
    # Cập nhật lại Store tập trung
    store.set("config", current_config, emit_change=True)
