"""
app/utils/srt_io.py — Bộ công cụ xử lý đọc/ghi và sửa lỗi định dạng tệp tin phụ đề SRT.
Hỗ trợ tự phát hiện bảng mã (Encoding) của file phụ đề (UTF-8 BOM, UTF-8, GBK/GB2312, CP1252).
"""

import re
import os
from app.core.contracts import SrtBlock

# Regex phát hiện lỗi định dạng timestamp (sử dụng dấu '.' thay vì dấu ',' ngăn cách phần nghìn giây)
_TS_DOT_RE = re.compile(r"(\d{2}:\d{2}:\d{2})\.(\d{3})")
# Regex kiểm tra tính hợp lệ của dòng chứa mốc thời gian: "00:00:01,000 --> 00:00:03,500"
_TS_LINE_RE = re.compile(r"\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}")

# Bản đồ ánh xạ ngôn ngữ đích -> mã viết tắt quốc gia (để tạo tên thư mục lưu kết quả)
LANG_CODE_MAP = {
    "indonesian":  "ID",
    "thai":        "TH",
    "vietnamese":  "VI",
    "hindi":       "HI",
    "korean":      "KO",
    "spanish":     "ES",
    "french":      "FR",
    "german":      "DE",
    "portuguese":  "PT_BR",
    "english":     "EN",
    "turkish":     "TR",
    "filipino":    "PH",
    "russian":     "RU",
    "japanese":    "JA",
    "chinese":     "ZH",
    "arabic":      "AR",
}


def _detect_encoding(data: bytes) -> str:
    """Tự động kiểm tra bảng mã (encoding) của dữ liệu nhị phân đầu vào."""
    if data[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"  # UTF-8 có ký hiệu BOM ở đầu
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        import codecs
        codecs.lookup("gbk")
        data.decode("gbk")
        return "gbk"  # Bảng mã tiếng Trung giản thể
    except (LookupError, UnicodeDecodeError):
        pass
    return "cp1252"  # Bảng mã ANSI mặc định của Windows Châu Âu


def _repair(text: str) -> str:
    """Sửa chữa các lỗi nhỏ thường gặp trong file phụ đề SRT của người dùng."""
    # 1. Thay thế dấu . thành dấu , trong timestamp để khớp đặc tả chuẩn SRT
    text = _TS_DOT_RE.sub(r"\1,\2", text)
    # 2. Loại bỏ các ký tự vô hình gây lỗi render (zero-width space và soft hyphen)
    text = text.replace("\u200b", "").replace("\u00ad", "")
    return text


def read_srt(filepath: str) -> list[SrtBlock]:
    """
    Đọc tệp SRT từ đĩa, tự động giải mã và phân tích cú pháp thành danh sách đối tượng SrtBlock.
    """
    with open(filepath, "rb") as fh:
        raw = fh.read()

    enc = _detect_encoding(raw)
    text = raw.decode(enc, errors="replace")

    # Chuẩn hóa ký tự xuống dòng chéo trên nhiều nền tảng (Windows/Unix/Mac)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.lstrip("\ufeff")
    text = _repair(text)

    blocks = []
    # Tách file srt thành các khối bằng cách cắt theo cụm có >= 2 dấu xuống dòng liên tiếp
    for chunk in re.split(r"\n{2,}", text.strip()):
        lines = chunk.strip().split("\n")
        if len(lines) < 2:
            continue
        idx_line = lines[0].strip()
        # Xác minh định dạng dòng 1 phải là số nguyên (index)
        if not re.match(r"^\d+$", idx_line):
            continue
        # Xác minh định dạng dòng 2 phải chứa cụm timestamp chỉ hướng
        if not _TS_LINE_RE.search(lines[1]):
            continue
        body = "\n".join(lines[2:]).strip() if len(lines) > 2 else ""
        blocks.append(SrtBlock(int(idx_line), lines[1].strip(), body))

    return blocks


def write_srt(blocks: list[SrtBlock], filepath: str) -> None:
    """
    Ghi danh sách SrtBlock xuống file phụ đề.
    Ghi dưới định dạng UTF-8 BOM (utf-8-sig) để đảm bảo không bị lỗi font khi mở trên Windows.
    """
    dir_path = os.path.dirname(filepath)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    parts = []
    for b in blocks:
        parts.append(str(b.idx))
        parts.append(b.timestamp)
        parts.append(b.text or "")
        parts.append("")  # Dòng trống phân tách giữa các block phụ đề
    content = "\n".join(parts)

    with open(filepath, "w", encoding="utf-8-sig", newline="\n") as fh:
        fh.write(content)


def get_output_path(source_path: str, lang_code: str) -> str:
    """
    Tính toán và trả về đường dẫn file kết quả dịch.
    Định dạng đường dẫn: <thư_mục_chứa_file>/output dịch/<MÃ_NGÔN_NGỮ>/<tên_file_gốc>
    """
    src_dir = os.path.dirname(os.path.abspath(source_path))
    filename = os.path.basename(source_path)
    return os.path.join(src_dir, "output dịch", lang_code, filename)


def lang_to_code(lang: str) -> str:
    """Ánh xạ tên hiển thị ngôn ngữ tiếng Anh sang mã viết tắt quốc gia (VD: 'Vietnamese' -> 'VI')."""
    return LANG_CODE_MAP.get(lang.lower(), lang.upper()[:2])
