---
name: ai-desktop-hybrid-refactor
description: Tái cấu trúc ứng dụng Python Desktop AI từ dạng monolithic sang kiến trúc Hybrid (Horizontal Core + Vertical Modules) nhằm phân tách UI, Store, và Plugins.
---

# Tái Cấu Trúc Hybrid Architecture Cho AI Desktop Apps

Kỹ năng này hướng dẫn cách tái cấu trúc một ứng dụng Python Desktop AI (Tkinter / PySide) từ dạng monolithic (giao diện trộn lẫn nghiệp vụ) thành cấu trúc **Hybrid** bền vững, an toàn luồng và dễ mở rộng.

---

## 1. Bản Chất Kiến Trúc Hybrid

```
[ Giao diện UI (app/ui) ] <───► [ Central Store & EventBus (app/core/store) ]
                                                       ▲
                                                       │ (Orchestrates)
                                                       ▼
[ Bộ chạy Pipeline (app/core/pipeline) ] ──► [ Luồng dịch Worker (modules/*/worker.py) ]
                                                       │
                                                       ▼
                                         [ Plugin Adapter (modules/*/plugins/*) ]
```

*   **Horizontal Core (Invariant - Bất biến):** Chứa các hạ tầng dùng chung không đổi theo nghiệp vụ (State Store, EventBus, Config Manager, Plugin Registry, Pipeline Runner).
*   **Horizontal UI (Presentation):** Tách biệt các Frame giao diện. UI không nắm giữ logic nghiệp vụ và chỉ cập nhật thông qua việc lắng nghe sự kiện từ EventBus.
*   **Vertical Domain Modules (Variable - Thay đổi):** Mỗi nghiệp vụ nghiệp vụ (ví dụ: `modules/translation`) được đóng gói đầy đủ và tự chứa (gồm Worker điều phối luồng phụ, Interface quy định giao thức và thư mục Plugins chứa các bộ chuyển đổi Adapter kết nối các API/Model).

---

## 2. Quy Trình Các Bước Tái Cấu Trúc

### Bước 1: Khai báo Data Contracts & Interfaces
1.  Tạo tệp `app/core/contracts.py` để định nghĩa cấu trúc dữ liệu chung để truyền nhận giữa các Layer (ví dụ: `SrtBlock`, `PluginMetadata`).
2.  Tạo tệp `app/core/interfaces.py` để định nghĩa các Abstract Base Class (ABC) như `TranslationEngine(StepEngine)`. Đây là ranh giới kỹ thuật bắt buộc các plugin phải tuân thủ.

### Bước 2: Thiết lập Central Store & EventBus (Thread-Safe)
Tạo tệp `app/core/store.py` để xây dựng kho quản lý trạng thái tập trung (`GlobalStore`) và bộ phát sự kiện (`EventBus`). 
> [!IMPORTANT]
> **Quy tắc an toàn luồng (Thread-Safety):**
> Giao diện đồ họa (Tkinter/PySide) chạy trên Main Thread và không an toàn luồng. Luồng phụ chạy ngầm xử lý AI/API khi muốn cập nhật UI **bắt buộc** phải ghi vào Store hoặc phát Event qua EventBus, sau đó UI lắng nghe và điều phối cuộc gọi về Main Thread thông qua `after(0, callback)` (Tkinter) hoặc `Signals/Slots` (PySide).

### Bước 3: Tạo Động Cơ Quét Plugin động (Plugin Registry)
Tạo tệp `app/core/plugin_registry.py` sử dụng thư viện chuẩn `importlib` để quét thư mục `modules/<domain>/plugins/`, đọc file metadata `plugin.toml` và nạp động các class Adapter kế thừa từ Interface. Điều này cho phép thêm plugin mới bằng cách copy thư mục mà không cần sửa code core.

### Bước 4: Thiết lập Pipeline & Checkpoints (Fault Tolerance)
Tạo tệp `app/core/pipeline.py` để quản lý luồng chạy tuần tự các tệp tin trong một luồng phụ độc lập.
*   **Cơ chế lưu vết (Checkpoint):** Ghi nhận tiến độ hoàn thành của từng khối phụ đề xuống đĩa (ví dụ: `storage/checkpoints/<file_md5_hash>.json`) sau khi hoàn thành mỗi cụm.
*   **Cơ chế phục hồi (Resume):** Khi bắt đầu dịch một file, nạp tệp checkpoint cũ. Bỏ qua các khối đã dịch thành công, giúp phục hồi tiến trình lập tức nếu xảy ra crash hoặc mất mạng.
*   **Xóa vết:** Khi tệp phụ đề hoàn thành trọn vẹn và ghi file output thành công, xóa tệp checkpoint tương ứng.

### Bước 5: Hiện thực hóa Domain Module & Plugins (Vertical Slice)
Tạo cấu trúc thư mục đứng độc lập:
*   `modules/<name>/contracts.py`: Hằng số, regex phát hiện lỗi đặc thù.
*   `modules/<name>/worker.py`: Bộ điều phối luồng phụ cho nghiệp vụ cụ thể. Thực thi cơ chế phân chia song song đa API key và xử lý **Tự phục hồi lỗi (Self-Healing)** tập trung (Immediate retries, Validation kiểm tra bản dịch hỏng, Multi-pass và Fallback Cascade model).
*   `modules/<name>/plugins/<plugin_id>/`:
    *   `plugin.toml`: Định nghĩa thông tin mô tả.
    *   `api_client.py`: Gói HTTP request thô và các parser bóc tách thô (JSON, Regex).
    *   `adapter.py`: Kế thừa `TranslationEngine` kết nối luồng chạy với `api_client`.

### Bước 6: Component hóa UI giao diện
Tách file giao diện monolithic thành các Frame độc lập. Mỗi Frame đăng ký lắng nghe (Subscribe) các sự kiện thay đổi của Store hoặc EventBus (ví dụ: `state_changed:files`) để tự động vẽ lại chính nó khi Store cập nhật.

---

## 3. Mã Nguồn Tham Khảo Chuẩn

### Central Store & EventBus mẫu (`app/core/store.py`):
```python
import threading
from typing import Callable, Dict, List, Any

class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable):
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(callback)

    def emit(self, event_type: str, *args, **kwargs):
        listeners = []
        with self._lock:
            if event_type in self._listeners:
                listeners = list(self._listeners[event_type])
        for cb in listeners:
            cb(*args, **kwargs)

class GlobalStore:
    def __init__(self):
        self._state = {"files": [], "is_running": False}
        self._lock = threading.Lock()
        self.event_bus = EventBus()

    def get(self, key: str) -> Any:
        with self._lock:
            return self._state.get(key)

    def set(self, key: str, value: Any):
        changed = False
        with self._lock:
            if self._state.get(key) != value:
                self._state[key] = value
                changed = True
        if changed:
            self.event_bus.emit(f"state_changed:{key}", value)
            self.event_bus.emit("state_changed", key, value)

store = GlobalStore()
```
