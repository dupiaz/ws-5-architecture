# Kế Hoạch: Reference Implementation Repo (v2 — Updated)

## Thay Đổi So Với v1

| # | Comment của bạn | Thay đổi |
|---|---|---|
| 1 | Đánh giá Vertical Slice Architecture | ✅ Phân tích 3 hướng, chọn **Hybrid** (xem bên dưới) |
| 2 | Vị trí repo | ✅ `D:\antigravity\ws-5-architecture\repos\dubbing-sample` |
| 3 | Mock phải mô phỏng faster-whisper | ✅ MockWhisperModel mirror API surface thật |
| 4 | GUI functional only | ✅ Chỉ button + progress bar + text output |

---

## Phân Tích Vertical Slice Architecture

### Ba hướng tổ chức

#### Hướng A: Horizontal (Layer-based) — Plan v1

```
app/
├── core/           ← Tất cả core logic gộp chung
├── ui/             ← Tất cả UI gộp chung
├── workers/        ← Tất cả workers gộp chung
modules/
├── asr/            ← Chỉ interface
plugins/
├── asr/            ← Chỉ implementation
services/
├── asr_service/    ← Chỉ FastAPI server
```

**Vấn đề:** Khi thêm module TTS, phải sửa/thêm file ở **5 thư mục khác nhau** (modules/, plugins/, services/, workers/, ui/). Developer phải nhảy qua nhảy lại giữa các folder → dễ quên, dễ thiếu.

#### Hướng B: Vertical Slice thuần

```
modules/
├── asr/
│   ├── engine.py, contracts.py
│   ├── worker.py, view.py
│   ├── plugins/mock_whisper/
│   └── service/server.py
├── tts/
│   ├── engine.py, contracts.py
│   ├── worker.py, view.py
│   ├── plugins/mock_xtts/
│   └── service/server.py
```

**Vấn đề:** Core framework (Pipeline engine, Orchestrator, GlobalStore, ResourceManager) đặt ở đâu? Chúng là **cross-cutting** — phục vụ TẤT CẢ modules, không thuộc module nào cả.

#### Hướng C: Hybrid (Horizontal core + Vertical modules) ← **KHUYẾN NGHỊ**

```
app/core/           ← HORIZONTAL: Infrastructure dùng chung cho mọi module
modules/asr/        ← VERTICAL: Mỗi module là 1 slice tự chứa
```

### Tại sao Hybrid là tối ưu cho kiểu hệ thống này

| Tiêu chí | Horizontal (A) | Vertical thuần (B) | Hybrid (C) ✅ |
|---|---|---|---|
| **Thêm module mới** | Sửa 5 folders | Copy 1 folder | Copy 1 folder (modules/) |
| **Core framework** | ✅ Gọn 1 chỗ | ❌ Không biết đặt đâu | ✅ Gọn 1 chỗ (app/core/) |
| **Module tự chứa** | ❌ Phân tán | ✅ Tất cả trong 1 folder | ✅ Tất cả trong 1 folder |
| **Onboarding dev mới** | Phải hiểu cả project | Chỉ cần xem 1 module | Xem core 1 lần + 1 module |
| **Agent thêm plugin** | Sửa nhiều file xa nhau | Sửa 1 folder | Sửa 1 folder |

**Lý do quyết định:**

1. **Core framework là bất biến (invariant)** — Pipeline engine, Orchestrator, GlobalStore không thay đổi khi thêm module → nên tách riêng
2. **Domain modules là variable** — mỗi module có interface, contracts, plugins, worker, view KHÁC NHAU → nên gộp theo vertical slice
3. **Thêm module = copy folder** — developer/agent copy `modules/asr/` → đổi tên → sửa interface + contracts → xong. Không sợ thiếu file

> [!IMPORTANT]
> **Quy tắc vàng:** "Nếu nó thay đổi cùng nhau, nó sống cùng nhau" (things that change together, live together).
> - Core framework thay đổi khi kiến trúc thay đổi → sống chung ở `app/core/`
> - ASR module thay đổi khi domain logic thay đổi → sống chung ở `modules/asr/`

---

## Cấu Trúc Repo Mới (Hybrid)

```
D:\antigravity\ws-5-architecture\repos\dubbing-sample\
│
├── README.md                          ← Kiến trúc + cách chạy + cách thêm module mới
├── pyproject.toml                     ← Dependencies (PySide6, FastAPI, uvicorn, httpx)
│
├── app/                               ← 🔵 CORE APPLICATION (Horizontal — dùng chung)
│   ├── __init__.py
│   ├── main.py                        ← Entry point: khởi tạo PySide6 app
│   │
│   ├── core/                          ← 🧠 Framework Engine (Invariant)
│   │   ├── __init__.py
│   │   ├── contracts.py               ← Base: StepInput, StepOutput, PluginMetadata
│   │   ├── interfaces.py             ← StepEngine ABC
│   │   ├── plugin_registry.py        ← Scan modules/*/plugins/, đăng ký adapters
│   │   ├── pipeline.py               ← Pipeline engine: nhận config, chạy DAG
│   │   ├── orchestrator.py           ← Điều phối: resource check → pipeline → error
│   │   ├── resource_manager.py       ← VRAM/RAM check (giả lập cho demo)
│   │   ├── checkpoint.py             ← Save/load checkpoint JSON
│   │   └── store.py                  ← GlobalStore + PySide6 Signals
│   │
│   ├── ui/                            ← 🖥️ App Shell (Horizontal)
│   │   ├── __init__.py
│   │   └── main_window.py            ← Main window: compose views từ modules
│   │
│   └── license/                       ← 🔑 License (Horizontal — dùng chung)
│       ├── __init__.py
│       ├── backends.py               ← LicenseBackend ABC + MockBackend
│       └── manager.py                ← LicenseManager
│
├── modules/                           ← 📦 DOMAIN MODULES (Vertical Slices)
│   ├── __init__.py
│   │
│   └── asr/                           ← 🎤 ASR Module — 1 VERTICAL SLICE ĐẦY ĐỦ
│       ├── __init__.py
│       ├── engine.py                  ← ASREngine(StepEngine) — domain interface
│       ├── contracts.py              ← TranscriptionResult, Segment, WordTiming
│       ├── worker.py                 ← ASRWorker(QObject) — QThread worker
│       ├── view.py                   ← ASRStepView(QWidget) — UI cho step ASR
│       │
│       ├── plugins/                   ← 🔌 Plugin implementations cho ASR
│       │   ├── __init__.py
│       │   └── mock_whisper/          ← Mock plugin mô phỏng faster-whisper
│       │       ├── __init__.py
│       │       ├── mock_model.py     ← MockWhisperModel (mirror faster-whisper API)
│       │       ├── adapter.py        ← MockWhisperAdapter(ASREngine)
│       │       └── plugin.toml       ← Metadata: name, version, vram_mb
│       │
│       └── service/                   ← 🌐 FastAPI service (Process Isolation)
│           ├── requirements.txt      ← Chỉ deps của service này
│           └── server.py             ← FastAPI: /process, /health, SSE progress
│
├── storage/                           ← 💾 Runtime data (gitignored)
│   └── projects/
│       └── .gitkeep
│
└── tests/                             ← ✅ Tests
    ├── __init__.py
    ├── test_contracts.py
    ├── test_plugin_registry.py
    ├── test_pipeline.py
    └── test_license.py
```

### Khi thêm module TTS sau này

```
modules/
├── asr/          ← Module ASR (đã có)
│   ├── engine.py
│   ├── contracts.py
│   ├── worker.py
│   ├── view.py
│   ├── plugins/mock_whisper/
│   └── service/server.py
│
└── tts/          ← Module TTS (copy từ asr/, đổi tên, sửa nội dung)
    ├── engine.py             ← TTSEngine(StepEngine)
    ├── contracts.py          ← SynthesisResult, AudioSegment
    ├── worker.py             ← TTSWorker
    ├── view.py               ← TTSStepView
    ├── plugins/mock_xtts/
    │   ├── mock_model.py
    │   ├── adapter.py
    │   └── plugin.toml
    └── service/server.py
```

> [!TIP]
> **Agent workflow:** "Thêm module TTS" = copy `modules/asr/` → rename → sửa 4 file interface (engine, contracts, worker, view) + 3 file plugin (mock_model, adapter, plugin.toml). Core app KHÔNG SỬA GÌ — plugin_registry tự scan folder mới.

---

## Mock Whisper — Mô Phỏng faster-whisper API

### Thiết kế MockWhisperModel

Mock phải **mirror chính xác API surface** của `faster_whisper.WhisperModel` để chuyển sang real chỉ cần đổi import:

```python
# modules/asr/plugins/mock_whisper/mock_model.py

from dataclasses import dataclass
import time

@dataclass
class MockSegment:
    """Mirror faster_whisper.transcribe() segment output."""
    start: float
    end: float
    text: str
    words: list | None = None    # Word-level timestamps
    avg_logprob: float = -0.3
    no_speech_prob: float = 0.01

@dataclass  
class MockTranscriptionInfo:
    """Mirror faster_whisper TranscriptionInfo."""
    language: str
    language_probability: float
    duration: float
    all_language_probs: list | None = None


class MockWhisperModel:
    """
    Mô phỏng faster_whisper.WhisperModel API surface.
    
    Chuyển sang real faster-whisper:
      1. pip install faster-whisper
      2. Đổi: from .mock_model import MockWhisperModel as WhisperModel
         Thành: from faster_whisper import WhisperModel
      3. Xóa file mock_model.py
    """
    
    def __init__(
        self,
        model_size_or_path: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        cpu_threads: int = 4,
        num_workers: int = 1,
    ):
        self.model_size = model_size_or_path
        self.device = device
        self.compute_type = compute_type
        
        # Giả lập thời gian load model (real: 15-45 giây)
        time.sleep(2)
    
    def transcribe(
        self,
        audio: str,                    # path to audio file
        language: str | None = None,
        beam_size: int = 5,
        word_timestamps: bool = False,
        vad_filter: bool = True,
    ) -> tuple[list[MockSegment], MockTranscriptionInfo]:
        """
        Mirror faster_whisper.WhisperModel.transcribe() signature.
        
        Real faster-whisper trả về (generator[Segment], TranscriptionInfo).
        Mock trả về (list[MockSegment], MockTranscriptionInfo) để đơn giản.
        """
        # Giả lập thời gian inference (real: 30-120 giây cho 10 phút audio)
        time.sleep(3)
        
        segments = [
            MockSegment(start=0.0, end=2.5, text="Xin chào các bạn"),
            MockSegment(start=2.5, end=5.8, text="Hôm nay chúng ta sẽ tìm hiểu về kiến trúc phần mềm"),
            MockSegment(start=6.0, end=8.2, text="Đây là một chủ đề rất quan trọng"),
        ]
        
        info = MockTranscriptionInfo(
            language=language or "vi",
            language_probability=0.98,
            duration=8.2,
        )
        
        return segments, info
```

### Adapter chuyển đổi output → contract chuẩn

```python
# modules/asr/plugins/mock_whisper/adapter.py

from modules.asr.engine import ASREngine
from modules.asr.contracts import TranscriptionResult, Segment

# ⚡ Đổi dòng này khi chuyển sang real faster-whisper:
from .mock_model import MockWhisperModel as WhisperModel
# Thành: from faster_whisper import WhisperModel


class MockWhisperAdapter(ASREngine):
    """
    Adapter: Chuyển đổi output faster-whisper → TranscriptionResult contract.
    
    Adapter này hoạt động GIỐNG NHAU cho cả mock lẫn real faster-whisper,
    vì mock mirror API surface thật.
    """
    
    PLUGIN_NAME = "mock_whisper"
    VRAM_REQUIRED_MB = 3500    # large-v3 cần ~3.5 GB
    
    def __init__(self):
        self._model = None
    
    def load_model(self, model_size: str = "large-v3", device: str = "cuda"):
        """Load model (lazy — chỉ load khi cần)."""
        self._model = WhisperModel(
            model_size_or_path=model_size,
            device=device,
            compute_type="float16",
        )
    
    def transcribe(self, audio_path: str, language: str) -> TranscriptionResult:
        """Implement ASREngine.transcribe() — trả về TranscriptionResult chuẩn."""
        if not self._model:
            self.load_model()
        
        raw_segments, info = self._model.transcribe(
            audio=audio_path,
            language=language,
            beam_size=5,
            word_timestamps=False,
        )
        
        # Chuyển đổi output đặc thù → contract chuẩn
        segments = [
            Segment(
                start_time=seg.start,
                end_time=seg.end,
                text=seg.text.strip(),
                speaker_id=None,
                confidence=1.0 - abs(seg.avg_logprob),
            )
            for seg in raw_segments
        ]
        
        return TranscriptionResult(
            language=info.language,
            segments=segments,
            full_text=" ".join(s.text for s in segments),
            duration_seconds=info.duration,
            model_name=f"faster_whisper_{self._model.model_size}",
        )
```

### Hướng dẫn chuyển Mock → Real

```diff
# modules/asr/plugins/mock_whisper/adapter.py

- from .mock_model import MockWhisperModel as WhisperModel
+ from faster_whisper import WhisperModel

  # Tất cả code adapter KHÔNG CẦN SỬA — vì mock mirror API surface thật
```

> [!TIP]
> **Đây chính là sức mạnh của Adapter Pattern:** Adapter chuyển đổi output bên ngoài → contract bên trong. Mock hay real đều đi qua cùng adapter → core app không biết, không cần biết.

---

## GUI — Functional Only

```
┌────────────────────────────────────────────────┐
│  Dubbing Sample — Architecture Demo            │
├────────────────────────────────────────────────┤
│                                                │
│  ┌─ ASR Step ────────────────────────────────┐ │
│  │                                            │ │
│  │  Audio file: [________________] [Browse]   │ │
│  │  Plugin:     [mock_whisper     ▼]          │ │
│  │                                            │ │
│  │  [▶ Start ASR]                             │ │
│  │                                            │ │
│  │  Progress: ████████████░░░░░░░ 65%         │ │
│  │  Status: Đang nhận dạng giọng nói...       │ │
│  │                                            │ │
│  │  ┌─ Result ─────────────────────────────┐  │ │
│  │  │ [0.0-2.5] Xin chào các bạn          │  │ │
│  │  │ [2.5-5.8] Hôm nay chúng ta sẽ...    │  │ │
│  │  │ [6.0-8.2] Đây là một chủ đề...      │  │ │
│  │  └──────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────┘ │
│                                                │
│  Status Bar: Pipeline: idle | VRAM: 6000 MB    │
└────────────────────────────────────────────────┘
```

Không styling phức tạp, chỉ QWidget mặc định + layout rõ ràng.

---

## Verification Plan

### Automated
```bash
cd D:\antigravity\ws-5-architecture\repos\dubbing-sample
pip install -e ".[dev]"
pytest tests/ -v
```

### Manual
1. `python -m app.main` → GUI → bấm Start → thấy progress → thấy result
2. `python -m modules.asr.service.server` → `http://localhost:8100/docs` → test API
3. Kiểm tra `storage/projects/` → checkpoint files xuất hiện
4. Chạy lại pipeline → skip step đã checkpoint → resume hoạt động

---

## Thứ Tự Triển Khai

```
Phase 1: Foundation (core + contracts)
  ├── pyproject.toml
  ├── app/core/contracts.py
  ├── app/core/interfaces.py
  ├── app/core/store.py
  └── app/core/checkpoint.py

Phase 2: Module ASR (vertical slice)
  ├── modules/asr/engine.py
  ├── modules/asr/contracts.py
  ├── modules/asr/plugins/mock_whisper/mock_model.py
  └── modules/asr/plugins/mock_whisper/adapter.py

Phase 3: Infrastructure (pipeline + orchestrator)
  ├── app/core/plugin_registry.py
  ├── app/core/pipeline.py
  ├── app/core/orchestrator.py
  └── app/core/resource_manager.py

Phase 4: UI + Worker
  ├── modules/asr/worker.py
  ├── modules/asr/view.py
  ├── app/ui/main_window.py
  └── app/main.py

Phase 5: Process Isolation
  └── modules/asr/service/server.py

Phase 6: License + Tests
  ├── app/license/backends.py
  ├── app/license/manager.py
  └── tests/*.py
```
