"""
modules/translation/contracts.py — Định nghĩa các hằng số, regex và cấu trúc dữ liệu miền dịch thuật.
"""

import re
from typing import Dict, Any, List

# Regex dùng để bỏ qua không gọi dịch thuật các dòng phụ đề chỉ chứa ký hiệu nhạc, ngoặc vuông hoặc dấu ba chấm.
SKIP_RE = re.compile(
    r"^\s*([\u266a\u266b]+|\[Music\]|\[Applause\]|\(Music\)|\[.*?\]|\(.*?\)|\.\.\.|-{2,}|\u2013{2,})\s*$",
    re.IGNORECASE,
)

# Các mẫu regex phát hiện bảng chữ cái gốc của ngôn ngữ nguồn (dùng để nhận biết block chưa được dịch)
CHINESE_RE  = re.compile(r"[\u4e00-\u9fff]")     # Chữ Hán
JAPANESE_RE = re.compile(r"[\u3040-\u30ff]")     # Chữ Hiragana + Katakana
KOREAN_RE   = re.compile(r"[\uac00-\ud7af]")     # Chữ Hangul Hàn Quốc
ARABIC_RE   = re.compile(r"[\u0600-\u06ff]")     # Chữ Ả Rập
THAI_RE     = re.compile(r"[\u0e00-\u0e7f]")     # Chữ Thái
CYRILLIC_RE = re.compile(r"[\u0400-\u04ff]")     # Chữ Kirin (Nga)

# Bản đồ liên kết định danh ngôn ngữ -> Regex kiểm tra bảng chữ
SCRIPT_DETECTORS = {
    "chinese":   CHINESE_RE,
    "japanese":  JAPANESE_RE,
    "korean":    KOREAN_RE,
    "arabic":    ARABIC_RE,
    "thai":      THAI_RE,
    "russian":   CYRILLIC_RE,
}

# Tên chuẩn hiển thị của các ngôn ngữ
LANG_NAMES = {
    "indonesian":  "Indonesian",
    "thai":        "Thai",
    "vietnamese":  "Vietnamese",
    "hindi":       "Hindi",
    "korean":      "Korean",
    "spanish":     "Spanish (Latin America)",
    "french":      "French",
    "german":      "German",
    "portuguese":  "Portuguese (Brazil)",
    "english":     "English",
    "turkish":     "Turkish",
    "filipino":    "Filipino/Tagalog",
    "russian":     "Russian",
    "japanese":    "Japanese",
    "chinese":     "Chinese (Simplified)",
    "arabic":      "Arabic",
}

# Thể loại nội dung phục vụ cấu hình tinh chỉnh register văn phong
CONTENT_LABELS = {
    "auto":         "general",
    "film":         "drama/film",
    "anime":        "anime",
    "wuxia":        "wuxia/martial arts",
    "news":         "news",
    "documentary":  "documentary",
}


class TranslationResult:
    """Lớp chứa thông tin đóng gói kết quả dịch thuật của một file srt hoàn chỉnh."""
    def __init__(self, target_lang: str, translated_text_map: Dict[int, str]):
        self.target_lang = target_lang
        self.translated_text_map = translated_text_map  # dict ánh xạ idx -> chuỗi văn bản dịch

    def __repr__(self):
        return f"TranslationResult(lang={self.target_lang!r}, blocks={len(self.translated_text_map)})"
