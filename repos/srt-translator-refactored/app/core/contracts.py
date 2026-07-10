"""
app/core/contracts.py — Định nghĩa các đối tượng dữ liệu mẫu (Data Contracts) lõi của hệ thống.
Các class ở đây đóng vai trò làm cấu trúc dữ liệu chuẩn để truyền nhận giữa các lớp (Layers).
"""

class SrtBlock:
    """
    Lớp đại diện cho một khối phụ đề đơn lẻ trong file SRT.
    Được tối ưu hóa bộ nhớ bằng cơ chế __slots__.
    """
    __slots__ = ("idx", "timestamp", "text")

    def __init__(self, idx: int, timestamp: str, text: str):
        self.idx = idx            # Số thứ tự dòng phụ đề (bắt đầu từ 1)
        self.timestamp = timestamp  # Chuỗi thời gian, định dạng: "00:00:01,000 --> 00:00:03,500"
        self.text = text          # Nội dung văn bản phụ đề (có thể gồm nhiều dòng)

    def __repr__(self):
        return f"SrtBlock(idx={self.idx}, ts={self.timestamp!r})"


class PluginMetadata:
    """
    Lớp chứa thông tin mô tả (Metadata) cho các plugin/bộ chuyển đổi (Adapters).
    Giúp hệ thống quét động và nhận diện thông tin của từng plugin.
    """
    def __init__(self, name: str, version: str, description: str = "", author: str = ""):
        self.name = name                # Tên định danh duy nhất của plugin (ví dụ: 'aibox')
        self.version = version          # Phiên bản plugin (ví dụ: '1.0.0')
        self.description = description  # Mô tả ngắn gọn về tính năng của plugin
        self.author = author            # Tác giả viết plugin này

    def __repr__(self):
        return f"PluginMetadata(name={self.name!r}, version={self.version!r})"
