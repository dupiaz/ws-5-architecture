# Các Tính Chất Kiến Trúc Bắt Buộc — Góc Nhìn Chuyên Gia Thiết Kế Hệ Thống Desktop

> Tài liệu này phân tích **tại sao** mỗi tính chất kiến trúc là cần thiết, dưới lăng kính đặc thù của một ứng dụng **Windows Desktop bằng Python** chạy **AI inference nặng** cho quy trình lồng tiếng video.

---

## Bối Cảnh Đặc Thù — Tại Sao Desktop AI App Khác Biệt

Trước khi đi vào từng tính chất, cần hiểu rõ bối cảnh đặc thù mà kiến trúc này phải phục vụ — vì nó **khác hoàn toàn** với cả web app lẫn desktop app truyền thống:

| Đặc thù | Hệ quả kiến trúc |
|---|---|
| **Chạy trên 1 máy duy nhất** của user | Không có horizontal scaling. Mọi tài nguyên (CPU, RAM, GPU) phải được quản lý tinh vi trên 1 node |
| **AI inference cực nặng** (Whisper load 3-5GB VRAM, XTTS mất 10-30s/câu) | UI thread bị block = app đơ = user nghĩ app crash. Thread/process boundary là vấn đề sống còn |
| **Đa dạng model/API** thay đổi liên tục | Hôm nay dùng WhisperX, ngày mai có model tốt hơn. Kiến trúc phải cho phép swap mà không rewrite |
| **Pipeline nhiều bước tuần tự** (Demux → ASR → Translate → TTS → Mix → Mux) | Cần cơ chế orchestration, checkpoint, resume. Mất điện giữa chừng không được mất toàn bộ |
| **User là người dùng cuối**, không phải developer | Phải hoạt động ổn định, lỗi phải được xử lý graceful, không bao giờ hiện traceback |
| **Chạy offline được** (local models) nhưng cũng hỗ trợ cloud API | Dual-mode: local inference + cloud API phải transparent với phần còn lại của hệ thống |

---

# PHẦN A — KIẾN TRÚC LOGIC (Logical Architecture)

Kiến trúc logic trả lời câu hỏi: **"Các thành phần được tổ chức và giao tiếp với nhau theo nguyên tắc nào?"**

---

## 1. Separation of Concerns — Phân Tách Trách Nhiệm

### Định nghĩa
Mỗi thành phần trong hệ thống chỉ chịu trách nhiệm cho **đúng một khía cạnh** của bài toán. Không có thành phần nào vừa vẽ UI vừa gọi AI model vừa quản lý file.

### Tại sao quan trọng (tổng quát)
Khi trách nhiệm bị trộn lẫn, một thay đổi nhỏ ở chức năng A sẽ vô tình phá vỡ chức năng B. Đây là nguyên nhân số 1 gây ra bug "ở đâu ra" trong các dự án phần mềm.

### Tại sao đặc biệt quan trọng cho dự án này

Hệ thống video dubbing có **ít nhất 5 miền trách nhiệm rất khác biệt về bản chất**:

```
┌─────────────┐   ┌──────────────┐   ┌──────────────┐   ┌─────────────┐   ┌────────────┐
│  Giao diện  │   │  Điều phối   │   │  Nghiệp vụ   │   │  AI/ML      │   │  Hạ tầng   │
│  (Qt/UI)    │   │  (Pipeline)  │   │  (Dubbing)   │   │  (Inference) │   │  (File/DB) │
│             │   │              │   │              │   │             │   │            │
│ PySide6     │   │ DAG, State   │   │ ASR, TTS,    │   │ PyTorch,    │   │ FFmpeg,    │
│ Signals     │   │ Checkpoint   │   │ Translation  │   │ CUDA,       │   │ SQLite,    │
│ QSS Theme   │   │ Scheduling   │   │ Audio Mix    │   │ REST APIs   │   │ File I/O   │
└─────────────┘   └──────────────┘   └──────────────┘   └─────────────┘   └────────────┘
```

Nếu trộn logic gọi CUDA vào code UI, thì:
- Không thể test UI mà không có GPU
- Không thể thay model AI mà không sửa code UI
- Bug UI và bug inference trộn lẫn, debug cực khó

### Vi phạm sẽ gây ra
- Technical debt tích lũy theo cấp số nhân
- Mỗi lần sửa bug tạo ra 2-3 bug mới
- Không thể phân công công việc cho nhiều người

---

## 2. Dependency Inversion — Đảo Ngược Phụ Thuộc

### Định nghĩa
Các module cấp cao (Orchestrator, Use Case) **không bao giờ phụ thuộc trực tiếp** vào module cấp thấp (WhisperX, ElevenLabs). Cả hai cùng phụ thuộc vào **một abstraction (interface) ở giữa**.

### Tại sao đây là tính chất quan trọng nhất cho yêu cầu "linh hoạt model/API"

```
❌ SAI (Tight coupling):
   Orchestrator → import whisperx → gọi whisperx.transcribe()
   
   Hậu quả: Muốn đổi sang Faster-Whisper phải sửa Orchestrator
   
✅ ĐÚNG (Dependency Inversion):
   Orchestrator → gọi ASREngine.transcribe()    ← Interface (abstraction)
                                                     ↑
                                                 WhisperXPlugin implements ASREngine
                                                 FasterWhisperPlugin implements ASREngine
                                                 OpenAIWhisperPlugin implements ASREngine
```

### Tại sao đặc biệt quan trọng cho dự án này

Thế giới AI thay đổi **cực nhanh**:
- 2023: WhisperX là state-of-the-art cho ASR
- 2024: Faster-Whisper nhanh hơn 4x, Distil-Whisper nhẹ hơn 6x
- 2025: Có thể xuất hiện model mới hoàn toàn

Nếu code nghiệp vụ (pipeline logic) bị gắn chặt vào 1 model cụ thể, thì **mỗi lần đổi model = rewrite cả pipeline**. Với Dependency Inversion, đổi model = chỉ viết 1 adapter mới, không sửa gì ở Core.

### Cách triển khai cụ thể

```python
# modules/asr/asr_engine.py — INTERFACE (không biết gì về Whisper hay OpenAI)
from abc import ABC, abstractmethod

class ASREngine(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, language: str) -> TranscriptionResult:
        """Trả về kết quả chuẩn hóa, bất kể công nghệ bên dưới."""
        ...

# plugins/asr/whisperx_local/adapter.py — IMPLEMENTATION
class WhisperXAdapter(ASREngine):
    def transcribe(self, audio_path, language):
        # Gọi WhisperX, biến đổi output thành TranscriptionResult chuẩn
        ...

# plugins/asr/faster_whisper/adapter.py — THÊM MỚI, KHÔNG SỬA GÌ Ở CORE
class FasterWhisperAdapter(ASREngine):
    def transcribe(self, audio_path, language):
        # Gọi Faster-Whisper, biến đổi output thành TranscriptionResult chuẩn
        ...
```

### Vi phạm sẽ gây ra
- Mỗi lần đổi model/API = sửa toàn bộ pipeline code
- Không thể cho user chọn model tại runtime
- Không thể test pipeline mà không có model thật (không mock được)

---

## 3. Event-Driven Reactivity — Giao Tiếp Hướng Sự Kiện

### Định nghĩa
Các thành phần **không gọi trực tiếp** lẫn nhau. Thay vào đó, chúng **phát ra sự kiện** (events) và **lắng nghe sự kiện** (subscribe). Một thành phần phát lệnh, thành phần khác nhận và xử lý — không ai chờ ai.

### Tại sao đây là tính chất sống còn cho Python Desktop

Đây là điểm mà **nhiều kiến trúc sư thiếu kinh nghiệm desktop hay mắc sai lầm nghiêm trọng nhất**.

Trong PySide6/PyQt6, **Main Thread = UI Thread**. Nếu bất kỳ đoạn code nào chạy trên Main Thread mất quá 100ms, giao diện sẽ:
- Không phản hồi click chuột
- Không cập nhật thanh tiến trình
- Windows hiện dòng chữ "(Not Responding)"
- User nghĩ app crash → Force close → Mất dữ liệu

Trong hệ thống dubbing, gần như **mọi tác vụ core** đều mất hàng chục giây đến hàng phút:

| Tác vụ | Thời gian điển hình |
|---|---|
| Load WhisperX model vào VRAM | 15-45 giây |
| Transcribe 10 phút audio | 30-120 giây |
| TTS cho 100 câu | 5-15 phút |
| FFmpeg demux/mux video 4K | 10-60 giây |

**Giải pháp duy nhất đúng: Event-Driven Architecture**

```
UI Thread                    Worker Thread/Process
─────────                    ────────────────────
  │                                   │
  ├── dispatch("START_ASR") ────────► │
  │   (trả về ngay, UI vẫn mượt)     ├── Load model...
  │                                   ├── Transcribe...
  │ ◄── event("PROGRESS", 50%) ──────┤
  │   (cập nhật progress bar)         │
  │ ◄── event("PROGRESS", 100%) ─────┤
  │ ◄── event("ASR_COMPLETE", data) ──┤
  │   (hiển thị kết quả)             │
```

### Vi phạm sẽ gây ra
- App đơ mỗi khi chạy inference
- User mất niềm tin, bỏ app
- Không thể cancel task giữa chừng (vì UI bị block, nút Cancel không click được)

---

## 4. Centralized State Management — Quản Lý Trạng Thái Tập Trung

### Định nghĩa
Toàn bộ trạng thái ứng dụng (project hiện tại, danh sách giọng, tiến trình pipeline, cấu hình model đang chọn...) được lưu tại **một nơi duy nhất** (Global Store). Mọi thành phần đọc/ghi state thông qua Store này.

### Tại sao quan trọng cho Desktop app (khác Web app)

Trong web app, mỗi request là stateless — không cần shared state.

Trong desktop app, **mọi thứ là stateful**:
- User mở project → tất cả các tab phải biết project nào đang mở
- User chọn giọng trong Voice Studio → tab Auto Dubbing phải thấy giọng đó
- Pipeline đang chạy 60% → tất cả các view phải hiện thanh tiến trình
- User thay đổi API key → tất cả plugin liên quan phải biết

Nếu mỗi feature tự quản lý state riêng (như v1.5 gợi ý), sẽ xảy ra:
- **State inconsistency:** Feature A nghĩ dùng giọng X, Feature B nghĩ dùng giọng Y
- **Spaghetti communication:** Feature A gọi Feature B để hỏi state → Feature B gọi Feature C → vòng lặp phụ thuộc
- **Khó persist/restore:** Khi app restart, phải khôi phục state ở N nơi khác nhau

### Mô hình đúng

```
                    ┌─────────────────────┐
                    │    GLOBAL STORE      │
                    │                     │
                    │  current_project    │
                    │  selected_voice     │
                    │  pipeline_status    │
                    │  plugin_configs     │
                    │  ...                │
                    └──────┬──────────────┘
                           │
              ┌────────────┼────────────┐
              │ subscribe  │ subscribe  │ subscribe
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Feature  │ │ Feature  │ │ Feature  │
        │ Subtitle │ │ Voice    │ │ Dubbing  │
        │ View     │ │ Studio   │ │ View     │
        └──────────┘ └──────────┘ └──────────┘
        
    Mỗi View chỉ subscribe những state nó cần.
    Khi state thay đổi, View tự động cập nhật.
    Không Feature nào cần biết Feature khác tồn tại.
```

### Vi phạm sẽ gây ra
- Dữ liệu không đồng bộ giữa các màn hình
- Bug "phantom" — chỉ xảy ra khi mở đúng tổ hợp tab
- Không thể implement Undo/Redo (vì không biết state nằm ở đâu)

---

## 5. Pipeline Composability — Khả Năng Tổ Hợp Pipeline

### Định nghĩa
Quy trình dubbing (Demux → ASR → Translate → TTS → Mix → Mux) phải được mô tả dưới dạng **cấu hình** (configuration), không phải **code cứng** (hardcoded). Mỗi bước là một node trong DAG (Directed Acyclic Graph), có thể thêm/bớt/thay đổi thứ tự.

### Tại sao quan trọng cho dự án này

Không phải lúc nào user cũng cần chạy full pipeline:

| Use case | Pipeline cần |
|---|---|
| Chỉ tạo phụ đề | Demux → ASR → Export SRT |
| Chỉ dịch phụ đề có sẵn | Import SRT → Translate → Export SRT |
| Dubbing không dịch (cùng ngôn ngữ) | Demux → ASR → TTS → Mix → Mux |
| Full dubbing | Demux → ASR → Translate → TTS → Mix → Mux |
| Clone giọng (test) | Upload audio → TTS (voice clone mode) |

Nếu pipeline bị hardcode, mỗi use case = 1 luồng code riêng → code trùng lặp, bug ở chỗ này mà chỗ kia không sửa.

### Mô hình đúng

```python
# Pipeline được mô tả bằng config, không phải code
full_dubbing_pipeline = Pipeline([
    Step("demux",     module="media",       plugin="ffmpeg"),
    Step("asr",       module="asr",         plugin="whisperx_local"),
    Step("translate", module="translation", plugin="deepl_api"),
    Step("tts",       module="tts",         plugin="coqui_xtts"),
    Step("mix",       module="audio_post",  plugin="sox"),
    Step("mux",       module="media",       plugin="ffmpeg"),
])

# User chỉ cần phụ đề? Bỏ 3 bước cuối
subtitle_only_pipeline = Pipeline([
    Step("demux", module="media",  plugin="ffmpeg"),
    Step("asr",   module="asr",    plugin="whisperx_local"),
    Step("export_srt", module="export", plugin="srt_formatter"),
])

# Orchestrator chạy bất kỳ pipeline nào theo cùng một cơ chế
orchestrator.execute(full_dubbing_pipeline, project_context)
```

### Vi phạm sẽ gây ra
- Mỗi use case mới = viết lại logic orchestration
- Không thể cho user customize pipeline qua UI
- Khó implement retry/resume cho từng bước riêng lẻ

---

## 6. Fault Isolation & Recovery — Cô Lập Lỗi và Phục Hồi

### Định nghĩa
Khi một bước trong pipeline thất bại (model crash, API timeout, hết VRAM), hệ thống phải:
1. **Cô lập** lỗi — không lan sang bước khác
2. **Lưu checkpoint** — dữ liệu đã xử lý xong không bị mất
3. **Cho phép resume** — chạy lại từ bước lỗi, không phải từ đầu

### Tại sao đặc biệt quan trọng cho dự án này

Hãy tưởng tượng kịch bản: User lồng tiếng video 2 tiếng. Pipeline đã chạy xong:
- ✅ Demux (2 phút)
- ✅ ASR (15 phút)
- ✅ Translate (3 phút)
- ✅ TTS đã tổng hợp 180/200 câu (45 phút)
- ❌ TTS câu 181 — ElevenLabs API trả về 429 (rate limit)

**Nếu không có checkpoint:** Mất 65 phút công việc. User phải chạy lại từ đầu. → User bỏ app.

**Nếu có checkpoint:** Hệ thống lưu trạng thái sau mỗi bước hoàn thành. Resume từ câu 181 sau khi rate limit hết. → User hài lòng.

### Cơ chế cần thiết

```
Pipeline Execution:
  Step 1: Demux    ✅ → checkpoint_1.json (lưu đường dẫn audio/video đã tách)
  Step 2: ASR      ✅ → checkpoint_2.json (lưu toàn bộ transcript)
  Step 3: Translate ✅ → checkpoint_3.json (lưu bản dịch)
  Step 4: TTS      ❌ → checkpoint_4_partial.json (lưu 180/200 câu đã xong)
  
Resume: Đọc checkpoint_4_partial.json → chỉ chạy TTS cho 20 câu còn lại
```

### Vi phạm sẽ gây ra
- User mất hàng giờ công việc khi có lỗi
- Tốn tiền API vô ích (phải gọi lại từ đầu)
- Mất niềm tin hoàn toàn vào sản phẩm

---

## 7. Contract-First Design — Thiết Kế Ưu Tiên Hợp Đồng

### Định nghĩa
Trước khi viết bất kỳ implementation nào, **định nghĩa rõ ràng Data Contract** — cấu trúc dữ liệu vào/ra của mỗi module. Mọi plugin phải tuân thủ contract này.

### Tại sao quan trọng

Khi có 3 plugin ASR (WhisperX, Faster-Whisper, OpenAI API), mỗi cái trả về output khác nhau:
- WhisperX: `{"segments": [{"text": "...", "start": 0.5, "end": 1.2, "words": [...]}]}`
- OpenAI: `{"text": "...", "segments": [{"id": 0, "text": "...", "start": 0.5, "end": 1.2}]}`
- Faster-Whisper: Generator of `Segment(text="...", start=0.5, end=1.2)`

Nếu module Translation phải xử lý 3 format khác nhau → code phình to, bug nhiều.

**Contract-First** đảm bảo: Dù plugin nào, output phải tuân theo 1 schema chuẩn:

```python
@dataclass
class TranscriptionResult:
    segments: list[Segment]
    language: str
    duration: float

@dataclass  
class Segment:
    text: str
    start_time: float
    end_time: float
    words: list[WordTiming] | None  # Optional word-level
    confidence: float
```

**Adapter** trong mỗi plugin chịu trách nhiệm biến đổi output đặc thù → contract chuẩn.

### Vi phạm sẽ gây ra
- Mỗi lần thêm plugin mới phải sửa module ở trên
- Data format inconsistency gây bug ở downstream modules
- Không thể test module độc lập (vì không biết input format chính xác)

---

# PHẦN B — TRIỂN KHAI VẬT LÝ (Physical Deployment)

Triển khai vật lý trả lời câu hỏi: **"Code được đóng gói, chạy trên process/thread nào, dữ liệu nằm ở đâu trên disk?"**

---

## 1. UI Thread Sanctity — Bảo Vệ Tuyệt Đối UI Thread

### Định nghĩa
UI Thread (Main Thread trong PySide6) **CHỈ** được phép:
- Render giao diện
- Nhận sự kiện chuột/bàn phím
- Phát dispatch command
- Nhận event và cập nhật widget

**TUYỆT ĐỐI KHÔNG** được phép:
- Gọi inference AI
- Đọc/ghi file lớn
- Gọi HTTP request
- Chạy bất kỳ logic nào có thể mất > 50ms

### Process Model đề xuất

```
┌─────────────────────────────────────────────────────────┐
│                    MAIN PROCESS                         │
│                                                         │
│  ┌──────────────┐    Signal/Slot    ┌────────────────┐  │
│  │  UI Thread   │ ◄──────────────► │  Event Bus     │  │
│  │  (Main)      │                   │  (QThread)     │  │
│  │              │                   │                │  │
│  │  - Render    │                   │  - Route cmds  │  │
│  │  - User input│                   │  - Route events│  │
│  └──────────────┘                   └───────┬────────┘  │
│                                             │           │
│  ┌──────────────────────────────────────────┼─────────┐ │
│  │           WORKER THREAD POOL             │         │ │
│  │                                          │         │ │
│  │  ┌─────────────┐  ┌─────────────┐       │         │ │
│  │  │ Orchestrator│  │ File I/O    │       │         │ │
│  │  │ (QThread)   │  │ (QThread)   │       │         │ │
│  │  └──────┬──────┘  └─────────────┘       │         │ │
│  │         │                                │         │ │
│  └─────────┼────────────────────────────────┘         │ │
│            │                                           │
└────────────┼───────────────────────────────────────────┘
             │ subprocess / IPC
             ▼
┌────────────────────────┐  ┌────────────────────────┐
│   AI INFERENCE PROCESS │  │   AI INFERENCE PROCESS │
│   (Isolated)           │  │   (Isolated)           │
│                        │  │                        │
│   WhisperX + CUDA      │  │   XTTS v2 + CUDA      │
│   Own Python env       │  │   Own Python env       │
│                        │  │                        │
│   Giao tiếp qua:       │  │   Giao tiếp qua:      │
│   - Local REST API     │  │   - Local REST API     │
│   - gRPC               │  │   - gRPC               │
│   - stdin/stdout pipe  │  │   - stdin/stdout pipe  │
└────────────────────────┘  └────────────────────────┘
```

### Tại sao cần Process riêng cho AI inference (không chỉ Thread)

> [!CAUTION]
> **Python GIL (Global Interpreter Lock)** khiến đa luồng trong Python không thực sự song song cho CPU-bound tasks. AI inference là CPU/GPU-bound — chạy trên QThread vẫn có thể gây jitter cho UI. **Subprocess** là giải pháp an toàn nhất cho các model inference nặng.

Ngoài ra:
- Nếu model crash (segfault từ CUDA), chỉ subprocess chết — app chính vẫn sống
- Mỗi model có thể cần Python environment khác nhau (WhisperX cần torch 2.0, XTTS cần torch 2.1)
- Có thể giới hạn VRAM per-process để tránh OOM

---

## 2. Process Isolation cho AI Models — Cô Lập Tiến Trình

### Định nghĩa
Mỗi AI model **nặng** (WhisperX, XTTS, v.v.) chạy trong process hoặc container riêng, giao tiếp với app chính qua IPC (Inter-Process Communication).

### Tại sao cần thiết

| Vấn đề | Giải pháp bằng Process Isolation |
|---|---|
| **Dependency conflict:** WhisperX cần `numpy==1.24`, XTTS cần `numpy==1.26` | Mỗi process có Python env riêng |
| **VRAM management:** 2 model cùng load = OOM | Orchestrator quyết định load/unload per-process |
| **Crash containment:** CUDA segfault trong Whisper | Chỉ subprocess chết, app chính bắt lỗi và thông báo user |
| **Scalability:** Muốn chạy trên remote GPU server sau này | Đổi IPC từ local socket → remote gRPC, không sửa app chính |

### Cơ chế giao tiếp đề xuất

```
App chính                              AI Subprocess
─────────                              ─────────────
    │                                       │
    ├─── HTTP POST /transcribe ───────────► │
    │    {"audio": "path/to/file.wav",      │
    │     "language": "vi"}                 │
    │                                       ├── Load model (nếu chưa)
    │                                       ├── Inference...
    │ ◄── SSE: progress 30% ────────────────┤
    │ ◄── SSE: progress 70% ────────────────┤
    │ ◄── HTTP 200: result ─────────────────┤
    │    {"segments": [...]}                │
```

> [!TIP]
> **Dùng Local HTTP server** (FastAPI/Flask chạy trên localhost) là giải pháp đơn giản nhất cho IPC. Dễ debug (có thể test bằng curl/Postman), dễ monitor, và dễ chuyển sang remote server sau này.

---

## 3. Resource-Aware Scheduling — Lập Lịch Theo Tài Nguyên

### Định nghĩa
Orchestrator phải **biết** tài nguyên hiện có (free VRAM, free RAM, GPU utilization) trước khi quyết định chạy task tiếp theo.

### Tại sao bắt buộc cho desktop chạy AI

Trên server, có thể scale up bằng thêm GPU. Trên desktop user, **chỉ có 1 GPU, thường 8-12GB VRAM**:

| Model | VRAM cần | Ghi chú |
|---|---|---|
| WhisperX large-v3 | ~3.5 GB | Cần giữ trong VRAM suốt quá trình ASR |
| XTTS v2 | ~2.5 GB | Cần load per TTS session |
| Tổng cộng | ~6 GB | Chưa tính OS + display driver (~1-2 GB) |

Nếu 2 model load đồng thời trên GPU 8GB → OOM → crash.

**Resource Manager** phải:
1. Query VRAM hiện tại (qua `nvidia-smi` hoặc `pynvml`)
2. Biết mỗi model cần bao nhiêu VRAM
3. Ra lệnh **unload** WhisperX trước khi **load** XTTS
4. Queue task nếu không đủ tài nguyên

### Vi phạm sẽ gây ra
- CUDA Out of Memory → app crash
- Máy user bị chiếm hết RAM → cả hệ thống chậm
- Không thể chạy trên máy GPU yếu (6GB VRAM)

---

## 4. Environment Isolation — Cô Lập Môi Trường

### Định nghĩa
App chính, mỗi local AI plugin, và các thư viện hệ thống (FFmpeg, Sox) có **môi trường chạy tách biệt** — tránh conflict dependency.

### Chiến lược đề xuất

```
auto_dubbing_system/
├── app/                          ← App chính (PySide6, orchestrator, UI)
│   └── venv/                     ← Python venv cho app chính (nhẹ, không có torch)
│
├── services/
│   ├── whisperx/
│   │   └── venv/                 ← Isolated venv: torch + whisperx + CUDA
│   │   └── server.py             ← FastAPI server, chạy như subprocess
│   │
│   └── xtts/
│       └── venv/                 ← Isolated venv: torch + TTS + CUDA
│       └── server.py             ← FastAPI server, chạy như subprocess
│
├── tools/
│   ├── ffmpeg.exe                ← Binary, không cần Python
│   └── sox.exe                   ← Binary, không cần Python
```

### Tại sao Docker cho desktop user?

> [!WARNING]
> **Docker KHÔNG phải lựa chọn tốt cho end-user desktop app.** Yêu cầu user cài Docker Desktop trên Windows là rào cản lớn (cần Hyper-V/WSL2, ~4GB RAM overhead, phức tạp khi setup GPU passthrough). **Isolated venv + subprocess** là giải pháp thực tế hơn cho desktop distribution.
>
> Docker chỉ nên dùng cho development/CI environment, không phải production deployment cho end-user.

---

## 5. Data Locality & Checkpoint — Dữ Liệu Cục Bộ và Điểm Kiểm Tra

### Định nghĩa
Mọi dữ liệu trung gian được lưu trên disk theo cấu trúc rõ ràng, cho phép resume pipeline từ bất kỳ bước nào.

### Cấu trúc project folder đề xuất

```
storage/projects/project_001/
├── metadata.json                 ← Trạng thái pipeline, timestamps, config
├── input/
│   └── original_video.mp4
├── intermediate/
│   ├── step_01_demux/
│   │   ├── vocal.wav
│   │   ├── background.wav
│   │   └── status.json           ← {"completed": true, "duration_sec": 12.5}
│   ├── step_02_asr/
│   │   ├── transcript.json
│   │   └── status.json
│   ├── step_03_translate/
│   │   ├── translated.json
│   │   └── status.json
│   └── step_04_tts/
│       ├── segments/
│       │   ├── seg_001.wav       ← Mỗi câu 1 file → resume granularity cao
│       │   ├── seg_002.wav
│       │   └── ...
│       └── status.json           ← {"completed_segments": 180, "total": 200}
├── output/
│   └── dubbed_video.mp4
└── logs/
    └── pipeline.log              ← Structured log cho debug
```

### Tại sao cấu trúc này

1. **Resume granularity:** TTS lỗi ở câu 181 → chỉ chạy lại từ câu 181 (vì 180 file .wav đã có)
2. **Debug transparency:** Mở folder intermediate, xem từng bước đã output gì → debug bằng mắt
3. **User inspection:** User có thể mở transcript.json, sửa text sai trước khi chạy TTS
4. **Backup/share:** Copy folder project = copy toàn bộ trạng thái

---

## 6. Packaging & Distribution — Đóng Gói và Phân Phối

### Thách thức đặc thù

Desktop app Python + AI models = **bài toán đóng gói phức tạp nhất** trong thế giới Python:

| Thành phần | Kích thước | Ghi chú |
|---|---|---|
| App chính (PySide6 + logic) | ~150 MB | PyInstaller bundle |
| PyTorch + CUDA runtime | ~2-3 GB | Cần GPU-specific build |
| WhisperX model weights | ~3 GB | Download lần đầu |
| XTTS model weights | ~2 GB | Download lần đầu |
| FFmpeg binary | ~80 MB | Bundled |

### Chiến lược đề xuất

```
Installer (NSIS/Inno Setup):
  1. Cài app chính (~200 MB)           ← Cài nhanh, dùng được ngay (cloud API mode)
  2. First-run wizard:
     - "Bạn có muốn cài WhisperX local?" → Download venv + model (~5 GB)
     - "Bạn có muốn cài XTTS local?"     → Download venv + model (~4 GB)
     - "Hay dùng Cloud API?"              → Chỉ cần API key, không cài gì thêm
```

> [!TIP]
> **Chiến lược "Core nhẹ + Plugin nặng tải sau"** là cách duy nhất khả thi. Installer 10+ GB = user không bao giờ tải. Installer 200 MB + tải plugin theo nhu cầu = trải nghiệm tốt hơn nhiều.

---

# PHẦN C — MA TRẬN ƯU TIÊN TỔNG HỢP

| # | Tính chất | Loại | Mức ưu tiên | Lý do |
|---|---|---|---|---|
| 1 | UI Thread Sanctity | Vật lý | 🔴 **BẮT BUỘC** | Vi phạm = app đơ = user bỏ |
| 2 | Event-Driven Reactivity | Logic | 🔴 **BẮT BUỘC** | Cơ chế duy nhất đảm bảo #1 |
| 3 | Dependency Inversion | Logic | 🔴 **BẮT BUỘC** | Không có = không thể swap model |
| 4 | Contract-First Design | Logic | 🔴 **BẮT BUỘC** | Nền tảng cho #3 hoạt động |
| 5 | Separation of Concerns | Logic | 🔴 **BẮT BUỘC** | Vi phạm = unmaintainable sau 3 tháng |
| 6 | Fault Isolation & Recovery | Logic | 🟡 **RẤT NÊN CÓ** | Thiếu = trải nghiệm user kém |
| 7 | Centralized State | Logic | 🟡 **RẤT NÊN CÓ** | Thiếu = bug state inconsistency |
| 8 | Pipeline Composability | Logic | 🟡 **RẤT NÊN CÓ** | Thiếu = khó mở rộng use case |
| 9 | Process Isolation (AI) | Vật lý | 🟡 **RẤT NÊN CÓ** | Thiếu = CUDA crash = app crash |
| 10 | Resource-Aware Scheduling | Vật lý | 🟡 **RẤT NÊN CÓ** | Thiếu = OOM trên GPU yếu |
| 11 | Data Locality & Checkpoint | Vật lý | 🟡 **RẤT NÊN CÓ** | Thiếu = mất data khi lỗi |
| 12 | Environment Isolation | Vật lý | 🟢 Nên có | v1 có thể dùng chung venv nếu deps không conflict |
| 13 | Lightweight Packaging | Vật lý | 🟢 Nên có | v1 có thể yêu cầu user cài deps thủ công |

> [!IMPORTANT]
> **5 tính chất đầu tiên (🔴) là nền tảng không thể thỏa hiệp.** Nếu thiếu bất kỳ tính chất nào trong 5 này, hệ thống sẽ gặp vấn đề nghiêm trọng sớm hay muộn — bất kể code có sạch đến đâu.

---

*Phân tích bởi chuyên gia thiết kế hệ thống desktop — dựa trên kinh nghiệm thực tế với các ứng dụng AI desktop phức tạp.*
