"""
app/core/interfaces.py — Định nghĩa các lớp giao diện trừu tượng (Abstract Base Classes - ABC).
Đóng vai trò làm "hợp đồng kỹ thuật" (Contracts) bắt buộc các plugin cụ thể phải tuân thủ.
Áp dụng nguyên lý nghịch đảo phụ thuộc (Dependency Inversion Principle - DIP).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.core.contracts import SrtBlock


class StepEngine(ABC):
    """
    Interface cơ sở trừu tượng cho mọi công cụ xử lý một bước trong Pipeline.
    Bất kỳ bước nào (ví dụ: ASR, Dịch, TTS) đều phải kế thừa lớp này.
    """
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Trả về tên định danh duy nhất của plugin."""
        pass


class TranslationEngine(StepEngine):
    """
    Interface quy định các hàm bắt buộc một Plugin Dịch Thuật phải hiện thực hóa.
    Giao diện UI và lõi chạy sẽ chỉ giao tiếp qua interface này chứ không gọi trực tiếp plugin cụ thể.
    """
    
    @abstractmethod
    def translate_batch(
        self,
        blocks: List[SrtBlock],
        target_lang: str,
        content_type: str,
        glossary: Dict[str, str],
        model: str
    ) -> Dict[int, str]:
        """
        Thực hiện dịch một lô (batch) các khối phụ đề SrtBlock.
        
        Args:
            blocks: Danh sách các khối phụ đề cần dịch.
            target_lang: Ngôn ngữ đích (ví dụ: 'vietnamese', 'indonesian').
            content_type: Thể loại nội dung (để tối ưu prompt, ví dụ: 'anime', 'film').
            glossary: Bộ từ điển thuật ngữ chuyên ngành dưới dạng {từ_gốc: từ_dịch}.
            model: Tên model AI được yêu cầu thực thi dịch.
            
        Returns:
            Dict[int, str]: Một dict kết quả ánh xạ từ index của khối (idx) sang chuỗi văn bản đã dịch.
        """
        pass
