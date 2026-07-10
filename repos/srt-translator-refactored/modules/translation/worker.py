"""
modules/translation/worker.py — Tiến trình dịch thuật và khôi phục lỗi (Self-Healing) song song đa luồng.
Chứa các thuật toán tự phục hồi lỗi 4 lớp (Immediate Retry, Validation, Multi-Pass, Fallback Cascade).
Được triển khai tập trung tại đây để tất cả các plugin (adapters) đều được hưởng lợi mà không cần viết lại.
"""

import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Type
from app.core.contracts import SrtBlock
from app.core.store import store
from app.core.plugin_registry import registry
from modules.translation.contracts import (
    SKIP_RE, SCRIPT_DETECTORS, CHINESE_RE,
    LANG_NAMES, CONTENT_LABELS
)

# Các hằng số điều khiển thuật toán tự phục hồi và dịch dự phòng
MAX_HEAL_ROUNDS = 2           # Số vòng quét và dịch bù tối đa với model chính
HEAL_BATCH_SIZE = 40          # Batch size tối ưu khi chạy dịch bù (tiết kiệm token hệ thống)
HEAL_RETRY_ATTEMPTS = 3       # Số lần thử lại tối đa cho mỗi cụm dịch bù lỗi
DEFAULT_FALLBACK_MODELS = ["deepseek-v4-flash"]  # Danh sách các mô hình dự phòng chạy cascade


def _detect_source_scripts(blocks: List[SrtBlock]) -> List[Any]:
    """Quét ngẫu nhiên 50 dòng phụ đề đầu tiên để phát hiện chữ cái ngôn ngữ nguồn."""
    sample_text = " ".join(
        b.text for b in blocks[:50] if b.text and not SKIP_RE.match(b.text)
    )
    detected = []
    for _name, pattern in SCRIPT_DETECTORS.items():
        # Nếu xuất hiện >= 5 ký tự của bảng chữ cái này, coi như ngôn ngữ nguồn dùng bảng chữ này
        if len(pattern.findall(sample_text)) >= 5:
            detected.append(pattern)
    return detected


def _is_untranslated(
    source_text: str,
    translated_text: str,
    source_patterns: List[Any],
    target_lang: str,
) -> bool:
    """
    Hàm lõi kiểm tra một dòng phụ đề có bị dịch lỗi hoặc chưa dịch hay không.
    Trả về True nếu:
      1. Bản dịch trống hoặc rỗng.
      2. Bản dịch giống hệt văn bản gốc (không thay đổi).
      3. Bản dịch vẫn còn sót lại ký tự ngôn ngữ nguồn (ví dụ: dịch sang tiếng Việt nhưng vẫn còn chữ Trung Quốc).
    """
    if not translated_text or not translated_text.strip():
        return True

    # Chuẩn hóa để so sánh
    src_clean = source_text.strip().replace("\n", " ").lower()
    tgt_clean = translated_text.strip().replace("\n", " ").lower()

    # Kiểm tra 1: Văn bản giống hệt nguồn
    if src_clean == tgt_clean:
        return True

    # Kiểm tra 2: Ký tự ngôn ngữ nguồn còn sót lại
    target_scripts = set()
    for name, pat in SCRIPT_DETECTORS.items():
        if name == target_lang.lower():
            target_scripts.add(pat)

    # Trường hợp đặc biệt: Tiếng Nhật và tiếng Hàn có thể sử dụng chữ Hán (Kanji/Hanja)
    if target_lang.lower() in ("japanese", "korean", "chinese"):
        target_scripts.add(CHINESE_RE)

    for pat in source_patterns:
        if pat in target_scripts:
            continue
        remain_chars = len(pat.findall(translated_text))
        if remain_chars > 0:
            return True

    return False


class TranslationWorker:
    """Quản lý và thực thi luồng dịch song song đa API key kèm cơ chế tự phục hồi cho một file phụ đề."""
    
    def __init__(self, filepath: str, settings: Dict[str, Any], checkpoint_map: Dict[int, str]):
        self.filepath = filepath
        self.settings = settings
        self.checkpoint_map = checkpoint_map  # Bản đồ kết quả đã dịch được lưu vết từ trước
        
        self.api_keys = settings.get("api_keys", [])
        self.model = settings.get("model", "deepseek-v4-flash")
        self.target_lang = settings.get("lang", "indonesian")
        self.content_type = settings.get("ctype", "auto")
        self.batch_size = settings.get("batch_size", 45)
        self.glossary = settings.get("glossary", {})
        self.plugin_name = settings.get("plugin_name", "aibox")

        self.source_patterns = []
        self._cb_lock = threading.Lock()  # Khóa đồng bộ luồng khi ghi file checkpoint

    def execute(
        self,
        blocks: List[SrtBlock],
        chunk_completed_cb: Callable[[Dict[int, str]], None]
    ) -> List[SrtBlock]:
        """Thực thi tiến trình dịch, phân phối công việc đa luồng và chạy sửa lỗi."""
        if not self.api_keys:
            raise ValueError("Cần ít nhất 1 API key để dịch.")

        # 0. Nạp danh sách các plugin nếu chưa được quét
        if not registry.get_plugin_class(self.plugin_name):
            registry.discover_plugins()

        adapter_class = registry.get_plugin_class(self.plugin_name)
        if not adapter_class:
            raise ValueError(f"Không tìm thấy plugin dịch thuật: {self.plugin_name}")

        # 1. Phát hiện ngôn ngữ nguồn để làm cơ sở xác minh bản dịch sau này
        self.source_patterns = _detect_source_scripts(blocks)
        detected_names = [name for name, pat in SCRIPT_DETECTORS.items() if pat in self.source_patterns]
        if detected_names:
            store.log(f"🔍 Phát hiện ngôn ngữ nguồn: {', '.join(detected_names)}", "info")

        # 2. Lọc bỏ các khối đã có sẵn trong checkpoint hoặc các khối nhạc cần bỏ qua
        blocks_to_translate = []
        skippable_translations = {}
        for b in blocks:
            if b.idx in self.checkpoint_map:
                continue
            if not b.text or SKIP_RE.match(b.text):
                # Khối trống hoặc khối âm nhạc -> bỏ qua không dịch, copy sang bản dịch ngay
                skippable_translations[b.idx] = b.text
                continue
            blocks_to_translate.append(b)

        # Cập nhật ngay các khối bỏ qua vào checkpoint để đồng bộ tiến độ
        if skippable_translations:
            self.checkpoint_map.update(skippable_translations)
            chunk_completed_cb(skippable_translations)

        if not blocks_to_translate:
            return self._build_result_list(blocks)

        # 3. Phân chia danh sách khối cần dịch thành N phần (mỗi API key xử lý 1 phần song song)
        n_workers = min(len(self.api_keys), 20, len(blocks_to_translate))
        chunk_size = (len(blocks_to_translate) + n_workers - 1) // n_workers
        chunks = [blocks_to_translate[i : i + chunk_size] for i in range(0, len(blocks_to_translate), chunk_size)]
        actual_workers = len(chunks)

        store.log(f"🚀 Khởi chạy {actual_workers} luồng song song | Cần dịch {len(blocks_to_translate)} blocks", "info")

        # ════════════════════════════════════════════════════════════════
        # LƯỢT 1: Chạy dịch song song đa luồng bằng ThreadPoolExecutor
        # ════════════════════════════════════════════════════════════════
        with ThreadPoolExecutor(max_workers=actual_workers) as pool:
            futures = {
                pool.submit(
                    self._translate_chunk,
                    i,
                    chunks[i],
                    self.api_keys[i % len(self.api_keys)],
                    adapter_class,
                    self.model,
                    chunk_completed_cb
                ): i
                for i in range(actual_workers)
            }
            
            for fut in as_completed(futures):
                i = futures[fut]
                try:
                    fut.result()
                    store.log(f"   ✓ Luồng {i+1}/{actual_workers} hoàn thành chunk xử lý.", "ok")
                except Exception as e:
                    store.log(f"   ❌ Luồng {i+1} gặp sự cố: {e}", "error")

        # ════════════════════════════════════════════════════════════════
        # LƯỢT 3: Tự phục hồi đa vòng (Self-Healing) sử dụng model chính
        # ════════════════════════════════════════════════════════════════
        source_text_map = {b.idx: b.text for b in blocks}

        for heal_round in range(1, MAX_HEAL_ROUNDS + 1):
            if store.get("stop_flag"):
                break

            untranslated = self._get_untranslated_blocks(blocks_to_translate, source_text_map)
            if not untranslated:
                break

            store.log(
                f"\n🔄 Tự phục hồi [{heal_round}/{MAX_HEAL_ROUNDS}] (model chính): "
                f"Còn {len(untranslated)} blocks chưa dịch đạt yêu cầu → chạy dịch bù song song...",
                "warn"
            )

            # Chạy bù song song sử dụng xoay vòng các key
            self._translate_blocks_in_parallel(
                untranslated,
                adapter_class,
                self.model,
                chunk_completed_cb
            )

        # ════════════════════════════════════════════════════════════════
        # LƯỢT 4: Cascade Model (Thử các model dự phòng khi model chính bế tắc)
        # ════════════════════════════════════════════════════════════════
        if not store.get("stop_flag"):
            untranslated = self._get_untranslated_blocks(blocks_to_translate, source_text_map)
            if untranslated:
                store.log(
                    f"\n⚡ CASCADE DỰ PHÒNG: Vẫn còn {len(untranslated)} blocks chưa dịch "
                    f"→ Thử lần lượt các mô hình dự phòng rẻ/khỏe...",
                    "warn"
                )

                for fb_idx, fallback_model in enumerate(DEFAULT_FALLBACK_MODELS):
                    untranslated = self._get_untranslated_blocks(blocks_to_translate, source_text_map)
                    if not untranslated:
                        break

                    store.log(
                        f"\n🔀 Dùng Model dự phòng [{fb_idx+1}/{len(DEFAULT_FALLBACK_MODELS)}]: "
                        f"{fallback_model} | {len(untranslated)} blocks",
                        "warn"
                    )

                    for fb_round in range(1, MAX_HEAL_ROUNDS + 1):
                        untranslated = self._get_untranslated_blocks(blocks_to_translate, source_text_map)
                        if not untranslated:
                            break

                        self._translate_blocks_in_parallel(
                            untranslated,
                            adapter_class,
                            fallback_model,
                            chunk_completed_cb
                        )

        # Kiểm tra xác minh cuối cùng báo cáo số lượng lỗi
        final_bad = len(self._get_untranslated_blocks(blocks_to_translate, source_text_map))
        if final_bad > 0 and not store.get("stop_flag"):
            store.log(f"⚠️ Kết thúc: {final_bad} blocks không thể dịch thành công sau tất cả các tầng tự sửa lỗi.", "error")

        return self._build_result_list(blocks)

    def _translate_chunk(
        self,
        worker_idx: int,
        chunk_blocks: List[SrtBlock],
        api_key: str,
        adapter_class: Type,
        model: str,
        chunk_completed_cb: Callable[[Dict[int, str]], None]
    ) -> None:
        """Tiến trình chạy trong một Thread: Cắt nhỏ chunk thành các lô batch và dịch."""
        # Giãn thời gian khởi chạy giữa các thread (stagger delay) tránh thắt nút cổ chai API
        if worker_idx > 0:
            time.sleep(worker_idx * 0.3)

        adapter = adapter_class(api_key=api_key)
        total_batches = (len(chunk_blocks) + self.batch_size - 1) // self.batch_size

        for b_idx in range(total_batches):
            if store.get("stop_flag"):
                break

            start = b_idx * self.batch_size
            batch = chunk_blocks[start : start + self.batch_size]

            label = f"Luồng {worker_idx+1} lô {b_idx+1}/{total_batches}"

            # Layer 1: Gọi API qua Adapter
            t_map = adapter.translate_batch(
                blocks=batch,
                target_lang=self.target_lang,
                content_type=self.content_type,
                glossary=self.glossary,
                model=model
            )

            # Layer 1b: Xác minh kết quả dịch từng lô (tìm block bị thiếu hoặc dịch sai)
            missing_blocks = []
            for b in batch:
                translated = t_map.get(b.idx)
                if translated is None or _is_untranslated(b.text, translated, self.source_patterns, self.target_lang):
                    missing_blocks.append(b)

            # Sửa lỗi lập tức (Immediate healing): Nếu chỉ có một vài block bị lỗi, gọi dịch bù ngay lập tức
            if missing_blocks and len(missing_blocks) < len(batch):
                retry_map = adapter.translate_batch(
                    blocks=missing_blocks,
                    target_lang=self.target_lang,
                    content_type=self.content_type,
                    glossary=self.glossary,
                    model=model
                )
                # Ghép kết quả dịch bù thành công
                for b in missing_blocks:
                    ret_txt = retry_map.get(b.idx)
                    if ret_txt and not _is_untranslated(b.text, ret_txt, self.source_patterns, self.target_lang):
                        t_map[b.idx] = ret_txt

            elif missing_blocks and len(missing_blocks) == len(batch):
                # Nếu toàn bộ lô bị thất bại (lỗi rate limit, rớt mạng), dừng nghỉ 4 giây rồi gọi dịch lại toàn bộ lô 1 lần
                time.sleep(4)
                retry_map = adapter.translate_batch(
                    blocks=batch,
                    target_lang=self.target_lang,
                    content_type=self.content_type,
                    glossary=self.glossary,
                    model=model
                )
                if retry_map:
                    for b in batch:
                        ret_txt = retry_map.get(b.idx)
                        if ret_txt and not _is_untranslated(b.text, ret_txt, self.source_patterns, self.target_lang):
                            t_map[b.idx] = ret_txt

            # Lọc bỏ các dòng dịch hỏng khỏi kết quả trước khi cập nhật lưu vết
            valid_batch_translations = {}
            for b in batch:
                txt = t_map.get(b.idx)
                if txt and not _is_untranslated(b.text, txt, self.source_patterns, self.target_lang):
                    valid_batch_translations[b.idx] = txt

            # Cập nhật luồng an toàn vào checkpoint lưu đĩa
            if valid_batch_translations:
                with self._cb_lock:
                    self.checkpoint_map.update(valid_batch_translations)
                    chunk_completed_cb(valid_batch_translations)

    def _translate_blocks_in_parallel(
        self,
        blocks: List[SrtBlock],
        adapter_class: Type,
        model: str,
        chunk_completed_cb: Callable[[Dict[int, str]], None]
    ) -> None:
        """Hàm bổ trợ hỗ trợ chạy dịch bù song song một danh sách các khối đơn lẻ."""
        n_workers = min(len(self.api_keys), 20, len(blocks))
        chunk_size = (len(blocks) + n_workers - 1) // n_workers
        chunks = [blocks[i : i + chunk_size] for i in range(0, len(blocks), chunk_size)]
        actual_workers = len(chunks)

        with ThreadPoolExecutor(max_workers=actual_workers) as pool:
            futures = [
                pool.submit(
                    self._translate_chunk,
                    i,
                    chunks[i],
                    self.api_keys[i % len(self.api_keys)],
                    adapter_class,
                    model,
                    chunk_completed_cb
                )
                for i in range(actual_workers)
            ]
            for fut in as_completed(futures):
                try:
                    fut.result()
                except Exception:
                    pass

    def _get_untranslated_blocks(self, original_blocks: List[SrtBlock], source_text_map: Dict[int, str]) -> List[SrtBlock]:
        """Duyệt tìm các khối phụ đề gốc chưa dịch thành công hoặc dịch bị lỗi trong checkpoint_map."""
        untranslated = []
        for b in original_blocks:
            translated_text = self.checkpoint_map.get(b.idx)
            src_text = source_text_map.get(b.idx, "")
            if _is_untranslated(src_text, translated_text, self.source_patterns, self.target_lang):
                untranslated.append(b)
        return untranslated

    def _build_result_list(self, original_blocks: List[SrtBlock]) -> List[SrtBlock]:
        """Hợp nhất danh sách SrtBlock gốc với nội dung văn bản đã dịch tương ứng."""
        results = []
        for b in original_blocks:
            translated_text = self.checkpoint_map.get(b.idx, b.text)
            results.append(SrtBlock(b.idx, b.timestamp, translated_text))
        results.sort(key=lambda x: x.idx)
        return results
