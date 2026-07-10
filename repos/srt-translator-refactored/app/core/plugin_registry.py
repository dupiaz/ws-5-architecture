"""
app/core/plugin_registry.py — Bộ quét động và đăng ký các plugin dịch thuật.
Áp dụng Open-Closed Principle (OCP) - dễ dàng mở rộng thêm plugin mà không sửa code lõi.
"""

import os
import sys
import importlib
from typing import Dict, Type, Optional
from app.core.contracts import PluginMetadata
from app.core.interfaces import TranslationEngine

# Xác định vị trí thư mục chứa các plugin nghiệp vụ dịch
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLUGINS_DIR = os.path.join(_ROOT_DIR, "modules", "translation", "plugins")


def _parse_simple_toml(path: str) -> Dict[str, str]:
    """
    Hàm đọc file TOML thô đơn giản không phụ thuộc thư viện ngoài.
    Giúp chương trình tương thích với các phiên bản Python cũ (dưới 3.11).
    """
    metadata = {}
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Bỏ qua dòng trống, comments, và tiêu đề mục [headers]
                    if not line or line.startswith("#") or line.startswith("["):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        metadata[k] = v
    except Exception as e:
        print(f"Lỗi đọc metadata TOML {path}: {e}")
    return metadata


class PluginRegistry:
    """Quản lý quét thư mục, import động các adapter và lưu danh mục plugin hỗ trợ."""
    
    def __init__(self):
        self._plugins: Dict[str, Type[TranslationEngine]] = {}
        self._metadata: Dict[str, PluginMetadata] = {}

    def discover_plugins(self) -> None:
        """Quét thư mục modules/translation/plugins/ để tìm kiếm và nạp các adapter."""
        if not os.path.exists(PLUGINS_DIR):
            return

        # Đảm bảo thư mục gốc dự án được thêm vào sys.path để python nạp được module
        if _ROOT_DIR not in sys.path:
            sys.path.insert(0, _ROOT_DIR)

        for folder_name in os.listdir(PLUGINS_DIR):
            folder_path = os.path.join(PLUGINS_DIR, folder_name)
            if not os.path.isdir(folder_path) or folder_name.startswith("__"):
                continue

            adapter_file = os.path.join(folder_path, "adapter.py")
            toml_file = os.path.join(folder_path, "plugin.toml")

            if not os.path.exists(adapter_file):
                continue

            # Đọc file cấu hình thông tin metadata của plugin
            meta_dict = _parse_simple_toml(toml_file)
            name = meta_dict.get("name", folder_name)
            version = meta_dict.get("version", "1.0.0")
            desc = meta_dict.get("description", "")
            author = meta_dict.get("author", "")

            plugin_metadata = PluginMetadata(name, version, desc, author)

            try:
                # Thực hiện import động: ví dụ nạp module 'modules.translation.plugins.aibox.adapter'
                module_name = f"modules.translation.plugins.{folder_name}.adapter"
                module = importlib.import_module(module_name)

                # Tìm kiếm class kế thừa từ TranslationEngine bên trong module vừa nạp
                registered = False
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type) 
                        and issubclass(attr, TranslationEngine) 
                        and attr is not TranslationEngine
                    ):
                        plugin_id = attr.PLUGIN_NAME if hasattr(attr, "PLUGIN_NAME") else name
                        self._plugins[plugin_id] = attr
                        self._metadata[plugin_id] = plugin_metadata
                        registered = True
                        break  # Chỉ đăng ký một class adapter đại diện trên mỗi folder plugin

                if not registered:
                    print(f"Thư mục plugin '{folder_name}' có file adapter.py nhưng không chứa class hợp lệ kế thừa từ TranslationEngine.")
            except Exception as e:
                print(f"Lỗi nạp plugin từ '{folder_name}': {e}")

    def get_plugin_class(self, plugin_id: str) -> Optional[Type[TranslationEngine]]:
        """Lấy class Adapter của plugin tương ứng để khởi tạo."""
        return self._plugins.get(plugin_id)

    def get_available_plugins(self) -> Dict[str, PluginMetadata]:
        """Trả về danh sách metadata của các plugin đang có sẵn."""
        return self._metadata.copy()


# Đối tượng registry duy nhất trong hệ thống
registry = PluginRegistry()
