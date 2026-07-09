# Product Configuration — Video Dubbing Desktop Application

> Tài liệu này là **Product Configuration** cho ứng dụng lồng tiếng video (Video Dubbing). Nó bổ sung cho [Reference Architecture](./reference_architecture.md) bằng cách điền các thông tin **đặc thù domain** — pipeline cụ thể, model AI, data contracts, và use cases.
>
> Mọi nguyên tắc kiến trúc, patterns, và mechanisms áp dụng đều nằm trong Reference Architecture. Tài liệu này **chỉ chứa phần variable** (thay đổi) — phần invariant (bất biến) xem tại Reference Architecture.

---

## Bảng Thuật Ngữ Domain

> [!NOTE]
> Bổ sung cho [Bảng Thuật Ngữ Tổng Hợp](./reference_architecture.md#bảng-thuật-ngữ-tổng-hợp) trong Reference Architecture.

| Thuật ngữ | Giải nghĩa dễ hiểu |
|---|---|
| **ASR (Automatic Speech Recognition)** | **Nhận dạng giọng nói tự động** — model AI "nghe" file audio và viết ra văn bản kèm mốc thời gian |
| **TTS (Text-to-Speech)** | **Chuyển văn bản thành giọng nói** — model AI đọc văn bản thành file audio, có thể sao chép giọng gốc (voice cloning) |
| **Demux (De-multiplex)** | **Tách luồng** — tách video thành các thành phần riêng: hình ảnh, giọng nói (vocal), nhạc nền (background) |
| **Mux (Multiplex)** | **Ghép luồng** — ghép audio mới với video gốc thành video hoàn chỉnh |
| **Sox (Sound eXchange)** | Công cụ dòng lệnh chuyên xử lý âm thanh (cắt, nối, trộn, chuyển đổi format). Tương tự FFmpeg nhưng **chỉ chuyên về audio** |
| **FFmpeg** | Công cụ dòng lệnh **đa năng** xử lý cả video lẫn audio. Dùng cho demux (tách), mux (ghép), chuyển đổi format, cắt ghép video |
| **Voice Cloning** | **Sao chép giọng nói** — model AI học giọng nói từ mẫu audio, sau đó đọc bất kỳ văn bản nào bằng giọng đã học |
| **Time-stretching** | **Giãn/nén thời lượng** — thay đổi tốc độ đọc mà không thay đổi cao độ (pitch) |
| **Speaker Diarization** | **Phân biệt người nói** — xác định "ai nói câu nào" trong audio có nhiều người nói |

---

## Bối Cảnh Sản Phẩm

### Mô tả sản phẩm
Ứng dụng Windows Desktop bằng Python, giúp user **lồng tiếng video tự động** từ ngôn ngữ nguồn sang ngôn ngữ đích, sử dụng AI inference nặng cho các bước nhận dạng giọng nói, dịch thuật, và tổng hợp giọng nói.

### Đối tượng người dùng
- **Đối tượng 1:** Chỉ có 1 GPU — biên tập viên video, YouTuber, người dịch thuật
- **Đối tượng 2:** Nhiều GPU trong LAN — studio dịch thuật, công ty sản xuất nội dung

### Thời gian xử lý điển hình (context cho Performance Targets)

| Tác vụ | Thời gian điển hình |
|---|---|
| Load model WhisperX vào GPU (VRAM) | 15-45 giây |
| Nhận dạng giọng nói (ASR) cho 10 phút audio | 30-120 giây |
| Tổng hợp giọng nói (TTS) cho 100 câu | 5-15 phút |
| Tách/ghép video 4K bằng FFmpeg | 10-60 giây |

---

## Pipeline Lồng Tiếng — Định Nghĩa Các Bước

Toàn bộ quy trình lồng tiếng video đi qua **6 bước chính**, mỗi bước có tên viết tắt từ thuật ngữ tiếng Anh:

```
 VIDEO GỐC                                                              VIDEO ĐÃ LỒNG TIẾNG
     │                                                                         ▲
     ▼                                                                         │
 ┌────────┐    ┌────────┐    ┌───────────┐    ┌────────┐    ┌────────┐    ┌────────┐
 │ DEMUX  │───►│  ASR   │───►│ TRANSLATE │───►│  TTS   │───►│  MIX   │───►│  MUX   │
 │        │    │        │    │           │    │        │    │        │    │        │
 │ Tách   │    │ Nghe & │    │   Dịch    │    │ Đọc    │    │ Trộn   │    │ Ghép   │
 │ âm     │    │ viết   │    │  thuật    │    │ thành  │    │ âm     │    │ lại    │
 │ thanh  │    │ thành  │    │           │    │ tiếng  │    │ thanh  │    │ video  │
 │ ra     │    │ chữ    │    │           │    │        │    │        │    │        │
 └────────┘    └────────┘    └───────────┘    └────────┘    └────────┘    └────────┘
```

| Bước | Tên đầy đủ | Ý nghĩa | Ví dụ cụ thể |
|---|---|---|---|
| **Demux** | **De-multiplex** (Tách luồng) | Tách video gốc thành: luồng hình ảnh, giọng nói (vocal), nhạc nền/tiếng động (background) | Video YouTube 10 phút → `video_only.mp4` + `vocal.wav` + `background.wav` |
| **ASR** | **Automatic Speech Recognition** | Đưa file giọng nói vào model AI để "nghe" và viết ra văn bản, kèm mốc thời gian chính xác | `vocal.wav` → "Xin chào các bạn" (0:00-0:02), "Hôm nay chúng ta..." (0:02-0:05) |
| **Translate** | **Machine Translation** | Dịch văn bản đã bóc băng sang ngôn ngữ đích | "Xin chào các bạn" → "Hello everyone" |
| **TTS** | **Text-to-Speech** | Model AI đọc văn bản đã dịch thành giọng nói, có thể sao chép giọng gốc (voice cloning) | "Hello everyone" → file `segment_001.wav` |
| **Mix** | **Audio Mixing** | Trộn giọng đọc mới với nhạc nền/tiếng động. Điều chỉnh tốc độ đọc cho khớp (time-stretching) | `segment_001.wav` + `background.wav` → `mixed_audio.wav` |
| **Mux** | **Multiplex** (Ghép luồng) | Ghép luồng âm thanh mới với luồng hình ảnh gốc thành video hoàn chỉnh | `video_only.mp4` + `mixed_audio.wav` → `dubbed_video.mp4` |

### DAG cụ thể cho Full Dubbing

```
  ┌────────┐
  │ Demux  │ ← Bắt đầu: tách video
  └───┬────┘
      │ tạo ra vocal.wav + background.wav
      ▼
  ┌────────┐
  │  ASR   │ ← Nghe và viết thành chữ
  └───┬────┘
      │ tạo ra transcript
      ▼
  ┌───────────┐
  │ Translate │ ← Dịch sang ngôn ngữ khác
  └─────┬─────┘
        │ tạo ra bản dịch
        ▼
  ┌────────┐
  │  TTS   │ ← Đọc bản dịch thành giọng mới
  └───┬────┘
      │ tạo ra audio segments
      ├──────────────────┐
      ▼                  ▼
  ┌────────┐        ┌────────┐
  │  Mix   │◄───────│ (lấy   │ ← Kết hợp giọng mới + nhạc nền từ Demux
  │        │        │ bg từ  │
  └───┬────┘        │ Demux) │
      │              └────────┘
      ▼
  ┌────────┐
  │  Mux   │ ← Ghép audio mới vào video gốc → VIDEO HOÀN THÀNH
  └────────┘
```

### Use Cases & Pipeline Variants

Không phải lúc nào user cũng cần chạy full pipeline:

| Use case | Pipeline cần |
|---|---|
| Chỉ tạo phụ đề | Demux → ASR → Export SRT |
| Chỉ dịch phụ đề có sẵn | Import SRT → Translate → Export SRT |
| Dubbing không dịch (cùng ngôn ngữ) | Demux → ASR → TTS → Mix → Mux |
| Full dubbing | Demux → ASR → Translate → TTS → Mix → Mux |
| Clone giọng (test) | Upload audio → TTS (voice clone mode) |

### Pipeline Config (theo pattern từ Reference Architecture)

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

---

## Bảng Công Nghệ / Model / API Cho Từng Module

### 🎤 Module ASR (Nhận dạng giọng nói → chữ viết)

| Công nghệ | Loại | Đặc điểm | Trạng thái |
|---|---|---|---|
| **WhisperX** | 🖥️ Local Model | Nhanh, word-level timestamp, speaker diarization | Phổ biến 2023-2024 |
| **Faster-Whisper** | 🖥️ Local Model | Nhanh gấp 4x Whisper gốc, tiết kiệm VRAM | Đang lên 2024+ |
| **Distil-Whisper** | 🖥️ Local Model | Nhẹ gấp 6x, tốc độ cực cao, chất lượng giảm nhẹ | Mới 2024 |
| **OpenAI Whisper API** | ☁️ Cloud API | Chất lượng cao, dễ dùng, tính phí theo phút audio | Ổn định |
| **Google Cloud Speech-to-Text** | ☁️ Cloud API | Hỗ trợ 125+ ngôn ngữ, streaming | Ổn định |
| **AssemblyAI** | ☁️ Cloud API | Chuyên nghiệp, speaker diarization tốt | Ổn định |
| **Deepgram** | ☁️ Cloud API | Cực nhanh, real-time, giá cạnh tranh | Đang lên |

### 🌐 Module Translation (Dịch thuật)

| Công nghệ | Loại | Đặc điểm | Trạng thái |
|---|---|---|---|
| **DeepL API** | ☁️ Cloud API | Chất lượng dịch tốt nhất, đặc biệt Châu Âu | Ổn định |
| **Google Translate API** | ☁️ Cloud API | Hỗ trợ nhiều ngôn ngữ nhất (130+) | Ổn định |
| **OpenAI GPT API** (dùng cho dịch) | ☁️ Cloud API | Dịch ngữ cảnh tốt, hiểu context phức tạp | Phổ biến |
| **Meta NLLB (No Language Left Behind)** | 🖥️ Local Model | Miễn phí, hỗ trợ 200+ ngôn ngữ, chạy local | Open-source |
| **MarianMT (Helsinki NLP)** | 🖥️ Local Model | Nhẹ, nhanh, nhiều cặp ngôn ngữ, chạy trên CPU được | Open-source |
| **Anthropic Claude API** (dùng cho dịch) | ☁️ Cloud API | Dịch văn phong tự nhiên, hiểu ngữ cảnh sâu | Mới |

### 🔊 Module TTS (Chuyển chữ → giọng nói)

| Công nghệ | Loại | Đặc điểm | Trạng thái |
|---|---|---|---|
| **Coqui XTTS v2** | 🖥️ Local Model | Voice cloning, đa ngôn ngữ, miễn phí | Open-source 2024 |
| **F5-TTS** | 🖥️ Local Model | Chất lượng rất cao, voice cloning thế hệ mới | Mới 2024+ |
| **Bark (Suno)** | 🖥️ Local Model | Tạo giọng + hiệu ứng (cười, thở, nhạc nền) | Open-source |
| **ElevenLabs API** | ☁️ Cloud API | Voice cloning tốt nhất, chất lượng studio | Ổn định, tốn phí |
| **OpenAI TTS API** | ☁️ Cloud API | Đơn giản, chất lượng tốt, ít giọng | Ổn định |
| **Google Cloud TTS** | ☁️ Cloud API | WaveNet voices, nhiều ngôn ngữ | Ổn định |
| **Microsoft Azure TTS** | ☁️ Cloud API | Neural voices, SSML support tốt | Ổn định |
| **Fish Speech** | 🖥️ Local Model | Open-source, voice cloning, đa ngôn ngữ | Mới 2024+ |

### 🎬 Module Media (Demux/Mux) & Audio Post-processing (Mix)

| Công nghệ | Loại | Đặc điểm | Trạng thái |
|---|---|---|---|
| **FFmpeg** | 🔧 Tool/Binary | Đa năng: tách/ghép video+audio, chuyển format | Tiêu chuẩn |
| **Sox (Sound eXchange)** | 🔧 Tool/Binary | Chuyên audio: trộn, cắt, nối, lọc tiếng ồn | Ổn định |
| **Demucs (Meta)** | 🖥️ Local Model | Tách giọng hát khỏi nhạc nền bằng AI (vocal separation) | AI-powered |
| **Spleeter (Deezer)** | 🖥️ Local Model | Tách nhạc thành stems (vocal, drums, bass...) | Open-source |
| **Rubberband** | 🔧 Library | Time-stretching và pitch-shifting chất lượng cao | Ổn định |
| **pyrubberband** | 🐍 Python lib | Python wrapper cho Rubberband | Ổn định |

---

## VRAM Requirements (Yêu cầu bộ nhớ GPU)

| Model | VRAM cần | RAM cần | Ghi chú |
|---|---|---|---|
| WhisperX (Large-v3) | ~3.5 GB | ~4 GB | ASR chính, chất lượng cao nhất |
| Faster-Whisper (Large-v3) | ~3 GB | ~3 GB | ASR thay thế, nhanh hơn |
| Coqui XTTS v2 | ~2.5 GB | ~3 GB | TTS chính, voice cloning |
| F5-TTS | ~3 GB | ~4 GB | TTS thay thế, chất lượng mới hơn |
| Demucs (htdemucs) | ~1.5 GB | ~2 GB | Vocal separation |
| MarianMT | ~0.5 GB | ~1 GB | Translation local (nhẹ) |
| **Tổng peak (chạy đồng thời ASR + TTS)** | **~6 GB** | **~7 GB** | **GPU tối thiểu khuyến nghị: 8 GB VRAM** |

---

## Data Contracts — Domain-Specific

### ASR Contract: TranscriptionResult

```python
from dataclasses import dataclass

@dataclass
class Segment:
    """Một đoạn phát biểu liên tục của người nói."""
    start_time: float           # Giây bắt đầu (0.0, 2.5, ...)
    end_time: float             # Giây kết thúc
    text: str                   # Nội dung đoạn nói
    speaker_id: str | None      # ID người nói (nếu có diarization)
    confidence: float           # Độ tin cậy (0.0 - 1.0)
    words: list[WordTiming]     # Thời gian từng từ (nếu model hỗ trợ)

@dataclass
class TranscriptionResult:
    """
    Contract chuẩn cho output ASR.
    BẤT KỲ plugin ASR nào (WhisperX, Faster-Whisper, OpenAI API...)
    đều phải trả về TranscriptionResult đúng format này.
    """
    language: str               # Ngôn ngữ phát hiện được ("vi", "en", "ja")
    segments: list[Segment]     # Danh sách các đoạn kèm timestamp
    full_text: str              # Toàn bộ transcript ghép lại
    duration_seconds: float     # Tổng thời lượng audio đã xử lý
    model_name: str             # Tên model đã dùng ("whisperx_large_v3")
```

> [!IMPORTANT]
> **Mọi plugin ASR** (WhisperX, Faster-Whisper, OpenAI API, Google API...) đều phải trả về `TranscriptionResult`. Adapter trong mỗi plugin chịu trách nhiệm biến đổi output đặc thù → format chuẩn này.

### Dependency Inversion — Ví dụ cụ thể cho module ASR

```python
# modules/asr/asr_engine.py — INTERFACE
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
        raw_result = whisperx.transcribe(audio_path, language=language)
        return TranscriptionResult(
            language=raw_result["language"],
            segments=[Segment(s["start"], s["end"], s["text"], ...) for s in raw_result["segments"]],
            ...
        )

# plugins/asr/faster_whisper/adapter.py — THÊM MỚI, KHÔNG SỬA GÌ Ở CORE
class FasterWhisperAdapter(ASREngine):
    def transcribe(self, audio_path, language):
        # Gọi Faster-Whisper, biến đổi output thành TranscriptionResult chuẩn
        ...
```

---

## Separation of Concerns — 5 Miền Trách Nhiệm Cụ Thể

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

---

## Event-Driven — Ví Dụ Worker Cụ Thể Cho ASR

```python
class ASRWorker(QObject):
    """Worker xử lý nhận dạng giọng nói — chạy trên thread riêng."""

    progress = Signal(int, str)
    completed = Signal(object)         # Emit TranscriptionResult
    error = Signal(str)

    def __init__(self, audio_path: str, plugin_name: str):
        super().__init__()
        self.audio_path = audio_path
        self.plugin_name = plugin_name   # "whisperx_local" hoặc "openai_api"

    @Slot()
    def run(self):
        try:
            self.progress.emit(10, "Đang khởi tạo model...")
            plugin = PluginRegistry.get_asr_plugin(self.plugin_name)

            self.progress.emit(30, "Đang nhận dạng giọng nói...")
            result = plugin.transcribe(self.audio_path, language="vi")

            self.progress.emit(100, "Hoàn thành!")
            self.completed.emit(result)

        except Exception as e:
            self.error.emit(f"Lỗi nhận dạng giọng nói: {str(e)}")
```

---

## Centralized State — Domain-Specific Fields

```python
class GlobalStore(QObject):
    """Bổ sung vào GlobalStore pattern (xem Reference Architecture)."""

    # ── Domain-specific Signals ──
    voice_list_changed = Signal(list)
    selected_asr_plugin = Signal(str)
    selected_tts_plugin = Signal(str)

    def __init__(self):
        super().__init__()
        # ── Domain-specific State ──
        self._voices = []
        self._plugin_config = {
            "asr": "whisperx_local",
            "tts": "coqui_xtts",
            "translation": "deepl_api",
        }
```

---

## Fault Isolation — Kịch Bản Cụ Thể

Kịch bản: User lồng tiếng video 2 tiếng. Pipeline đã chạy xong:

- ✅ Demux — tách audio (2 phút)
- ✅ ASR — nhận dạng giọng nói (15 phút)
- ✅ Translate — dịch thuật (3 phút)
- ✅ TTS đã tổng hợp 180/200 câu (45 phút)
- ❌ TTS câu 181 — ElevenLabs API trả về lỗi 429 (quá giới hạn gọi API)

**Nếu không có checkpoint:** Mất 65 phút công việc. User phải chạy lại từ đầu. → User bỏ app.

**Nếu có checkpoint:** Resume từ câu 181 sau khi rate limit hết. → User hài lòng.

```
Pipeline Execution (Dubbing):
  Step 1: Demux    ✅ → checkpoint_1.json (lưu đường dẫn audio/video đã tách)
  Step 2: ASR      ✅ → checkpoint_2.json (lưu toàn bộ transcript)
  Step 3: Translate ✅ → checkpoint_3.json (lưu bản dịch)
  Step 4: TTS      ❌ → checkpoint_4_partial.json (lưu 180/200 câu đã xong)
  
Resume: Đọc checkpoint_4_partial.json → chỉ chạy TTS cho 20 câu còn lại
```

---

## Data Locality — Project Folder Cụ Thể

```
storage/projects/{project_id}/
├── metadata.json                 ← Trạng thái pipeline, timestamps, config
├── input/
│   └── original_video.mp4
├── intermediate/
│   ├── step_01_demux/
│   │   ├── video_only.mp4
│   │   ├── vocal.wav
│   │   ├── background.wav
│   │   └── status.json           ← {"completed": true, "duration_sec": 12.5}
│   ├── step_02_asr/
│   │   ├── transcript.json       ← TranscriptionResult serialized
│   │   ├── transcript.srt        ← SRT format cho user preview
│   │   └── status.json
│   ├── step_03_translate/
│   │   ├── translation.json
│   │   └── status.json
│   ├── step_04_tts/
│   │   ├── segment_001.wav
│   │   ├── segment_002.wav
│   │   ├── ...
│   │   └── status.json           ← {"completed_items": 180, "total": 200}
│   ├── step_05_mix/
│   │   ├── mixed_audio.wav
│   │   └── status.json
│   └── step_06_mux/
│       └── status.json
├── output/
│   └── dubbed_video.mp4
└── logs/
    └── pipeline.log
```

---

## Packaging — Kích Thước Cụ Thể

| Thành phần | Kích thước | Ghi chú |
|---|---|---|
| App chính (PySide6 + logic) | ~150 MB | PyInstaller bundle |
| PyTorch + CUDA runtime | ~2-3 GB | Cần GPU-specific build |
| WhisperX model (Large-v3) | ~3 GB | Download lần đầu |
| XTTS v2 model | ~2 GB | Download lần đầu |
| Demucs model | ~800 MB | Download lần đầu |
| FFmpeg binary | ~80 MB | Đi kèm installer |
| Sox binary | ~5 MB | Đi kèm installer |
| **Tổng (full local)** | **~9-10 GB** | **Cài dần theo nhu cầu** |

---

## License — Feature Tiers Cụ Thể

> [!NOTE]
> Cơ chế license và pattern LicenseManager xem tại [Reference Architecture — Phần C](./reference_architecture.md#phần-c--hệ-thống-kiểm-tra-bản-quyền-license).

| Feature | Free | Pro | Enterprise |
|---|---|---|---|
| Số video/tháng | 3 | Unlimited | Unlimited |
| Thời lượng video | Max 5 phút | Max 2 giờ | Unlimited |
| ASR models | WhisperX (base) | WhisperX (large), Faster-Whisper | All + custom |
| TTS models | OpenAI TTS (6 giọng) | XTTS v2 (voice clone), F5-TTS | All + custom |
| Translation | Google Translate | DeepL, GPT | All + custom |
| Cloud API integration | ❌ | ✅ | ✅ |
| Multi-GPU LAN | ❌ | ❌ | ✅ |
| Batch processing | ❌ | ✅ | ✅ |
| Priority support | ❌ | Email | Dedicated |

---

*Product Configuration cho Video Dubbing Desktop Application — bổ sung cho [Reference Architecture](./reference_architecture.md).*
