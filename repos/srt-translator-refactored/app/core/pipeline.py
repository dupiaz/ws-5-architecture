"""
app/core/pipeline.py — Bộ điều phối chạy dịch nhiều file và quản lý vết (Checkpoint) tự phục hồi lỗi.
"""

import os
import json
import hashlib
import threading
from typing import List, Dict, Any, Callable
from app.core.store import store
from app.utils.srt_io import read_srt, write_srt, get_output_path

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKPOINTS_DIR = os.path.join(_ROOT_DIR, "storage", "checkpoints")


def get_checkpoint_path(filepath: str) -> str:
    """Trả về đường dẫn tệp JSON checkpoint lưu vết tương ứng của file srt dựa trên mã băm MD5 đường dẫn."""
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    # Dùng mã băm MD5 từ đường dẫn tuyệt đối để tạo tên file duy nhất cho mỗi file đầu vào
    file_id = hashlib.md5(os.path.abspath(filepath).encode('utf-8')).hexdigest()
    return os.path.join(CHECKPOINTS_DIR, f"{file_id}.json")


def load_checkpoint(filepath: str) -> Dict[int, str]:
    """Nạp dữ liệu các khối đã dịch từ trước của tệp srt này nếu có checkpoint lưu đĩa."""
    path = get_checkpoint_path(filepath)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Khôi phục kiểu dữ liệu key trong JSON (chuỗi -> int block index)
            return {int(k): v for k, v in data.items()}
        except Exception as e:
            store.log(f"Lỗi đọc checkpoint tại {path}: {e}", "error")
    return {}


def save_checkpoint(filepath: str, checkpoint_data: Dict[int, str]) -> None:
    """Ghi tiến độ dịch hiện tại xuống file checkpoint JSON để đề phòng crash/dừng ứng dụng."""
    path = get_checkpoint_path(filepath)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        store.log(f"Lỗi ghi checkpoint tại {path}: {e}", "error")


def clear_checkpoint(filepath: str) -> None:
    """Xóa file checkpoint JSON sau khi một file srt đã dịch hoàn thành và lưu thành công."""
    path = get_checkpoint_path(filepath)
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            store.log(f"Không thể xóa checkpoint {path}: {e}", "warn")


class PipelineOrchestrator:
    """Điều phối chạy tuần tự việc dịch nhiều file phụ đề, xử lý tiến độ tổng thể."""
    
    def __init__(self, worker_factory: Callable[[str, Dict[str, Any], Dict[int, str]], Any]):
        """
        Args:
            worker_factory: Hàm callback tạo tiến trình dịch ngầm cho từng file.
                            Mẫu chữ ký: (filepath, settings, checkpoint_map) -> Worker
        """
        self.worker_factory = worker_factory
        self._thread: Optional[threading.Thread] = None

    def start(self, selected_files: List[Dict[str, Any]], settings: Dict[str, Any]) -> None:
        """Bắt đầu chạy pipeline dịch trong một luồng phụ độc lập để tránh đơ UI."""
        store.set("is_running", True)
        store.set("stop_flag", False)
        
        self._thread = threading.Thread(
            target=self._run_pipeline,
            args=(selected_files, settings),
            daemon=True
        )
        self._thread.start()

    def _run_pipeline(self, selected_files: List[Dict[str, Any]], settings: Dict[str, Any]) -> None:
        store.log("▶ Bắt đầu tiến trình dịch phụ đề...", "info")
        
        # Reset các biến tiến độ trong Store
        store.set("progress_pct", 0.0)
        store.set("progress_text", "0/0 blocks (0%)")

        total_files = len(selected_files)
        total_blocks = 0
        valid_files_data = []
        
        # 1. Đọc thử tất cả các file để đếm tổng số khối (block) cần xử lý
        for index_in_files, file_info in selected_files:
            filepath = file_info["path"]
            try:
                blocks = read_srt(filepath)
                total_blocks += len(blocks)
                valid_files_data.append((index_in_files, file_info, blocks))
            except Exception as e:
                store.log(f"❌ Lỗi đọc file {file_info['name']}: {e}", "error")
                self._update_file_status_in_store(index_in_files, "❌ Lỗi đọc file")

        if not valid_files_data:
            store.log("Không tìm thấy file hợp lệ nào để thực hiện dịch.", "warn")
            self._finalize_run()
            return

        done_blocks_counter = [0]  # Dùng list chứa biến đếm để có thể thay đổi dữ liệu trong callback

        def progress_callback(blocks_completed: int):
            """Hàm callback cập nhật thanh tiến trình tổng thể trên UI."""
            done_blocks_counter[0] += blocks_completed
            pct = (done_blocks_counter[0] / total_blocks * 100) if total_blocks > 0 else 0.0
            store.set("progress_pct", pct)
            store.set("progress_text", f"{done_blocks_counter[0]}/{total_blocks} blocks ({pct:.0f}%)")

        # 2. Lần lượt dịch từng file
        for index_in_files, file_info, blocks in valid_files_data:
            # Kiểm tra xem người dùng có bấm dừng hay không
            if store.get("stop_flag"):
                self._update_file_status_in_store(index_in_files, "⏹ Đã dừng")
                continue

            filepath = file_info["path"]
            store.log(f"\n📄 Đang dịch: {file_info['name']} ({len(blocks)} blocks)", "info")
            self._update_file_status_in_store(index_in_files, "⚡ Đang dịch...")

            # Khôi phục vết (checkpoint) nếu có chạy lỗi lần trước
            checkpoint_map = load_checkpoint(filepath)
            if checkpoint_map:
                store.log(f"   ↳ Tìm thấy checkpoint! Đã hoàn thành trước {len(checkpoint_map)}/{len(blocks)} blocks.", "ok")
                # Đẩy tiến trình tổng thể lên bằng số khối đã khôi phục thành công
                progress_callback(len(checkpoint_map))

            try:
                # Khởi tạo luồng dịch cho file (thông qua factory truyền vào)
                worker = self.worker_factory(filepath, settings, checkpoint_map)
                
                # Định nghĩa hàm callback cập nhật lưu vết khi từng lô (chunk) dịch xong
                def chunk_completed_callback(new_translations: Dict[int, str]):
                    checkpoint_map.update(new_translations)
                    save_checkpoint(filepath, checkpoint_map)
                    progress_callback(len(new_translations))

                # Thực thi tiến trình dịch của file
                translated_blocks = worker.execute(blocks, chunk_completed_callback)
                
                # Kiểm tra cờ dừng trước khi ghi file
                if store.get("stop_flag"):
                    self._update_file_status_in_store(index_in_files, "⏹ Đã dừng")
                    continue

                # Lưu file kết quả dịch
                out_path = get_output_path(filepath, settings["lang_code"])
                write_srt(translated_blocks, out_path)
                
                # Dịch xong trọn vẹn file -> Xóa tệp checkpoint lưu vết
                clear_checkpoint(filepath)
                
                store.log(f"💾 Đã lưu file kết quả dịch: {out_path}", "ok")
                self._update_file_status_in_store(index_in_files, "✅ Hoàn thành")
                
            except Exception as e:
                store.log(f"❌ Lỗi khi dịch file {file_info['name']}: {e}", "error")
                self._update_file_status_in_store(index_in_files, "❌ Lỗi")

        self._finalize_run()

    def _update_file_status_in_store(self, index: int, status: str) -> None:
        """Cập nhật trạng thái hiển thị của từng dòng file phụ đề trên giao diện UI."""
        files = list(store.get("files"))
        if index < len(files):
            files[index] = dict(files[index], status=status)
            store.set("files", files)

    def _finalize_run(self) -> None:
        """Hàm dọn dẹp và kết thúc lượt chạy pipeline."""
        store.set("is_running", False)
        if store.get("stop_flag"):
            store.log("\n⏹ Đã dừng tiến trình dịch phụ đề.", "warn")
        else:
            store.log("\n🎉 HOÀN THÀNH TOÀN BỘ TIẾN TRÌNH!", "ok")
            store.set("progress_pct", 100.0)
