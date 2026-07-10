"""
app/core/store.py — Quản lý trạng thái tập trung (State Store) và xe buýt sự kiện (Event Bus) an toàn luồng.
Cho phép các luồng xử lý chạy ngầm gửi tín hiệu cập nhật giao diện mà không gây xung đột (Thread Safety).
"""

import threading
from typing import Callable, Dict, List, Any


class EventBus:
    """
    Hệ thống phát và nhận sự kiện (PubSub Pattern) an toàn luồng (Thread-Safe).
    Cho phép liên kết lỏng (Loose Coupling) giữa phần xử lý logic ngầm và Giao diện UI.
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()  # Khóa bảo vệ tránh xung đột luồng khi đăng ký sự kiện

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Đăng ký lắng nghe một loại sự kiện cụ thể."""
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Hủy đăng ký lắng nghe sự kiện."""
        with self._lock:
            if event_type in self._listeners:
                try:
                    self._listeners[event_type].remove(callback)
                except ValueError:
                    pass

    def emit(self, event_type: str, *args, **kwargs) -> None:
        """Phát sự kiện, tự động gọi tất cả hàm callback đã đăng ký lắng nghe."""
        listeners_to_call = []
        with self._lock:
            if event_type in self._listeners:
                # Sao chép danh sách listener để gọi ngoài phạm vi khóa, tránh deadlock
                listeners_to_call = list(self._listeners[event_type])
        
        for callback in listeners_to_call:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                # Fallback print ra console nếu có lỗi trong hàm callback nhận sự kiện
                print(f"Lỗi trong bộ nhận sự kiện của EventBus cho '{event_type}': {e}")


class GlobalStore:
    """
    Kho quản lý trạng thái tập trung của toàn bộ ứng dụng (Single Source of Truth).
    Mọi biến trạng thái như danh sách file, tiến độ chạy đều được lưu ở đây.
    """
    
    def __init__(self):
        # Trạng thái mặc định ban đầu của ứng dụng
        self._state: Dict[str, Any] = {
            "files": [],            # Danh sách file: List[Dict] (path, name, size, checked, status)
            "is_running": False,    # Trạng thái tiến trình dịch có đang chạy hay không
            "progress_pct": 0.0,    # Phần trăm tiến độ tổng thể (0.0 -> 100.0)
            "progress_text": "",    # Chuỗi hiển thị tiến độ (ví dụ: "15/50 blocks (30%)")
            "stop_flag": False,     # Cờ báo hiệu yêu cầu dừng đột ngột từ người dùng
            "config": {},           # Bản sao cấu hình active đang sử dụng
        }
        self._state_lock = threading.Lock()  # Khóa bảo vệ dữ liệu khi nhiều luồng cùng đọc/ghi
        self.event_bus = EventBus()

    def get(self, key: str, default: Any = None) -> Any:
        """Lấy giá trị từ Store một cách an toàn luồng."""
        with self._state_lock:
            return self._state.get(key, default)

    def set(self, key: str, value: Any, emit_change: bool = True) -> None:
        """
        Cập nhật dữ liệu vào Store và tự động phát sự kiện thay đổi.
        
        Args:
            key: Tên biến trạng thái cần ghi.
            value: Giá trị mới cần lưu.
            emit_change: Nếu True, sẽ phát sự kiện 'state_changed:<key>' báo cho UI vẽ lại.
        """
        old_val = None
        changed = False
        with self._state_lock:
            if key in self._state:
                old_val = self._state[key]
                if old_val != value:
                    self._state[key] = value
                    changed = True
            else:
                self._state[key] = value
                changed = True

        # Nếu giá trị thực sự thay đổi, phát tín hiệu cho các thành phần UI cập nhật
        if changed and emit_change:
            # Phát sự kiện đặc thù cho key: ví dụ: 'state_changed:is_running'
            self.event_bus.emit(f"state_changed:{key}", value, old_val)
            # Phát sự kiện thay đổi chung
            self.event_bus.emit("state_changed", key, value, old_val)

    def log(self, message: str, level: str = "default") -> None:
        """Hàm tiện ích gửi dòng nhật ký trực tiếp qua Event Bus."""
        self.event_bus.emit("log", message, level)


# Biến instance duy nhất (Singleton) được sử dụng xuyên suốt toàn ứng dụng
store = GlobalStore()
