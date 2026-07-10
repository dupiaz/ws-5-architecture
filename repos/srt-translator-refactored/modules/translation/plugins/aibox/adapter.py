"""
modules/translation/plugins/aibox/adapter.py — Bộ điều hợp (Adapter) kết nối AI-Box API triển khai giao diện TranslationEngine.
Thực thi gọi API thô và tự kiểm soát lỗi kết nối/vượt ngưỡng tần suất (HTTP 429/503).
"""

import time
import random
import urllib.error
from typing import List, Dict
from app.core.contracts import SrtBlock
from app.core.store import store
from modules.translation.engine import TranslationEngine
from . import api_client

# Số lần thử lại tối đa khi gọi API dịch của một lô (batch) gặp sự cố mạng hoặc vượt quota
BATCH_RETRY_ATTEMPTS = 3


class AIBoxAdapter(TranslationEngine):
    """Adapter hiện thực hóa TranslationEngine kết nối với AI-Box API."""
    
    PLUGIN_NAME = "aibox"

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Key xác thực dùng để gọi API.
        """
        self.api_key = api_key

    @property
    def plugin_name(self) -> str:
        return self.PLUGIN_NAME

    def translate_batch(
        self,
        blocks: List[SrtBlock],
        target_lang: str,
        content_type: str,
        glossary: Dict[str, str],
        model: str
    ) -> Dict[int, str]:
        """
        Triển khai thực thi dịch một lô phụ đề.
        Tích hợp bộ tự thử lại khi gặp lỗi giới hạn tần suất gọi API (HTTP 429/503).
        """
        if not blocks:
            return {}

        system_prompt = api_client.build_system_prompt(target_lang, content_type, glossary)
        user_content = api_client.build_user_content(blocks)
        
        # Nhận diện tên thread đang thực hiện để ghi vào nhật ký gỡ lỗi
        thread_name = threading.current_thread().name if hasattr(threading, "current_thread") else "Worker"

        for attempt in range(1, BATCH_RETRY_ATTEMPTS + 1):
            # Kiểm tra xem người dùng có yêu cầu dừng khẩn cấp giữa chừng không
            if store.get("stop_flag"):
                return {}

            try:
                # 1. Thực hiện gọi API thô
                raw_response = api_client.call_api(
                    api_key=self.api_key,
                    model=model,
                    system_prompt=system_prompt,
                    user_content=user_content
                )
                
                # 2. Phân tích kết quả thô thành dict ánh xạ chỉ mục
                t_map = api_client.parse_response(raw_response)
                if t_map:
                    return t_map
                
                # Nhận phản hồi rỗng hoặc lỗi phân tích
                store.log(f"  [{thread_name}] Phản hồi API trống hoặc lỗi cú pháp (Thử lại {attempt}/{BATCH_RETRY_ATTEMPTS})", "warn")
                
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 503):
                    # Thuật toán giãn cách số mũ (Exponential backoff) kèm độ lệch ngẫu nhiên (jitter) tránh thắt cổ chai
                    wait = (2 ** attempt * 2) + random.uniform(0.5, 2.5)
                    store.log(f"  [{thread_name}] Gặp lỗi giới hạn tần suất HTTP {exc.code}. Đợi {wait:.1f}s để thử lại...", "warn")
                    time.sleep(wait)
                else:
                    store.log(f"  [{thread_name}] Lỗi HTTP {exc.code} không thể phục hồi: {exc.reason}", "error")
                    break
            except Exception as exc:
                store.log(f"  [{thread_name}] Lỗi kết nối mạng: {exc}", "error")
                time.sleep(3)

        return {}


# Import thư viện quản lý thread cục bộ an toàn luồng
import threading
