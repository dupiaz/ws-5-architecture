# Các Tính Chất Kiến Trúc Bắt Buộc — Góc Nhìn Chuyên Gia Thiết Kế Hệ Thống Desktop

> Tài liệu này phân tích **tại sao** mỗi tính chất kiến trúc là cần thiết, dưới lăng kính đặc thù của một ứng dụng **Windows Desktop bằng Python** chạy **AI inference nặng** cho quy trình lồng tiếng video.

---

## Bảng Thuật Ngữ Tổng Hợp

> [!NOTE]
> Bảng này giải nghĩa các thuật ngữ kỹ thuật xuất hiện trong tài liệu, giúp người mới dễ theo dõi. Có thể quay lại tra cứu bất kỳ lúc nào.

| Thuật ngữ | Giải nghĩa dễ hiểu |
|---|---|
| **Inference (Suy luận)** | Quá trình **chạy một model AI để cho ra kết quả**. Ví dụ: đưa file âm thanh vào model Whisper để nó "nghe" và cho ra văn bản — đó là inference. Khác với Training (huấn luyện) là quá trình dạy model. Inference nặng vì model phải xử lý hàng triệu phép tính toán học trên GPU |
| **Dispatch (Phát lệnh)** | Hành động **gửi một yêu cầu đi** mà **không chờ kết quả trả về**. Giống như gửi tin nhắn rồi đi làm việc khác, thay vì gọi điện và phải đứng chờ người ta trả lời. Trong app: UI gửi lệnh "bắt đầu bóc băng" rồi tiếp tục hoạt động bình thường |
| **DAG (Directed Acyclic Graph)** | **Đồ thị có hướng không tuần hoàn** — một sơ đồ mô tả các bước công việc theo thứ tự, trong đó mỗi bước chỉ đi tới (không quay lại). Giải thích chi tiết ở [Mục A.5](#5-pipeline-composability--khả-năng-tổ-hợp-pipeline) |
| **IPC (Inter-Process Communication)** | **Giao tiếp liên tiến trình** — cơ chế để 2 chương trình đang chạy riêng biệt nói chuyện với nhau. Ví dụ: app chính gửi file audio cho chương trình WhisperX (đang chạy riêng) để xử lý, rồi WhisperX gửi kết quả trả lại. Các cách IPC phổ biến: gọi HTTP qua localhost, gRPC, pipe (đường ống stdin/stdout), shared memory |
| **Segfault (Segmentation Fault)** | **Lỗi truy cập bộ nhớ trái phép** — khi chương trình cố đọc/ghi vào vùng bộ nhớ không thuộc về nó. Thường xảy ra trong code C/C++ bên trong các thư viện AI (PyTorch, CUDA). Khi segfault xảy ra, chương trình bị hệ điều hành **ép buộc tắt ngay lập tức** mà không kịp xử lý lỗi (try/catch không bắt được) |
| **GIL (Global Interpreter Lock)** | **Khóa toàn cục của Python** — cơ chế trong Python chỉ cho phép **1 thread chạy Python code tại 1 thời điểm**, kể cả trên máy nhiều lõi CPU. Giải thích chi tiết ở [Mục B.1](#1-ui-thread-sanctity--bảo-vệ-tuyệt-đối-ui-thread) |
| **State (Trạng thái)** | **Dữ liệu hiện tại** mà ứng dụng đang giữ trong bộ nhớ. Ví dụ: project đang mở tên gì, pipeline đang chạy bước nào, user đã chọn giọng đọc nào, API key là gì... Tất cả gộp lại gọi là "state" của ứng dụng |
| **Event Bus (Xe buýt sự kiện)** | **Kênh giao tiếp trung tâm** — giống như một "bảng thông báo" chung. Ai muốn thông báo gì thì "dán lên bảng" (publish). Ai quan tâm thì "đăng ký theo dõi" (subscribe). Không ai cần biết ai đang đăng ký |
| **Adapter (Bộ chuyển đổi)** | **Lớp trung gian chuyển đổi định dạng**. Giống như ổ cắm điện chuyển đổi 3 chân sang 2 chân — ổ cắm bên trong (plugin AI) khác format, adapter biến đổi cho khớp với format chuẩn của hệ thống |
| **Interface / Contract (Giao diện / Hợp đồng)** | **Bản cam kết** về hình dạng dữ liệu vào/ra. Ví dụ: "Bất kỳ plugin ASR nào cũng phải nhận vào file audio và trả ra danh sách câu kèm timestamp." Plugin nào cũng phải tuân thủ — giống hợp đồng pháp lý |
| **Plugin** | **Thành phần cắm-rút** — một module có thể thêm/bớt/thay thế mà không ảnh hưởng phần còn lại. Mỗi AI model/API là một plugin |
| **Pipeline** | **Dây chuyền xử lý** — chuỗi các bước nối tiếp nhau. Giống dây chuyền lắp ráp trong nhà máy: mỗi trạm làm 1 việc, sản phẩm đi qua lần lượt |
| **Checkpoint** | **Điểm lưu trạng thái** — giống như save game. Nếu có lỗi, có thể quay lại checkpoint gần nhất thay vì chơi lại từ đầu |
| **Thread (Luồng)** | **Một nhánh thực thi trong cùng 1 chương trình**. 1 chương trình có thể có nhiều thread chạy đồng thời: 1 thread vẽ giao diện, 1 thread xử lý file |
| **Process (Tiến trình)** | **Một chương trình đang chạy hoàn toàn riêng biệt**, có bộ nhớ riêng. Khác thread ở chỗ: 2 thread dùng chung bộ nhớ, 2 process thì không |
| **VRAM** | **Video RAM** — bộ nhớ trên card đồ họa (GPU). AI model cần load trọng số (weights) vào VRAM để chạy inference. GPU 8GB VRAM = chỉ chứa được ~6GB model (trừ OS dùng) |
| **OOM (Out of Memory)** | **Hết bộ nhớ** — khi chương trình cố dùng nhiều RAM/VRAM hơn mức có sẵn → crash |
| **State-of-the-art** | **Tiên tiến nhất tại thời điểm đó** — công nghệ/model đạt kết quả tốt nhất so với mọi giải pháp khác đang tồn tại |
| **Orchestrator (Bộ điều phối)** | **Nhạc trưởng** của hệ thống — quyết định bước nào chạy trước, bước nào chạy sau, phân bổ tài nguyên, xử lý lỗi |
| **SSE (Server-Sent Events)** | Cơ chế server **liên tục gửi cập nhật** cho client qua 1 kết nối HTTP. Dùng để báo tiến độ (30%... 50%... 100%) |
| **Sox** | **Sound eXchange** — công cụ dòng lệnh chuyên xử lý âm thanh (cắt, nối, trộn, chuyển đổi format). Tương tự FFmpeg nhưng **chỉ chuyên về audio** (không xử lý video). Nhẹ hơn FFmpeg, có một số bộ lọc âm thanh chuyên biệt hơn |
| **FFmpeg** | Công cụ dòng lệnh **đa năng** xử lý cả video lẫn audio. Dùng cho demux (tách), mux (ghép), chuyển đổi format, cắt ghép video |
| **REST API** | **Giao tiếp qua HTTP** — gửi request (yêu cầu) đến một URL và nhận response (phản hồi). Giống như gửi đơn hàng qua website và nhận kết quả |
| **gRPC** | Giao thức giao tiếp **nhanh hơn REST** (dùng binary thay vì text), phù hợp cho giao tiếp giữa các service nội bộ. Phức tạp hơn REST khi setup |

---

## Bối Cảnh Đặc Thù — Tại Sao Desktop AI App Khác Biệt

Trước khi đi vào từng tính chất, cần hiểu rõ bối cảnh đặc thù mà kiến trúc này phải phục vụ — vì nó **khác hoàn toàn** với cả web app lẫn desktop app truyền thống:

| Đặc thù | Nghĩa là gì | Hệ quả cho kiến trúc |
|---|---|---|
| **Chạy trên 1 máy duy nhất** của user | Mọi thứ (giao diện, AI, database) đều chạy trên laptop/PC của user. Không có server riêng | Không thể "thêm server" khi thiếu sức mạnh. Phải quản lý tinh tế CPU, RAM, GPU trên 1 máy duy nhất. Phải biết máy user có GPU hay không, có bao nhiêu VRAM |
| **AI inference cực nặng** — tức là quá trình chạy model AI để cho ra kết quả | Model Whisper (nhận dạng giọng nói) cần load 3-5GB vào bộ nhớ GPU. Model XTTS (tổng hợp giọng) mất 10-30 giây cho mỗi câu nói | Nếu code AI chạy cùng chỗ với code giao diện, giao diện sẽ **đơ cứng** trong suốt thời gian AI xử lý. User sẽ nghĩ app bị crash. Phải tách riêng phần chạy AI ra khỏi phần hiển thị giao diện |
| **Đa dạng model/API** thay đổi liên tục | Hôm nay dùng WhisperX cho nhận dạng giọng, ngày mai có model Faster-Whisper tốt hơn. Hoặc user muốn dùng API cloud thay vì chạy local | Kiến trúc phải cho phép **thay thế** bất kỳ model/API nào mà **không cần viết lại** phần logic chính. Giống thay pin điện thoại — chỉ cần đúng kích thước, hãng nào cũng được |
| **Pipeline nhiều bước tuần tự** | Quy trình lồng tiếng gồm 6 bước nối tiếp nhau (giải thích chi tiết ở mục dưới). Mỗi bước có thể mất từ vài giây đến hàng chục phút | Cần cơ chế "save game" (checkpoint) sau mỗi bước. Nếu bước 5 bị lỗi, chạy lại từ bước 5 thay vì từ đầu. Mất điện giữa chừng không được mất toàn bộ công việc |
| **User là người dùng cuối**, không phải lập trình viên | User là biên tập viên video, người dịch thuật, YouTuber — không biết code | App phải ổn định, lỗi phải hiện thông báo dễ hiểu ("Hết dung lượng bộ nhớ GPU, vui lòng đóng bớt ứng dụng"), **tuyệt đối không** hiện lỗi kỹ thuật kiểu `Traceback (most recent call last): ...` |
| **Chạy offline được** nhưng cũng hỗ trợ cloud API | Khi có internet: gọi OpenAI, ElevenLabs (chất lượng cao, tốn tiền). Khi không có internet: dùng model chạy local trên máy (miễn phí, chất lượng tùy GPU) | Hệ thống phải hoạt động **giống hệt nhau** dù dùng local model hay cloud API. Phần logic chính (pipeline) không cần biết đang dùng cái nào — chỉ cần gửi input và nhận output theo format chuẩn |

---

### Quy trình Pipeline lồng tiếng — Giải thích từng bước

Toàn bộ quy trình lồng tiếng video đi qua 6 bước chính, mỗi bước có tên viết tắt từ thuật ngữ tiếng Anh:

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
| **Demux** | **De-multiplex** (Tách luồng) | Tách video gốc thành các thành phần riêng biệt: luồng hình ảnh, luồng giọng nói (vocal), luồng nhạc nền/tiếng động (background) | Video YouTube 10 phút → tách ra: `video_only.mp4` + `vocal.wav` + `background.wav` |
| **ASR** | **Automatic Speech Recognition** (Nhận dạng giọng nói tự động) | Đưa file giọng nói vào model AI để nó "nghe" và viết ra văn bản, kèm theo mốc thời gian chính xác từng câu/từng từ | `vocal.wav` → "Xin chào các bạn" (0:00-0:02), "Hôm nay chúng ta..." (0:02-0:05) |
| **Translate** | **Machine Translation** (Dịch thuật máy) | Dịch văn bản đã bóc băng sang ngôn ngữ đích | "Xin chào các bạn" → "Hello everyone" |
| **TTS** | **Text-to-Speech** (Chuyển văn bản thành giọng nói) | Model AI đọc văn bản đã dịch thành giọng nói, có thể **sao chép giọng gốc** (voice cloning) để giữ tông giọng | "Hello everyone" → file `segment_001.wav` với giọng giống người nói gốc |
| **Mix** | **Audio Mixing** (Trộn âm thanh) | Trộn giọng đọc mới (từ TTS) với nhạc nền/tiếng động (từ Demux). Điều chỉnh tốc độ đọc cho khớp với khẩu hình (time-stretching) | `segment_001.wav` + `background.wav` → `mixed_audio.wav` |
| **Mux** | **Multiplex** (Ghép luồng) | Ghép luồng âm thanh mới (đã trộn) với luồng hình ảnh gốc thành video hoàn chỉnh | `video_only.mp4` + `mixed_audio.wav` → `dubbed_video.mp4` |

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
- Technical debt (nợ kỹ thuật) tích lũy theo cấp số nhân
- Mỗi lần sửa bug tạo ra 2-3 bug mới
- Không thể phân công công việc cho nhiều người

---

## 2. Dependency Inversion — Đảo Ngược Phụ Thuộc

### Định nghĩa
Các module cấp cao (Orchestrator, Use Case) **không bao giờ phụ thuộc trực tiếp** vào module cấp thấp (WhisperX, ElevenLabs). Cả hai cùng phụ thuộc vào **một abstraction (interface — bản hợp đồng trung gian) ở giữa**.

### Tại sao đây là tính chất quan trọng nhất cho yêu cầu "linh hoạt model/API"

```
❌ SAI (Gắn chặt - Tight coupling):
   Orchestrator → import whisperx → gọi whisperx.transcribe()
   
   Hậu quả: Muốn đổi sang Faster-Whisper phải sửa Orchestrator
   
✅ ĐÚNG (Đảo ngược phụ thuộc - Dependency Inversion):
   Orchestrator → gọi ASREngine.transcribe()    ← Interface (bản hợp đồng chung)
                                                     ↑
                                                 WhisperXPlugin implements ASREngine
                                                 FasterWhisperPlugin implements ASREngine
                                                 OpenAIWhisperPlugin implements ASREngine
```

### Tại sao đặc biệt quan trọng cho dự án này

Thế giới AI thay đổi **cực nhanh** — "state-of-the-art" (tiên tiến nhất) hôm nay có thể bị thay thế chỉ sau vài tháng:

**Bức tranh công nghệ cho từng module trong pipeline:**

#### 🎤 Module ASR (Nhận dạng giọng nói → chữ viết)

| Công nghệ | Loại | Đặc điểm | Trạng thái |
|---|---|---|---|
| **WhisperX** | 🖥️ Local Model | Nhanh, word-level timestamp, speaker diarization | Phổ biến 2023-2024 |
| **Faster-Whisper** | 🖥️ Local Model | Nhanh gấp 4x Whisper gốc, tiết kiệm VRAM | Đang lên 2024+ |
| **Distil-Whisper** | 🖥️ Local Model | Nhẹ gấp 6x, tốc độ cực cao, chất lượng giảm nhẹ | Mới 2024 |
| **OpenAI Whisper API** | ☁️ Cloud API | Chất lượng cao, dễ dùng, tính phí theo phút audio | Ổn định |
| **Google Cloud Speech-to-Text** | ☁️ Cloud API | Hỗ trợ 125+ ngôn ngữ, streaming | Ổn định |
| **AssemblyAI** | ☁️ Cloud API | Chuyên nghiệp, speaker diarization tốt | Ổn định |
| **Deepgram** | ☁️ Cloud API | Cực nhanh, real-time, giá cạnh tranh | Đang lên |

#### 🌐 Module Translation (Dịch thuật)

| Công nghệ | Loại | Đặc điểm | Trạng thái |
|---|---|---|---|
| **DeepL API** | ☁️ Cloud API | Chất lượng dịch tốt nhất, đặc biệt Châu Âu | Ổn định |
| **Google Translate API** | ☁️ Cloud API | Hỗ trợ nhiều ngôn ngữ nhất (130+) | Ổn định |
| **OpenAI GPT API** (dùng cho dịch) | ☁️ Cloud API | Dịch ngữ cảnh tốt, hiểu context phức tạp | Phổ biến |
| **Meta NLLB (No Language Left Behind)** | 🖥️ Local Model | Miễn phí, hỗ trợ 200+ ngôn ngữ, chạy local | Open-source |
| **MarianMT (Helsinki NLP)** | 🖥️ Local Model | Nhẹ, nhanh, nhiều cặp ngôn ngữ, chạy trên CPU được | Open-source |
| **Anthropic Claude API** (dùng cho dịch) | ☁️ Cloud API | Dịch văn phong tự nhiên, hiểu ngữ cảnh sâu | Mới |

#### 🔊 Module TTS (Chuyển chữ → giọng nói)

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

#### 🎬 Module Media (Demux/Mux) & Audio Post-processing (Mix)

| Công nghệ | Loại | Đặc điểm | Trạng thái |
|---|---|---|---|
| **FFmpeg** | 🔧 Tool/Binary | Đa năng: tách/ghép video+audio, chuyển format. "Swiss Army knife" của xử lý media | Tiêu chuẩn |
| **Sox (Sound eXchange)** | 🔧 Tool/Binary | Chuyên audio: trộn, cắt, nối, lọc tiếng ồn. Không xử lý video. Có bộ lọc âm thanh chuyên biệt hơn FFmpeg | Ổn định |
| **Demucs (Meta)** | 🖥️ Local Model | Tách giọng hát khỏi nhạc nền bằng AI (vocal separation). Chất lượng vượt trội so với FFmpeg | AI-powered |
| **Spleeter (Deezer)** | 🖥️ Local Model | Tách nhạc thành stems (vocal, drums, bass...) | Open-source |
| **Rubberband** | 🔧 Library | Time-stretching (giãn/nén thời lượng) và pitch-shifting (thay đổi cao độ) chất lượng cao | Ổn định |
| **pyrubberband** | 🐍 Python lib | Python wrapper cho Rubberband | Ổn định |

> [!IMPORTANT]
> **Đây chính là lý do Dependency Inversion quan trọng bậc nhất.** Mỗi module có 4-7+ lựa chọn công nghệ. Nhân 5 module = hàng trăm tổ hợp có thể. Nếu code gắn chặt vào 1 công nghệ, mỗi lần đổi = viết lại. Với Dependency Inversion, đổi bất kỳ = chỉ viết 1 adapter mới (~100-200 dòng code), không sửa gì ở Core.

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
- Không thể cho user chọn model tại runtime (lúc đang dùng app)
- Không thể test pipeline mà không có model thật (không mock/giả lập được)

---

## 3. Event-Driven Reactivity — Giao Tiếp Hướng Sự Kiện

### Định nghĩa
Các thành phần **không gọi trực tiếp** lẫn nhau. Thay vào đó, chúng **phát ra sự kiện** (events) và **lắng nghe sự kiện** (subscribe). Một thành phần phát lệnh (dispatch), thành phần khác nhận và xử lý — không ai chờ ai.

**Dispatch** ở đây nghĩa là: gửi một yêu cầu đi rồi **quay lại làm việc khác ngay**, không đứng chờ kết quả. Giống gửi email thay vì gọi điện — bạn gửi xong thì tiếp tục công việc, khi nào có phản hồi thì xử lý.

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
| Load model WhisperX vào bộ nhớ GPU (VRAM) | 15-45 giây |
| Nhận dạng giọng nói (ASR) cho 10 phút audio | 30-120 giây |
| Tổng hợp giọng nói (TTS) cho 100 câu | 5-15 phút |
| Tách/ghép video 4K bằng FFmpeg | 10-60 giây |

### Giải pháp duy nhất đúng: Event-Driven Architecture

```
UI Thread                    Worker Thread/Process
─────────                    ────────────────────
  │                                   │
  ├── dispatch("START_ASR") ────────► │   ← "Gửi lệnh rồi quay về ngay"
  │   (trả về ngay, UI vẫn mượt)     ├── Load model...
  │                                   ├── Transcribe...
  │ ◄── event("PROGRESS", 50%) ──────┤   ← "Worker báo cáo tiến độ"
  │   (cập nhật progress bar)         │
  │ ◄── event("PROGRESS", 100%) ─────┤
  │ ◄── event("ASR_COMPLETE", data) ──┤   ← "Worker báo xong việc"
  │   (hiển thị kết quả)             │
```

### Công nghệ hỗ trợ Event-Driven trong PySide6

PySide6 (framework giao diện) **đã có sẵn** cơ chế Event-Driven tuyệt vời gọi là **Signals & Slots**:

- **Signal** = Sự kiện phát ra (giống chuông báo)
- **Slot** = Hàm xử lý khi nhận được signal (giống người nghe chuông rồi làm gì đó)
- **QThread** = Thread riêng biệt để chạy tác vụ nặng mà không ảnh hưởng UI

### Ví dụ code cụ thể cho dự án dubbing

```python
from PySide6.QtCore import QObject, Signal, Slot, QThread


# ═══════════════════════════════════════════════════════════
# WORKER — Chạy trên thread riêng, KHÔNG BAO GIỜ chạm vào UI
# ═══════════════════════════════════════════════════════════
class ASRWorker(QObject):
    """Worker xử lý nhận dạng giọng nói — chạy trên thread riêng."""

    # Khai báo các Signal (sự kiện) mà worker có thể phát ra
    progress = Signal(int, str)        # (phần trăm, thông báo)
    completed = Signal(object)         # (kết quả transcription)
    error = Signal(str)                # (thông báo lỗi)

    def __init__(self, audio_path: str, plugin_name: str):
        super().__init__()
        self.audio_path = audio_path
        self.plugin_name = plugin_name   # "whisperx_local" hoặc "openai_api"

    @Slot()
    def run(self):
        """Hàm chính — chạy trên Worker Thread, KHÔNG PHẢI UI Thread."""
        try:
            # Bước 1: Load plugin theo tên (Dependency Inversion!)
            self.progress.emit(10, "Đang khởi tạo model...")
            plugin = PluginRegistry.get_asr_plugin(self.plugin_name)

            # Bước 2: Chạy inference (có thể mất 30-120 giây)
            self.progress.emit(30, "Đang nhận dạng giọng nói...")
            result = plugin.transcribe(self.audio_path, language="vi")

            # Bước 3: Phát signal kết quả
            self.progress.emit(100, "Hoàn thành!")
            self.completed.emit(result)

        except Exception as e:
            self.error.emit(f"Lỗi nhận dạng giọng nói: {str(e)}")


# ═══════════════════════════════════════════════════════════
# UI VIEW — Chạy trên Main Thread, CHỈ LÀM VIỆC VỚI GIAO DIỆN
# ═══════════════════════════════════════════════════════════
class SubtitleView(QWidget):
    """Giao diện tính năng tạo phụ đề."""

    def on_start_button_clicked(self):
        """Khi user bấm nút 'Bắt đầu bóc băng'."""

        # 1. Tạo worker và thread riêng
        self.worker = ASRWorker(
            audio_path="project/vocal.wav",
            plugin_name="whisperx_local"     # Có thể đổi sang "openai_api"
        )
        self.thread = QThread()
        self.worker.moveToThread(self.thread)  # Chuyển worker sang thread khác

        # 2. Kết nối signals → slots (ai phát gì, ai nhận gì)
        self.thread.started.connect(self.worker.run)         # Thread bắt đầu → worker chạy
        self.worker.progress.connect(self.on_progress)       # Worker báo tiến độ → UI cập nhật
        self.worker.completed.connect(self.on_completed)     # Worker xong → UI hiển thị
        self.worker.error.connect(self.on_error)             # Worker lỗi → UI thông báo

        # 3. Bắt đầu! UI KHÔNG BỊ BLOCK — trả về ngay lập tức
        self.thread.start()
        self.start_button.setEnabled(False)
        self.status_label.setText("Đang xử lý...")

    @Slot(int, str)
    def on_progress(self, percent, message):
        """Nhận tiến độ từ worker → cập nhật thanh tiến trình."""
        self.progress_bar.setValue(percent)    # Thanh tiến trình chạy mượt
        self.status_label.setText(message)     # Hiển thị "Đang nhận dạng giọng nói..."

    @Slot(object)
    def on_completed(self, result):
        """Nhận kết quả từ worker → hiển thị transcript."""
        self.text_editor.setText(result.to_srt())   # Hiển thị phụ đề
        self.start_button.setEnabled(True)
        self.thread.quit()

    @Slot(str)
    def on_error(self, error_message):
        """Nhận lỗi từ worker → hiển thị thông báo thân thiện."""
        QMessageBox.warning(self, "Có lỗi xảy ra", error_message)
        self.start_button.setEnabled(True)
        self.thread.quit()
```

> [!NOTE]
> **Điểm mấu chốt:** Khi user bấm nút, `self.thread.start()` trả về **ngay lập tức**. UI vẫn mượt mà. Worker chạy inference 2 phút trên thread riêng. Mỗi khi worker phát signal `progress`, UI tự động cập nhật progress bar. **Không bao giờ đơ giao diện.**

### Vi phạm sẽ gây ra
- App đơ mỗi khi chạy inference (chạy AI model)
- User mất niềm tin, bỏ app
- Không thể cancel task giữa chừng (vì UI bị block, nút Cancel không click được)

---

## 4. Centralized State Management — Quản Lý Trạng Thái Tập Trung

### Định nghĩa
Toàn bộ trạng thái ứng dụng (project hiện tại, danh sách giọng, tiến trình pipeline, cấu hình model đang chọn...) được lưu tại **một nơi duy nhất** (Global Store). Mọi thành phần đọc/ghi state thông qua Store này.

### Tại sao quan trọng cho Desktop app (khác Web app)

Trong web app, mỗi request (yêu cầu) là stateless (không lưu trạng thái) — server xử lý xong thì quên.

Trong desktop app, **mọi thứ là stateful** (luôn giữ trạng thái):
- User mở project → tất cả các tab phải biết project nào đang mở
- User chọn giọng trong Voice Studio → tab Auto Dubbing phải thấy giọng đó
- Pipeline đang chạy 60% → tất cả các view phải hiện thanh tiến trình
- User thay đổi API key → tất cả plugin liên quan phải biết

Nếu mỗi feature tự quản lý state riêng (như v1.5 gợi ý), sẽ xảy ra:
- **State inconsistency (trạng thái không đồng bộ):** Feature A nghĩ dùng giọng X, Feature B nghĩ dùng giọng Y
- **Spaghetti communication (giao tiếp rối loạn):** Feature A gọi Feature B để hỏi state → Feature B gọi Feature C → vòng lặp phụ thuộc
- **Khó persist/restore (khó lưu/khôi phục):** Khi app restart, phải khôi phục state ở N nơi khác nhau

### Ví dụ cụ thể: Global Store trong dự án dubbing

```python
from PySide6.QtCore import QObject, Signal


class GlobalStore(QObject):
    """
    Nơi lưu trữ DUY NHẤT toàn bộ trạng thái của ứng dụng.
    
    Mọi feature (tab) đều đọc/ghi state thông qua đây.
    Khi state thay đổi, các Signal tự động thông báo cho UI cập nhật.
    """

    # ── Khai báo Signals: mỗi khi state thay đổi, phát signal ──
    project_changed = Signal(object)        # Khi đổi project đang mở
    voice_list_changed = Signal(list)       # Khi danh sách giọng thay đổi
    pipeline_progress = Signal(str, int)    # Khi pipeline đang chạy (bước nào, %)
    selected_asr_plugin = Signal(str)       # Khi user đổi plugin ASR
    selected_tts_plugin = Signal(str)       # Khi user đổi plugin TTS

    def __init__(self):
        super().__init__()
        # ── State thực tế ──
        self._current_project = None
        self._voices = []
        self._plugin_config = {
            "asr": "whisperx_local",       # Plugin mặc định
            "tts": "coqui_xtts",
            "translation": "deepl_api",
        }

    @property
    def current_project(self):
        return self._current_project

    def set_current_project(self, project):
        """Khi user mở project mới → cập nhật state → thông báo TẤT CẢ các tab."""
        self._current_project = project
        self.project_changed.emit(project)    # ← Tự động thông báo!

    def set_asr_plugin(self, plugin_name: str):
        """Khi user chọn plugin ASR khác → thông báo."""
        self._plugin_config["asr"] = plugin_name
        self.selected_asr_plugin.emit(plugin_name)


# ── Sử dụng trong Feature View ──
class AutoDubbingView(QWidget):
    def __init__(self, store: GlobalStore):
        super().__init__()
        self.store = store
        # Đăng ký "lắng nghe" — khi project thay đổi, tự động cập nhật UI
        self.store.project_changed.connect(self.on_project_changed)
        self.store.voice_list_changed.connect(self.on_voices_updated)

    def on_project_changed(self, project):
        """Tự động được gọi khi user mở project khác ở BẤT KỲ tab nào."""
        self.title_label.setText(f"Dự án: {project.name}")
        self.timeline.load(project.manifest)

    def on_voices_updated(self, voices):
        """Tự động cập nhật dropdown giọng đọc khi Voice Studio thêm giọng mới."""
        self.voice_combo.clear()
        for voice in voices:
            self.voice_combo.addItem(voice.name)
```

### Mô hình tổng quan

```
                    ┌─────────────────────┐
                    │    GLOBAL STORE      │
                    │                     │
                    │  current_project    │   ← Duy nhất 1 nơi lưu
                    │  selected_voice     │
                    │  pipeline_status    │
                    │  plugin_configs     │
                    │  ...                │
                    └──────┬──────────────┘
                           │
              ┌────────────┼────────────┐
              │ subscribe  │ subscribe  │ subscribe
              │ (lắng nghe)│(lắng nghe) │ (lắng nghe)
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Feature  │ │ Feature  │ │ Feature  │
        │ Subtitle │ │ Voice    │ │ Dubbing  │
        │ View     │ │ Studio   │ │ View     │
        └──────────┘ └──────────┘ └──────────┘
        
    Mỗi View chỉ "đăng ký theo dõi" những state nó cần.
    Khi state thay đổi, View TỰ ĐỘNG cập nhật giao diện.
    Không Feature nào cần biết Feature khác tồn tại.
```

### Vi phạm sẽ gây ra
- Dữ liệu không đồng bộ giữa các màn hình
- **Bug "phantom" (ma)** — đây là loại bug chỉ xảy ra khi mở **đúng tổ hợp** tab theo **đúng thứ tự**. Ví dụ: mở tab Voice Studio → thêm giọng mới → chuyển sang tab Dubbing → dropdown giọng vẫn hiện danh sách cũ (vì tab Dubbing tự lưu state riêng, không biết Voice Studio đã thêm giọng). Bug này cực khó tái tạo (reproduce) khi debug, vì developer thường test từng tab riêng lẻ
- Không thể implement Undo/Redo (vì không biết state nằm ở đâu)

---

## 5. Pipeline Composability — Khả Năng Tổ Hợp Pipeline

### Định nghĩa
Quy trình dubbing (Demux → ASR → Translate → TTS → Mix → Mux) phải được mô tả dưới dạng **cấu hình** (configuration), không phải **code cứng** (hardcoded). Mỗi bước là một node (điểm nút) trong DAG, có thể thêm/bớt/thay đổi thứ tự.

### DAG là gì? Tại sao lại là DAG?

**DAG = Directed Acyclic Graph = Đồ thị có hướng không tuần hoàn.**

Hãy tưởng tượng bạn vẽ sơ đồ quy trình trên bảng trắng:
- Mỗi **ô** (node) là một bước công việc
- Mỗi **mũi tên** (edge) nối từ ô này sang ô khác, chỉ hướng "làm xong cái này → mới đến cái kia"
- **Không có vòng tròn** — không bao giờ quay lại bước đã làm (vì sẽ thành vòng lặp vô tận)

```
Ví dụ DAG cho Full Dubbing:

  ┌────────┐
  │ Demux  │ ← Bắt đầu: tách video
  └───┬────┘
      │ tạo ra vocal.wav
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

**Tại sao DAG mà không phải danh sách tuần tự đơn giản?**

Vì một số bước có thể chạy **song song**. Ví dụ: sau khi Demux tách xong vocal.wav và background.wav, bước ASR (xử lý vocal) và bước pre-process background có thể chạy đồng thời — DAG cho phép mô tả điều này.

**DAG được dùng ở đâu ngoài dự án này?**

| Lĩnh vực | Ví dụ | Vì sao dùng DAG |
|---|---|---|
| **CI/CD** (triển khai phần mềm) | GitHub Actions, GitLab CI | Build → Test → Deploy, một số bước chạy song song |
| **Xử lý dữ liệu lớn** | Apache Airflow, Apache Spark | ETL pipeline: Extract → Transform → Load, hàng trăm bước |
| **AI/ML Training** | Kubeflow, MLflow | Thu thập data → Tiền xử lý → Train → Evaluate → Deploy |
| **Đồ họa 3D / Video** | Blender, Nuke, DaVinci Resolve | Node-based compositing: các filter/effect nối thành chuỗi |
| **Build hệ thống** | Make, Bazel, Gradle | Compile file A trước, rồi mới link với file B |

### Tại sao quan trọng cho dự án này

Không phải lúc nào user cũng cần chạy full pipeline:

| Use case | Pipeline cần |
|---|---|
| Chỉ tạo phụ đề | Demux → ASR → Export SRT |
| Chỉ dịch phụ đề có sẵn | Import SRT → Translate → Export SRT |
| Dubbing không dịch (cùng ngôn ngữ) | Demux → ASR → TTS → Mix → Mux |
| Full dubbing | Demux → ASR → Translate → TTS → Mix → Mux |
| Clone giọng (test) | Upload audio → TTS (voice clone mode) |

Nếu pipeline bị hardcode (viết cứng trong code), mỗi use case = 1 luồng code riêng → code trùng lặp, bug ở chỗ này mà chỗ kia không sửa.

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
- **Mỗi use case mới = viết lại logic điều phối** — thay vì chỉ tạo config mới, phải viết hàm mới, test lại từ đầu
- **Không thể cho user tùy chỉnh pipeline qua giao diện** — ví dụ: kéo thả các bước, bỏ bước dịch, thêm bước kiểm tra chất lượng. Với DAG config, UI chỉ cần cho user sắp xếp các block rồi sinh ra config tương ứng
- Khó implement retry/resume cho từng bước riêng lẻ

---

## 6. Fault Isolation & Recovery — Cô Lập Lỗi và Phục Hồi

### Định nghĩa
Khi một bước trong pipeline thất bại (model crash, API timeout, hết VRAM), hệ thống phải:
1. **Cô lập** lỗi — không lan sang bước khác
2. **Lưu checkpoint** (điểm lưu) — dữ liệu đã xử lý xong không bị mất
3. **Cho phép resume** (tiếp tục) — chạy lại từ bước lỗi, không phải từ đầu

### Tại sao đặc biệt quan trọng cho dự án này

Hãy tưởng tượng kịch bản: User lồng tiếng video 2 tiếng. Pipeline đã chạy xong:
- ✅ Demux — tách audio (2 phút)
- ✅ ASR — nhận dạng giọng nói (15 phút)
- ✅ Translate — dịch thuật (3 phút)
- ✅ TTS đã tổng hợp 180/200 câu (45 phút)
- ❌ TTS câu 181 — ElevenLabs API trả về lỗi 429 (quá giới hạn gọi API)

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
Trước khi viết bất kỳ implementation (code triển khai) nào, **định nghĩa rõ ràng Data Contract** — cấu trúc dữ liệu vào/ra của mỗi module. Mọi plugin phải tuân thủ contract này.

### Contract-First: Tư duy thiết kế cho thời đại công nghệ thay đổi hàng ngày

> [!IMPORTANT]
> **Đúng — đây không chỉ là một design pattern, mà là một TƯ DUY THIẾT KẾ cốt lõi** cho bất kỳ hệ thống nào hoạt động trong môi trường công nghệ biến đổi nhanh.
>
> **Nguyên lý:** Thay vì thiết kế hệ thống xung quanh **công nghệ cụ thể** (WhisperX, ElevenLabs, DeepL...), hãy thiết kế xung quanh **hợp đồng dữ liệu** (input/output format). Công nghệ sẽ thay đổi, nhưng bản chất công việc thì không:
> - Bất kể dùng model ASR nào, đầu vào luôn là file audio, đầu ra luôn là danh sách câu + timestamp
> - Bất kể dùng API TTS nào, đầu vào luôn là văn bản, đầu ra luôn là file audio
>
> **Khi bạn định nghĩa "hợp đồng" trước, bạn đang nói:** "Tôi không quan tâm bên trong dùng công nghệ gì, miễn là đầu vào/đầu ra đúng format này." → Thay đổi công nghệ = thay đổi bên trong plugin, hệ thống bên ngoài không biết, không cần sửa.

### Ví dụ thực tế

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

**Adapter** (bộ chuyển đổi) trong mỗi plugin chịu trách nhiệm biến đổi output đặc thù của mỗi công nghệ → contract chuẩn mà hệ thống hiểu.

### Vi phạm sẽ gây ra
- Mỗi lần thêm plugin mới phải sửa module ở trên
- Data format inconsistency (dữ liệu không nhất quán) gây bug ở downstream modules (các module phía sau trong pipeline)
- Không thể test module độc lập (vì không biết input format chính xác)

---

# PHẦN B — TRIỂN KHAI VẬT LÝ (Physical Deployment)

Triển khai vật lý trả lời câu hỏi: **"Code được đóng gói, chạy trên process/thread nào, dữ liệu nằm ở đâu trên disk?"**

---

## 1. UI Thread Sanctity — Bảo Vệ Tuyệt Đối UI Thread

### Định nghĩa
UI Thread (Main Thread trong PySide6) **CHỈ** được phép:
- Render (vẽ) giao diện
- Nhận sự kiện chuột/bàn phím
- Phát dispatch command (gửi lệnh)
- Nhận event và cập nhật widget (thành phần giao diện)

**TUYỆT ĐỐI KHÔNG** được phép:
- Gọi inference AI (chạy model AI)
- Đọc/ghi file lớn
- Gọi HTTP request (gọi API qua mạng)
- Chạy bất kỳ logic nào có thể mất > 50ms

### Process Model (Mô hình tiến trình) đề xuất

```
┌─────────────────────────────────────────────────────────┐
│                    MAIN PROCESS                         │
│           (Chương trình chính của app)                   │
│                                                         │
│  ┌──────────────┐    Signal/Slot    ┌────────────────┐  │
│  │  UI Thread   │ ◄──────────────► │  Event Bus     │  │
│  │  (Main)      │  (giao tiếp qua  │  (QThread)     │  │
│  │              │   tín hiệu)      │                │  │
│  │  - Vẽ giao   │                   │  - Chuyển lệnh │  │
│  │    diện      │                   │  - Chuyển kết  │  │
│  │  - Nhận thao │                   │    quả         │  │
│  │    tác user  │                   │                │  │
│  └──────────────┘                   └───────┬────────┘  │
│                                             │           │
│  ┌──────────────────────────────────────────┼─────────┐ │
│  │      WORKER THREAD POOL                  │         │ │
│  │      (Nhóm luồng xử lý nặng)            │         │ │
│  │                                          │         │ │
│  │  ┌─────────────┐  ┌─────────────┐       │         │ │
│  │  │ Orchestrator│  │ File I/O    │       │         │ │
│  │  │ (Điều phối) │  │ (Đọc/ghi   │       │         │ │
│  │  │             │  │  file)      │       │         │ │
│  │  └──────┬──────┘  └─────────────┘       │         │ │
│  │         │                                │         │ │
│  └─────────┼────────────────────────────────┘         │ │
│            │                                           │
└────────────┼───────────────────────────────────────────┘
             │ subprocess / IPC
             │ (tiến trình con / giao tiếp liên tiến trình)
             ▼
┌────────────────────────┐  ┌────────────────────────┐
│   TIẾN TRÌNH AI #1     │  │   TIẾN TRÌNH AI #2     │
│   (Chạy riêng biệt)   │  │   (Chạy riêng biệt)   │
│                        │  │                        │
│   WhisperX + CUDA      │  │   XTTS v2 + CUDA      │
│   Môi trường Python    │  │   Môi trường Python    │
│   riêng                │  │   riêng                │
│                        │  │                        │
│   Giao tiếp qua:       │  │   Giao tiếp qua:      │
│   - HTTP nội bộ        │  │   - HTTP nội bộ        │
│   - gRPC               │  │   - gRPC               │
│   - stdin/stdout pipe  │  │   - stdin/stdout pipe  │
└────────────────────────┘  └────────────────────────┘
```

### Tại sao cần Process (tiến trình) riêng cho AI inference — không chỉ Thread (luồng)

> [!CAUTION]
> **Giải thích dễ hiểu về Python GIL (Global Interpreter Lock — Khóa toàn cục):**
>
> Hãy tưởng tượng Python như một **phòng họp chỉ có 1 micro**. Dù có 10 người (10 thread) muốn nói (chạy code), tại mỗi thời điểm **chỉ 1 người được cầm micro**. Những người khác phải **xếp hàng chờ**.
>
> Điều này có nghĩa:
> - Nếu bạn tạo 2 thread trong Python — 1 thread vẽ UI, 1 thread chạy AI — chúng **không thực sự chạy đồng thời**. Chúng luân phiên nhau "giành micro".
> - Khi thread AI đang giữ micro và xử lý nặng, thread UI phải chờ → giao diện bị **giật** (jitter), không mượt mà.
>
> **Giải pháp: Subprocess (tiến trình con)**
> - Mỗi subprocess là **một phòng họp riêng, có micro riêng** → chạy thực sự song song
> - AI inference chạy trong subprocess → hoàn toàn **không ảnh hưởng** đến UI ở process chính
> - Thread (QThread) vẫn hữu ích cho các tác vụ I/O-bound (chờ file, chờ mạng) — vì khi chờ I/O, Python tự nhả GIL
> - Subprocess cần thiết cho các tác vụ CPU/GPU-bound (tính toán nặng) như AI inference

Ngoài ra, subprocess giải quyết thêm 3 vấn đề:

- **Crash containment (ngăn chặn sập lan):** Khi model AI gặp **segfault** — tức lỗi truy cập bộ nhớ trái phép (thường xảy ra trong thư viện CUDA/PyTorch viết bằng C++, khi code cố đọc/ghi vùng bộ nhớ không thuộc về nó) — hệ điều hành **ép tắt chương trình ngay lập tức**. Python không thể bắt (catch) lỗi này. Nếu chạy cùng process với app chính → cả app chết. Nếu chạy trong subprocess → chỉ subprocess chết, app chính bắt lỗi và thông báo user "Model bị lỗi, vui lòng thử lại"
- **Dependency isolation:** Mỗi model có thể cần Python environment khác nhau (WhisperX cần PyTorch 2.0, XTTS cần PyTorch 2.1)
- **VRAM control:** Có thể giới hạn VRAM per-process để tránh OOM (hết bộ nhớ GPU)

---

## 2. Process Isolation cho AI Models — Cô Lập Tiến Trình

### Định nghĩa
Mỗi AI model **nặng** (WhisperX, XTTS, v.v.) chạy trong process (tiến trình) hoặc container riêng, giao tiếp với app chính qua **IPC (Inter-Process Communication — Giao tiếp liên tiến trình)** — tức cơ chế để 2 chương trình đang chạy riêng biệt "nói chuyện" với nhau.

### Tại sao cần thiết

| Vấn đề | Giải pháp bằng Process Isolation |
|---|---|
| **Xung đột thư viện:** WhisperX cần `numpy==1.24`, XTTS cần `numpy==1.26` | Mỗi process có Python env riêng, cài phiên bản khác nhau |
| **Hết bộ nhớ GPU:** 2 model cùng load vào VRAM = OOM (hết bộ nhớ) | Orchestrator quyết định load/unload per-process |
| **Ngăn sập lan:** CUDA segfault (lỗi bộ nhớ trái phép) trong Whisper | Chỉ subprocess chết, app chính bắt lỗi và thông báo user thân thiện |
| **Mở rộng tương lai:** Muốn chạy AI trên remote GPU server sau này | Đổi IPC từ local socket → remote gRPC, không sửa app chính |

### Cơ chế giao tiếp đề xuất

```
App chính                              AI Subprocess
─────────                              ─────────────
    │                                       │
    ├─── HTTP POST /transcribe ───────────► │
    │    {"audio": "path/to/file.wav",      │
    │     "language": "vi"}                 │
    │                                       ├── Load model (nếu chưa)
    │                                       ├── Inference (chạy AI)...
    │ ◄── SSE: progress 30% ────────────────┤  (Server gửi tiến độ liên tục)
    │ ◄── SSE: progress 70% ────────────────┤
    │ ◄── HTTP 200: result ─────────────────┤
    │    {"segments": [...]}                │
```

### Nên dùng FastAPI hay Flask cho Local HTTP Server?

> [!TIP]
> **Đề xuất: FastAPI** — vì các lý do sau:
>
> | Tiêu chí | FastAPI | Flask |
> |---|---|---|
> | **Async support** | ✅ Có sẵn (native async/await) — quan trọng để xử lý nhiều request đồng thời và SSE streaming tiến độ | ❌ Cần extension (Flask-SocketIO) |
> | **Tự động tạo API docs** | ✅ Swagger UI tự động tại `/docs` — debug cực tiện, test API bằng trình duyệt | ❌ Phải cài thêm và cấu hình |
> | **Type validation** | ✅ Pydantic tích hợp — kiểm tra dữ liệu vào/ra tự động, bắt lỗi sớm | ❌ Phải tự viết validation |
> | **Hiệu năng** | ✅ Nhanh gấp 2-3x Flask (dùng Starlette/Uvicorn) | Đủ dùng cho local |
> | **Learning curve** | Trung bình (cần hiểu async) | Thấp |
> | **Phù hợp cho project này** | ✅ **Rất phù hợp** — cần streaming progress, type-safe contracts, nhiều endpoint | Phù hợp cho prototype đơn giản |
>
> **Lý do chính:** FastAPI + Pydantic **enforce Contract-First tự động** — khi định nghĩa endpoint với type hints, FastAPI tự động validate input/output. Điều này khớp hoàn hảo với triết lý kiến trúc Contract-First.

---

## 3. Resource-Aware Scheduling — Lập Lịch Theo Tài Nguyên

### Định nghĩa
Orchestrator (bộ điều phối) phải **biết** tài nguyên hiện có (VRAM trống, RAM trống, mức sử dụng GPU) trước khi quyết định chạy task tiếp theo.

### Tại sao bắt buộc cho desktop chạy AI

Trên server, có thể scale up (nâng cấp) bằng thêm GPU. Trên desktop user, **chỉ có 1 GPU, thường 8-12GB VRAM**:

| Model | VRAM cần | Ghi chú |
|---|---|---|
| WhisperX large-v3 | ~3.5 GB | Cần giữ trong VRAM suốt quá trình ASR |
| XTTS v2 | ~2.5 GB | Cần load per TTS session |
| Tổng cộng | ~6 GB | Chưa tính OS + display driver (~1-2 GB) |

Nếu 2 model load đồng thời trên GPU 8GB → OOM (hết bộ nhớ) → crash.

**Resource Manager** phải:
1. Kiểm tra VRAM hiện tại (qua `nvidia-smi` hoặc thư viện `pynvml`)
2. Biết mỗi model cần bao nhiêu VRAM
3. Ra lệnh **unload** (giải phóng) WhisperX trước khi **load** (nạp) XTTS
4. Queue (xếp hàng) task nếu không đủ tài nguyên

### Vi phạm sẽ gây ra
- CUDA Out of Memory → app crash
- Máy user bị chiếm hết RAM → cả hệ thống chậm
- Không thể chạy trên máy GPU yếu (6GB VRAM)

---

## 4. Environment Isolation — Cô Lập Môi Trường

### Định nghĩa
App chính, mỗi local AI plugin, và các công cụ hệ thống (FFmpeg, Sox) có **môi trường chạy tách biệt** — tránh xung đột thư viện (dependency conflict).

**Sox (Sound eXchange)** là gì và khác FFmpeg thế nào?

| Tiêu chí | FFmpeg | Sox |
|---|---|---|
| **Chức năng** | Xử lý **cả video lẫn audio** — "dao đa năng Thụy Sĩ" của xử lý media | **Chỉ xử lý audio** — chuyên sâu hơn về âm thanh |
| **Điểm mạnh** | Demux/mux video, chuyển format, cắt ghép video, encode/decode | Trộn audio, cắt nối audio, lọc tiếng ồn, chuyển đổi tốc độ, hiệu ứng âm thanh |
| **Dùng trong project** | Bước Demux (tách video) và Mux (ghép video) | Bước Mix (trộn giọng đọc với nhạc nền) |
| **Kích thước** | ~80 MB | ~5 MB |
| **Khi nào dùng** | Khi cần thao tác **video** hoặc chuyển đổi format | Khi cần thao tác **audio** chuyên sâu (effect, filter, mixing) |

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
│   ├── ffmpeg.exe                ← Binary (file chạy), không cần Python
│   └── sox.exe                   ← Binary, không cần Python
```

### Tại sao Docker cho desktop user?

> [!WARNING]
> **Docker KHÔNG phải lựa chọn tốt cho end-user desktop app.** Yêu cầu user cài Docker Desktop trên Windows là rào cản lớn (cần Hyper-V/WSL2, ~4GB RAM overhead, phức tạp khi setup GPU passthrough). **Isolated venv + subprocess** là giải pháp thực tế hơn cho desktop distribution.
>
> Docker chỉ nên dùng cho development/CI environment, không phải production deployment cho end-user.

---

## 5. Data Locality & Checkpoint — Dữ Liệu Cục Bộ và Điểm Lưu

### Định nghĩa
Mọi dữ liệu trung gian được lưu trên disk theo cấu trúc rõ ràng, cho phép resume (tiếp tục) pipeline từ bất kỳ bước nào.

### Cấu trúc project folder đề xuất

```
storage/projects/project_001/
├── metadata.json                 ← Trạng thái pipeline, timestamps, config
├── input/
│   └── original_video.mp4
├── intermediate/                  ← Dữ liệu trung gian — "save game" sau mỗi bước
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

1. **Resume granularity (độ chi tiết khi tiếp tục):** TTS lỗi ở câu 181 → chỉ chạy lại từ câu 181 (vì 180 file .wav đã có)
2. **Debug transparency (debug dễ dàng):** Mở folder intermediate, xem từng bước đã output gì → debug bằng mắt
3. **User inspection (user kiểm tra được):** User có thể mở transcript.json, sửa text sai trước khi chạy TTS
4. **Backup/share:** Copy folder project = copy toàn bộ trạng thái

---

## 6. Packaging & Distribution — Đóng Gói và Phân Phối

### Thách thức đặc thù

Desktop app Python + AI models = **bài toán đóng gói phức tạp nhất** trong thế giới Python:

| Thành phần | Kích thước | Ghi chú |
|---|---|---|
| App chính (PySide6 + logic) | ~150 MB | PyInstaller bundle |
| PyTorch + CUDA runtime | ~2-3 GB | Cần GPU-specific build |
| WhisperX model weights (trọng số) | ~3 GB | Download lần đầu |
| XTTS model weights (trọng số) | ~2 GB | Download lần đầu |
| FFmpeg binary | ~80 MB | Đi kèm installer |

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

# PHẦN C — HỆ THỐNG KIỂM TRA BẢN QUYỀN (LICENSE)

## Yêu cầu

Hệ thống cần cơ chế kiểm tra bản quyền (license) để:
- Phân biệt bản Free / Pro / Enterprise
- Giới hạn tính năng hoặc số lượng sử dụng theo gói
- Bảo vệ doanh thu khi phát hành thương mại

## Phân tích giải pháp License

### Lựa chọn 1: Supabase (Đề xuất của bạn)

**Supabase** là nền tảng Backend-as-a-Service mã nguồn mở, cung cấp: PostgreSQL database, Authentication, API tự động, Realtime subscriptions.

| Tiêu chí | Đánh giá |
|---|---|
| **Chi phí** | ✅ Free tier hào phóng (50,000 monthly active users, 500 MB database, 1 GB file storage) |
| **Dễ tích hợp** | ✅ Python SDK chính thức (`supabase-py`), REST API đơn giản |
| **Authentication** | ✅ Có sẵn (email/password, OAuth) — dùng để xác thực user |
| **Database** | ✅ PostgreSQL — lưu license keys, usage tracking, user profiles |
| **Realtime** | ✅ Có thể push thông báo hết hạn, cập nhật license từ xa |
| **Self-host được** | ✅ Nếu muốn kiểm soát hoàn toàn, có thể tự host Supabase |
| **Rủi ro** | ⚠️ Phụ thuộc vào dịch vụ bên thứ ba — nếu Supabase sập, app không xác thực được |
| **Offline** | ⚠️ Cần thiết kế thêm offline grace period (cho phép dùng X ngày không có mạng) |

### Lựa chọn 2: Keygen.sh — License API chuyên dụng

| Tiêu chí | Đánh giá |
|---|---|
| **Chi phí** | ✅ Free tier cho solo developer (100 licenses). Paid plans từ $49/tháng |
| **Chuyên biệt** | ✅ Thiết kế riêng cho việc quản lý license phần mềm desktop |
| **Tính năng** | ✅ License keys, machine fingerprinting (khóa theo máy), feature flags, trial periods |
| **Offline** | ✅ Hỗ trợ offline license validation bằng cryptographic signatures |
| **API** | ✅ REST API rõ ràng, SDK cho Python |
| **Nhược điểm** | ⚠️ Free tier giới hạn 100 licenses — cần trả phí khi scale |

### Lựa chọn 3: Tự xây dựng (Self-built) trên Supabase

Đây là **lựa chọn tôi khuyến nghị** — kết hợp ưu điểm miễn phí của Supabase với sự linh hoạt tự kiểm soát:

```
┌─────────────────────────────────────────────┐
│            DESKTOP APP (Client)             │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │         License Manager               │  │
│  │                                       │  │
│  │  1. Startup: kiểm tra license local   │  │
│  │  2. Nếu hết hạn local: gọi server    │  │
│  │  3. Cache license 7 ngày (offline)    │  │
│  │  4. Kiểm tra feature flags            │  │
│  └───────────────┬───────────────────────┘  │
│                  │                           │
└──────────────────┼───────────────────────────┘
                   │ HTTPS (chỉ khi online)
                   ▼
┌─────────────────────────────────────────────┐
│          SUPABASE (License Server)          │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  PostgreSQL Database                │    │
│  │                                     │    │
│  │  Table: licenses                    │    │
│  │  ├── license_key (unique)           │    │
│  │  ├── tier (free/pro/enterprise)     │    │
│  │  ├── features_enabled (jsonb)       │    │
│  │  ├── machine_id                     │    │
│  │  ├── expires_at                     │    │
│  │  └── usage_count                    │    │
│  │                                     │    │
│  │  Table: activations                 │    │
│  │  ├── license_key                    │    │
│  │  ├── machine_fingerprint            │    │
│  │  ├── activated_at                   │    │
│  │  └── last_check_in                  │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Edge Functions (Serverless)        │    │
│  │                                     │    │
│  │  POST /validate-license             │    │
│  │  POST /activate-license             │    │
│  │  POST /deactivate-license           │    │
│  │  GET  /check-updates                │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Row Level Security (RLS)           │    │
│  │  Mỗi user chỉ thấy license của mình│    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### Thiết kế License Manager trong kiến trúc

License Manager nên nằm ở **shared infrastructure** — hoạt động xuyên suốt, mọi feature đều kiểm tra qua nó:

```python
# shared/license/license_manager.py

class LicenseManager:
    """Quản lý bản quyền — kiểm tra local trước, online sau."""

    def __init__(self, supabase_client, local_cache_path: str):
        self.client = supabase_client
        self.cache_path = local_cache_path
        self.OFFLINE_GRACE_DAYS = 7    # Cho phép dùng 7 ngày không có mạng

    def validate(self, license_key: str) -> LicenseInfo:
        """
        1. Kiểm tra cache local trước (nhanh, không cần mạng)
        2. Nếu cache hết hạn → gọi Supabase kiểm tra online
        3. Nếu không có mạng → cho phép dùng nếu còn trong grace period
        """
        cached = self._check_local_cache()
        if cached and not cached.is_expired():
            return cached

        try:
            # Gọi Supabase Edge Function
            result = self.client.functions.invoke("validate-license", {
                "license_key": license_key,
                "machine_id": self._get_machine_fingerprint()
            })
            license_info = LicenseInfo.from_response(result)
            self._update_local_cache(license_info)    # Lưu cache
            return license_info
        except ConnectionError:
            # Không có mạng → dùng offline grace period
            if cached and cached.days_since_last_check < self.OFFLINE_GRACE_DAYS:
                return cached
            raise LicenseError("Cần kết nối internet để xác thực bản quyền")

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Kiểm tra feature có được bật cho tier hiện tại không."""
        license = self.validate(self._stored_key)
        return feature_name in license.features_enabled

    def _get_machine_fingerprint(self) -> str:
        """Tạo ID duy nhất cho máy (dựa trên CPU, disk, MAC address)."""
        ...
```

### Feature gating (giới hạn tính năng) theo tier

```python
# Ví dụ phân quyền theo gói
TIER_FEATURES = {
    "free": [
        "generate_subtitles",          # Tạo phụ đề
        "asr_cloud_api_only",          # Chỉ dùng Cloud ASR (giới hạn 10 phút/tháng)
    ],
    "pro": [
        "generate_subtitles",
        "full_auto_dubbing",           # Lồng tiếng đầy đủ
        "voice_cloning_studio",        # Studio clone giọng
        "all_asr_plugins",             # Mọi plugin ASR
        "all_tts_plugins",             # Mọi plugin TTS
        "unlimited_usage",             # Không giới hạn
    ],
    "enterprise": [
        "*",                           # Tất cả tính năng
        "batch_processing",            # Xử lý hàng loạt
        "priority_support",            # Hỗ trợ ưu tiên
        "custom_model_integration",    # Tích hợp model riêng
    ]
}
```

### Tại sao Supabase + Self-built là lựa chọn tốt nhất

| Tiêu chí | Supabase tự xây | Keygen.sh | Tự host hoàn toàn |
|---|---|---|---|
| **Chi phí khởi đầu** | ✅ $0 | ✅ $0 (100 licenses) | ❌ Cần VPS (~$5-10/tháng) |
| **Chi phí scale** | ✅ Free tier rất lớn | ⚠️ $49/tháng từ 101 licenses | ✅ Chỉ phí hosting |
| **Linh hoạt** | ✅ Toàn quyền thiết kế | ⚠️ Theo framework Keygen | ✅ Toàn quyền |
| **Offline support** | ✅ Tự thiết kế grace period | ✅ Có sẵn | ✅ Tự thiết kế |
| **Bảo trì** | ✅ Supabase lo server | ✅ Keygen lo server | ❌ Tự bảo trì mọi thứ |
| **Chống crack** | ⚠️ Trung bình (cần thêm obfuscation) | ✅ Tốt (machine fingerprint) | ⚠️ Tùy thiết kế |
| **Tích hợp với hệ thống** | ✅ Dùng cùng Supabase cho auth + analytics | ⚠️ Chỉ license | ✅ Tùy thiết kế |

> [!TIP]
> **Khuyến nghị:** Dùng **Supabase** làm license server vì:
> 1. **Miễn phí** đến quy mô rất lớn (50K users/tháng)
> 2. **Đa năng** — ngoài license, còn dùng cho: user auth, usage analytics, crash reporting, update notification
> 3. **Self-host được** — nếu sau này muốn kiểm soát hoàn toàn, Supabase là open-source, có thể deploy trên server riêng
> 4. **Row Level Security** — bảo mật ở database level, mỗi user chỉ truy cập được data của mình
>
> Keygen.sh là backup plan tốt nếu bạn cần tính năng anti-piracy (chống crack) mạnh hơn ở giai đoạn sau.

---

# PHẦN D — MA TRẬN ƯU TIÊN TỔNG HỢP

| # | Tính chất | Giải nghĩa dễ hiểu | Loại | Mức ưu tiên | Lý do |
|---|---|---|---|---|---|
| 1 | UI Thread Sanctity | **Bảo vệ giao diện** — giao diện không bao giờ bị đơ | Vật lý | 🔴 **BẮT BUỘC** | Vi phạm = app đơ = user bỏ |
| 2 | Event-Driven Reactivity | **Giao tiếp bằng sự kiện** — gửi lệnh rồi đi, không đứng chờ | Logic | 🔴 **BẮT BUỘC** | Cơ chế duy nhất đảm bảo giao diện mượt (#1) |
| 3 | Dependency Inversion | **Đảo ngược phụ thuộc** — code chính không gắn chặt vào model cụ thể | Logic | 🔴 **BẮT BUỘC** | Không có = không thể thay đổi model/API |
| 4 | Contract-First Design | **Hợp đồng dữ liệu** — thống nhất format vào/ra trước khi code | Logic | 🔴 **BẮT BUỘC** | Nền tảng cho #3 hoạt động |
| 5 | Separation of Concerns | **Phân tách trách nhiệm** — mỗi module chỉ làm 1 việc | Logic | 🔴 **BẮT BUỘC** | Vi phạm = code rối, không bảo trì được sau 3 tháng |
| 6 | Fault Isolation & Recovery | **Cô lập lỗi + phục hồi** — lỗi ở 1 bước không mất toàn bộ | Logic | 🟡 **RẤT NÊN CÓ** | Thiếu = user mất hàng giờ khi pipeline lỗi |
| 7 | Centralized State | **Trạng thái tập trung** — 1 nơi duy nhất lưu dữ liệu chia sẻ | Logic | 🟡 **RẤT NÊN CÓ** | Thiếu = dữ liệu không đồng bộ giữa các tab |
| 8 | Pipeline Composability | **Tổ hợp pipeline** — quy trình là config, không phải code cứng | Logic | 🟡 **RẤT NÊN CÓ** | Thiếu = khó thêm use case mới |
| 9 | Process Isolation (AI) | **Cô lập tiến trình** — mỗi model AI chạy trong "hộp" riêng | Vật lý | 🟡 **RẤT NÊN CÓ** | Thiếu = model crash kéo toàn bộ app crash |
| 10 | Resource-Aware Scheduling | **Lập lịch theo tài nguyên** — kiểm tra GPU/RAM trước khi chạy | Vật lý | 🟡 **RẤT NÊN CÓ** | Thiếu = hết bộ nhớ GPU → crash |
| 11 | Data Locality & Checkpoint | **Lưu dữ liệu + điểm phục hồi** — "save game" sau mỗi bước | Vật lý | 🟡 **RẤT NÊN CÓ** | Thiếu = mất toàn bộ khi lỗi/mất điện |
| 12 | License Management | **Kiểm tra bản quyền** — xác thực license, phân quyền tính năng | Vật lý | 🟡 **RẤT NÊN CÓ** | Bảo vệ doanh thu, phân biệt tier |
| 13 | Environment Isolation | **Cô lập môi trường** — mỗi model có Python env riêng | Vật lý | 🟢 Nên có | v1 có thể dùng chung nếu thư viện không xung đột |
| 14 | Lightweight Packaging | **Đóng gói nhẹ** — installer nhỏ, tải thêm plugin sau | Vật lý | 🟢 Nên có | v1 có thể yêu cầu user cài thủ công |

> [!IMPORTANT]
> **5 tính chất đầu tiên (🔴) là nền tảng không thể thỏa hiệp.** Nếu thiếu bất kỳ tính chất nào trong 5 này, hệ thống sẽ gặp vấn đề nghiêm trọng sớm hay muộn — bất kể code có sạch đến đâu.

---

*Phân tích bởi chuyên gia thiết kế hệ thống desktop — dựa trên kinh nghiệm thực tế với các ứng dụng AI desktop phức tạp.*
