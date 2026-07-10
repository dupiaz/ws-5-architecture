"""
modules/translation/engine.py — Re-expose TranslationEngine từ app/core/interfaces.
Giúp cấu trúc dependencies của domain module sạch sẽ và dễ nhìn.
"""

from app.core.interfaces import TranslationEngine

# Khai báo biến __all__ chỉ rõ những gì được public ra ngoài gói
__all__ = ["TranslationEngine"]
