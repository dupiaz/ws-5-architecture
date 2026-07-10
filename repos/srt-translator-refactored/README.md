# SRT Subtitle Translator (Hybrid Architecture)

Phiên bản tái cấu trúc hoàn chỉnh của **SRT-Translator** áp dụng kiến trúc **Hybrid (Horizontal Core + Vertical Modules)**. Kiến trúc này tách biệt rõ ràng giữa giao diện, cấu hình lõi của ứng dụng và logic nghiệp vụ dịch thuật để dễ đọc, dễ kiểm thử và dễ mở rộng.

---

## 🛠️ Công Nghệ & Rationale

*   **Không phụ thuộc thư viện ngoài (Zero-dependency):** Duy trì triết lý gọn nhẹ của app gốc, sử dụng 100% Python Standard Library (không cần chạy `pip install` để sử dụng các tính năng cơ bản).
*   **Tkinter OOP Componentization:** Thay vì file giao diện monolithic, các thành phần UI (Sidebar, File List, Logs) được tách thành các lớp kế thừa `tk.Frame` riêng biệt, tăng tính đóng gói.
*   **Thread-safe State Store & Event Bus (PubSub):** Trạng thái ứng dụng được quản lý tập trung trong `GlobalStore`. Mọi thông tin truyền tin giữa Tiến trình dịch (Thread phụ) và Giao diện (Main Thread) đều đi qua `EventBus` và được đồng bộ hóa luồng an toàn qua `after()` của Tkinter.
*   **Cơ chế lưu vết và tự phục hồi (JSON Checkpoints):** Tiến độ dịch của từng file phụ đề được lưu liên tục vào `storage/checkpoints/` dưới dạng JSON hash. Nếu xảy ra sự cố đột ngột (mất mạng, crash), ứng dụng sẽ tự phục hồi tiến trình cũ ở lần khởi chạy sau.

---

## 📂 Cấu Trúc Dự Án

```
srt-translator-refactored/
├── run.bat                            ← Khởi chạy nhanh ứng dụng trên Windows
├── app/                               ← 🔵 CORE FRAMEWORK (Horizontal - Invariant)
│   ├── main.py                        ← Entry point khởi động ứng dụng
│   ├── core/                          ← Logic lõi hệ thống
│   │   ├── contracts.py               ← Khai báo SrtBlock, PluginMetadata...
│   │   ├── interfaces.py             ← Quy định lớp cơ sở StepEngine, TranslationEngine
│   │   ├── store.py                  ← State Store tập trung + Event Bus
│   │   ├── pipeline.py               ← Bộ chạy pipeline tuần tự và quản lý checkpoint
│   │   ├── plugin_registry.py        ← Quét và nạp động các adapter plugins
│   │   ├── config_manager.py         ← Quản lý lưu/nạp cấu hình config.json
│   │   └── updater.py                ← Bộ kiểm tra phiên bản mới từ GitHub
│   ├── ui/                            ← Presentation Layer (Tkinter views)
│   │   ├── main_window.py
│   │   ├── sidebar.py
│   │   ├── file_list.py
│   │   └── log_panel.py
│   └── utils/                         ← Tiện ích hỗ trợ đọc/ghi/sửa lỗi file SRT
│       └── srt_io.py
│
├── modules/                           ← 📦 DOMAIN MODULES (Vertical Slice)
│   └── translation/                   ← Module dịch thuật
│       ├── engine.py                  ← Định nghĩa cụ thể TranslationEngine interface
│       ├── contracts.py              ← Hợp đồng dữ liệu dịch
│       ├── worker.py                 ← Worker chạy dịch đa luồng song song & self-healing
│       └── plugins/                   ← Thư mục chứa các plugin adapter cụ thể
│           └── aibox/                 ← Plugin mặc định kết nối AI-Box API
│
└── tests/                             ← ✅ Bộ kiểm thử tự động (Unit/Integration tests)
```

---

## 🔌 Hướng Dẫn Viết Thêm Plugin Dịch Mới

Để thêm một API dịch thuật mới (ví dụ: Google Translate, OpenAI, Gemini hoặc NLLB Offline), bạn chỉ cần làm theo các bước sau mà **không cần chỉnh sửa bất kỳ phần code core nào** của ứng dụng:

### Bước 1: Tạo thư mục plugin
Tạo một thư mục mới trong `modules/translation/plugins/` (ví dụ: `modules/translation/plugins/my_translator/`).

### Bước 2: Tạo tệp `plugin.toml`
Tạo file metadata giới thiệu thông tin plugin:
```toml
name = "my_translator"
version = "1.0.0"
description = "Plugin dịch thuật của tôi"
author = "Developer"
```

### Bước 3: Tạo tệp `adapter.py`
Tạo file triển khai interface `TranslationEngine`. Lớp adapter này bắt buộc phải có thuộc tính `PLUGIN_NAME` trùng khớp với tên thư mục:

```python
from typing import List, Dict
from app.core.contracts import SrtBlock
from modules.translation.engine import TranslationEngine

class MyTranslatorAdapter(TranslationEngine):
    PLUGIN_NAME = "my_translator"

    def __init__(self, api_key: str):
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
        # 1. Gọi API dịch thuật của bạn tại đây...
        # 2. Trả về dict map dạng {block_index: "nội dung đã dịch"}
        result = {}
        for b in blocks:
            result[b.idx] = f"[Dịch] {b.text}"
        return result
```

Hệ thống sẽ tự động quét, đăng ký và sử dụng adapter mới này dựa trên trường `"plugin_name"` được gửi từ cài đặt.

---

## ✅ Kiểm Thử Tự Động (Tests)

Bộ kiểm thử được viết bằng module `unittest` có sẵn của Python. Chạy tất cả kiểm thử:
```bash
python -m unittest discover -s tests
```
