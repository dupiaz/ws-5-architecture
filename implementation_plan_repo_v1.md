# Kế Hoạch: Reference Implementation Repo

## Mục Tiêu

Tạo một repo Python **chạy được**, thể hiện **đầy đủ 14 tính chất kiến trúc** từ Reference Architecture, nhưng chỉ dùng:
- **1 module:** ASR (Nhận dạng giọng nói)
- **1 plugin:** MockWhisper (giả lập, không cần GPU)

Developer/Agent đọc repo này sẽ hiểu ngay "code phải viết theo pattern nào" khi thêm module/plugin mới.

---

## Cấu Trúc Repo

```
sample/
├── README.md                          ← Giải thích kiến trúc + cách chạy
├── pyproject.toml                     ← Dependencies (PySide6, FastAPI, etc.)
│
├── app/                               ← 🔵 CORE APPLICATION
│   ├── __init__.py
│   ├── main.py                        ← Entry point: khởi tạo app
│   │
│   ├── core/                          ← 🧠 Engine (Invariant)
│   │   ├── __init__.py
│   │   ├── contracts.py               ← Base contracts: StepInput, StepOutput
│   │   ├── interfaces.py             ← StepEngine ABC + PluginMetadata
│   │   ├── plugin_registry.py        ← Tìm & đăng ký plugins
│   │   ├── pipeline.py               ← Pipeline engine: chạy DAG steps
│   │   ├── orchestrator.py           ← Điều phối pipeline + resource check
│   │   ├── resource_manager.py       ← Kiểm tra VRAM/RAM
│   │   ├── checkpoint.py             ← Lưu/load checkpoint
│   │   └── store.py                  ← GlobalStore (Centralized State)
│   │
│   ├── ui/                            ← 🖥️ Giao diện (PySide6)
│   │   ├── __init__.py
│   │   ├── main_window.py            ← Cửa sổ chính
│   │   └── step_view.py              ← View cho 1 step: input + progress + output
│   │
│   ├── workers/                       ← ⚙️ Background workers
│   │   ├── __init__.py
│   │   └── pipeline_worker.py        ← QThread worker cho pipeline step
│   │
│   └── license/                       ← 🔑 License management
│       ├── __init__.py
│       ├── backends.py               ← LicenseBackend ABC + MockBackend
│       └── manager.py                ← LicenseManager (validate, cache, offline)
│
├── modules/                           ← 📦 Module interfaces (domain)
│   ├── __init__.py
│   └── asr/
│       ├── __init__.py
│       ├── engine.py                  ← ASREngine(StepEngine) interface
│       └── contracts.py              ← TranscriptionResult, Segment dataclasses
│
├── plugins/                           ← 🔌 Plugin implementations
│   ├── __init__.py
│   └── asr/
│       └── mock_whisper/
│           ├── __init__.py
│           ├── adapter.py            ← MockWhisperAdapter(ASREngine)
│           └── plugin.toml           ← Metadata: name, version, vram_mb, etc.
│
├── services/                          ← 🌐 Isolated AI services (FastAPI)
│   └── asr_service/
│       ├── requirements.txt
│       └── server.py                 ← FastAPI server: /process, /health, SSE progress
│
├── storage/                           ← 💾 Project data (runtime, gitignored)
│   └── projects/
│       └── .gitkeep
│
└── tests/                             ← ✅ Tests
    ├── __init__.py
    ├── test_contracts.py             ← Test dataclass serialization
    ├── test_plugin_registry.py       ← Test plugin discovery
    ├── test_pipeline.py              ← Test pipeline execution + checkpoint
    └── test_license.py               ← Test license validation + offline
```

---

## Mỗi File Minh Họa Pattern Nào

| File | Pattern(s) minh họa | Mô tả |
|---|---|---|
| `core/interfaces.py` | **Dependency Inversion, Contract-First** | `StepEngine` ABC — mọi plugin phải implement |
| `core/contracts.py` | **Contract-First** | `StepInput`, `StepOutput` base dataclasses |
| `core/plugin_registry.py` | **Dependency Inversion, Separation of Concerns** | Scan `plugins/` folder, đăng ký adapters |
| `core/pipeline.py` | **Pipeline Composability** | DAG runner: nhận `Pipeline([Step(...)])` config, chạy tuần tự |
| `core/orchestrator.py` | **Separation of Concerns** | Điều phối: check resource → run pipeline → handle errors |
| `core/resource_manager.py` | **Resource-Aware Scheduling** | Check VRAM giả lập, quyết định load/unload |
| `core/checkpoint.py` | **Fault Isolation, Data Locality** | Save/load JSON checkpoint sau mỗi step |
| `core/store.py` | **Centralized State, Event-Driven** | GlobalStore + PySide6 Signals |
| `ui/main_window.py` | **UI Thread Sanctity** | Main window chỉ render, không chạy logic nặng |
| `ui/step_view.py` | **Event-Driven, UI Thread Sanctity** | Progress bar + result display via Signal/Slot |
| `workers/pipeline_worker.py` | **Event-Driven, UI Thread Sanctity** | QThread worker: dispatch task, emit progress |
| `license/backends.py` | **Dependency Inversion** | `LicenseBackend` ABC + `MockLicenseBackend` |
| `license/manager.py` | **Fault Isolation** | Validate → cache → offline grace period |
| `modules/asr/engine.py` | **Dependency Inversion** | `ASREngine(StepEngine)` domain interface |
| `modules/asr/contracts.py` | **Contract-First** | `TranscriptionResult`, `Segment` |
| `plugins/asr/mock_whisper/adapter.py` | **Dependency Inversion** | `MockWhisperAdapter(ASREngine)` — giả lập inference |
| `services/asr_service/server.py` | **Process Isolation** | FastAPI server: `/process`, `/health`, SSE streaming |

---

## Chi Tiết Thiết Kế Một Số File Quan Trọng

### MockWhisperAdapter — Plugin giả lập

```python
# Giả lập AI inference bằng time.sleep(3)
# → Chạy được trên MỌI máy, không cần GPU
# → Demo đầy đủ: interface compliance, progress reporting, contract output

class MockWhisperAdapter(ASREngine):
    def transcribe(self, audio_path, language):
        time.sleep(3)  # Giả lập inference 3 giây
        return TranscriptionResult(
            language=language,
            segments=[
                Segment(0.0, 2.5, "Xin chào các bạn", confidence=0.95),
                Segment(2.5, 5.0, "Đây là demo kiến trúc", confidence=0.92),
            ],
            full_text="Xin chào các bạn. Đây là demo kiến trúc.",
            duration_seconds=5.0,
            model_name="mock_whisper_v1",
        )
```

### FastAPI Service — Process Isolation demo

```python
# services/asr_service/server.py
# Chạy như subprocess riêng, giao tiếp qua HTTP

@app.post("/process")
async def process_audio(request: ProcessRequest):
    adapter = MockWhisperAdapter()
    result = adapter.transcribe(request.audio_path, request.language)
    return result

@app.get("/health")
async def health():
    return {"status": "ok", "vram_available_mb": 6000}

@app.get("/progress")
async def progress_stream():
    # SSE streaming demo
    async def event_generator():
        for i in range(0, 101, 10):
            yield f"data: {json.dumps({'percent': i})}\n\n"
            await asyncio.sleep(0.3)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## Cách Chạy Demo

```bash
# 1. Cài dependencies
cd sample
pip install -e ".[dev]"

# 2. Chạy tests (không cần GUI)
pytest tests/ -v

# 3. Chạy FastAPI service (Process Isolation demo)
python -m services.asr_service.server
# → Mở http://localhost:8100/docs để thấy Swagger API

# 4. Chạy app GUI (PySide6)
python -m app.main
# → Cửa sổ mở ra, bấm "Start ASR" → thấy progress bar → thấy kết quả
```

---

## Verification Plan

### Automated Tests
```bash
pytest tests/ -v
```

Tests kiểm tra:
- `test_contracts.py`: Dataclass serialization/deserialization
- `test_plugin_registry.py`: Plugin discovery từ folder
- `test_pipeline.py`: Pipeline execution + checkpoint save/load
- `test_license.py`: License validation + offline grace period

### Manual Verification
- Chạy `python -m app.main` → GUI hiện ra, bấm button, thấy progress bar
- Chạy FastAPI service → mở `/docs` → test endpoint
- Kiểm tra `storage/projects/` → thấy checkpoint files sau khi chạy pipeline

---

## Open Questions

> [!IMPORTANT]
> 1. **Nên đặt repo mẫu ở đâu?** Hiện tôi plan đặt trong `d:\antigravity\ws-5-architecture\sample\`. Bạn muốn đặt ở vị trí khác không?
> 2. **Mock level:** MockWhisper dùng `time.sleep(3)` để giả lập. Bạn có muốn nó đọc 1 file audio thật và trả về kết quả cứng (hardcoded) không? Hay mock đơn giản là đủ?
> 3. **PySide6 GUI:** Bạn có muốn GUI demo đẹp (styled) hay chỉ cần functional (nút bấm + progress bar + text output) là đủ cho mục đích minh họa kiến trúc?
