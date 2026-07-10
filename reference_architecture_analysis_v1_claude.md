# Từ Product Architecture Đến Reference Architecture — Phân Tích Bản Chất

> Câu hỏi: *"Nếu video dubbing chỉ là MỘT MẪU trong một lớp hệ thống phổ biến, thì bản chất seed documents có còn là PRD không?"*

---

## Câu Trả Lời Ngắn

**Không.** Bạn đúng hoàn toàn. Khi mục tiêu chuyển từ *"thiết kế 1 sản phẩm cụ thể"* sang *"xây dựng 1 thiết kế tiêu chuẩn cho 1 lớp hệ thống"*, thì **PRD không còn là seed** — vì PRD gắn chặt với 1 sản phẩm cụ thể.

Seed thực sự lúc này là: **Problem Space Definition** — định nghĩa không gian vấn đề mà lớp hệ thống này phải giải quyết.

---

## Phân Tích Chi Tiết

### Hai cách tiếp cận kiến trúc hoàn toàn khác nhau

```
╔════════════════════════════════╦════════════════════════════════════╗
║   PRODUCT ARCHITECTURE         ║   REFERENCE ARCHITECTURE           ║
║   (Kiến trúc sản phẩm)        ║   (Kiến trúc khuôn mẫu)           ║
╠════════════════════════════════╬════════════════════════════════════╣
║                                ║                                    ║
║   Mục tiêu:                   ║   Mục tiêu:                       ║
║   Build 1 sản phẩm cụ thể    ║   Tạo khuôn mẫu áp dụng cho      ║
║   (Video Dubbing App)          ║   NHIỀU sản phẩm cùng loại       ║
║                                ║                                    ║
║   Seed: PRD                    ║   Seed: Problem Space Definition  ║
║   "Sản phẩm này làm gì?"     ║   "Lớp hệ thống này đối mặt      ║
║                                ║    với những thách thức gì?"       ║
║                                ║                                    ║
║   Output: 1 bộ tài liệu      ║   Output: 1 TEMPLATE + N bộ      ║
║   cho 1 hệ thống              ║   tài liệu cho N hệ thống        ║
║                                ║                                    ║
║   Ví dụ:                      ║   Ví dụ:                          ║
║   "Dùng WhisperX cho ASR"     ║   "Module ASR phải tuân thủ       ║
║                                ║    ASREngine interface, dùng       ║
║                                ║    model nào là config"            ║
║                                ║                                    ║
╚════════════════════════════════╩════════════════════════════════════╝
```

### Video Dubbing thuộc lớp hệ thống nào?

Khi bạn trừu tượng hóa Video Dubbing App, bản chất nó thuộc **System Archetype** (kiểu mẫu hệ thống):

**"Desktop Application with Heavy AI Multi-Step Pipeline Processing"**

Hay ngắn gọn: **Desktop AI Pipeline App**

Và đây là các hệ thống khác CÙNG archetype:

| Hệ thống cụ thể | Pipeline | AI Models | Domain |
|---|---|---|---|
| **Video Dubbing** | Demux→ASR→Translate→TTS→Mix→Mux | Whisper, XTTS, DeepL | Audio/Video |
| **AI Video Editing** | Import→Detect→Style Transfer→Upscale→Export | YOLO, Stable Diffusion, Real-ESRGAN | Video |
| **AI Audio Production** | Import→Separate→Enhance→Mix→Master→Export | Demucs, RVC, UVR | Audio |
| **AI Document Processing** | Scan→OCR→Classify→Extract→Translate→Format | Tesseract, LayoutLM, GPT | Document |
| **AI Medical Imaging** | Import→Preprocess→Detect→Segment→Annotate→Report | U-Net, MONAI, SAM | Medical |
| **AI Photo Editing Suite** | Import→Detect→Remove/Replace→Enhance→Export | SAM, Stable Diffusion, GFPGAN | Image |
| **AI Music Production** | Import→Transcribe→Arrange→Generate→Mix→Master | Whisper, MusicGen, Suno | Music |

> [!IMPORTANT]
> **Nhận xét quan trọng:** Tất cả các hệ thống trên đều chia sẻ **cùng một tập thách thức kiến trúc** mà `architecture_properties_v2.md` đã mô tả:
> - UI Thread phải được bảo vệ (vì AI inference nặng)
> - Cần Plugin/Adapter architecture (vì AI model thay đổi liên tục)
> - Cần Pipeline composability (vì quy trình có nhiều bước)
> - Cần Process isolation (vì GPU/VRAM có giới hạn)
> - Cần Checkpoint/Resume (vì pipeline chạy lâu, có thể lỗi)
>
> **Các thách thức này là BẤT BIẾN (invariant) cho cả lớp hệ thống.** Chỉ có domain cụ thể (dubbing, editing, medical...) và model cụ thể (Whisper, YOLO, U-Net...) là thay đổi.

---

## Bản Chất: Invariant vs Variable

Đây là bước tư duy then chốt. Khi thiết kế Reference Architecture, việc đầu tiên là **tách rõ cái gì bất biến, cái gì thay đổi:**

### Invariant (Bất biến — đúng cho MỌI hệ thống cùng archetype)

```
┌─────────────────────────────────────────────────────────────────┐
│                     INVARIANT LAYER                             │
│              (Không đổi dù domain nào)                         │
│                                                                 │
│  ┌──────────────────┐  ┌───────────────────┐  ┌─────────────┐  │
│  │ UI Thread        │  │ Event-Driven      │  │ Global      │  │
│  │ Protection       │  │ Architecture      │  │ State       │  │
│  │                  │  │                   │  │ Management  │  │
│  │ Main Thread chỉ  │  │ Signal/Slot +     │  │             │  │
│  │ vẽ UI, không     │  │ Dispatch/Listen   │  │ Single      │  │
│  │ chạy AI          │  │                   │  │ source of   │  │
│  │                  │  │                   │  │ truth       │  │
│  └──────────────────┘  └───────────────────┘  └─────────────┘  │
│                                                                 │
│  ┌──────────────────┐  ┌───────────────────┐  ┌─────────────┐  │
│  │ Plugin           │  │ Pipeline Engine   │  │ Resource    │  │
│  │ Architecture     │  │                   │  │ Manager     │  │
│  │                  │  │ DAG-based step    │  │             │  │
│  │ Interface →      │  │ execution with    │  │ VRAM/RAM    │  │
│  │ Adapter →        │  │ checkpoint/resume │  │ aware       │  │
│  │ Registry         │  │                   │  │ scheduling  │  │
│  └──────────────────┘  └───────────────────┘  └─────────────┘  │
│                                                                 │
│  ┌──────────────────┐  ┌───────────────────┐  ┌─────────────┐  │
│  │ Process          │  │ IPC Layer         │  │ Fault       │  │
│  │ Isolation        │  │                   │  │ Isolation   │  │
│  │                  │  │ HTTP/gRPC giữa    │  │ & Recovery  │  │
│  │ Mỗi AI model    │  │ main app và AI    │  │             │  │
│  │ = 1 subprocess   │  │ subprocess        │  │ Checkpoint  │  │
│  │                  │  │                   │  │ + Resume    │  │
│  └──────────────────┘  └───────────────────┘  └─────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Variable (Thay đổi — mỗi sản phẩm cụ thể điền vào)

```
┌─────────────────────────────────────────────────────────────────┐
│                     VARIABLE LAYER                              │
│              (Mỗi sản phẩm cụ thể khác nhau)                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ DOMAIN CONFIG (Config nghiệp vụ)                        │   │
│  │                                                          │   │
│  │ • Pipeline steps cụ thể: [Demux→ASR→Translate→TTS→...]  │   │
│  │ • Data contracts: TranscriptionResult, TranslationResult │   │
│  │ • Domain-specific UI: Timeline editor, Waveform viewer   │   │
│  │ • Domain terminology: "segment", "vocal", "subtitle"     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ PLUGIN IMPLEMENTATIONS (Các plugin cụ thể)              │   │
│  │                                                          │   │
│  │ • Dubbing: WhisperX, XTTS, DeepL, FFmpeg               │   │
│  │ • Video Edit: YOLO, Stable Diffusion, Real-ESRGAN       │   │
│  │ • Medical: U-Net, MONAI, SAM                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ PRODUCT DECISIONS (Quyết định sản phẩm)                 │   │
│  │                                                          │   │
│  │ • Target users, pricing, features per tier              │   │
│  │ • Supported languages/formats                            │   │
│  │ • Performance targets cụ thể                             │   │
│  │ • Branding, UX style                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Seed Documents Cho Reference Architecture

Khi mục tiêu là Reference Architecture, 5 Seed cũ **thay đổi hoàn toàn** thành 3 Seed mới:

```
Product Architecture (5 Seed)          Reference Architecture (3 Seed)
═══════════════════════════           ═══════════════════════════════

A. PRD (Sản phẩm cụ thể)      ──►    R1. System Archetype Definition
                                          (Định nghĩa kiểu mẫu hệ thống)
B. Technical Decisions         ──►    
                                      R2. Architecture Pattern Catalog
                                          (Danh mục pattern giải quyết
C. Domain Knowledge            ──►         thách thức bất biến)

D. Non-Functional Requirements ──►    R3. Product Configuration Schema
                                          (Khuôn mẫu để mỗi sản phẩm
E. Business Constraints        ──►         cụ thể điền vào)
```

> [!IMPORTANT]
> **Sự khác biệt cốt lõi:**
> - **Product seed (5 docs):** Trả lời "Sản phẩm CỤ THỂ này là gì?"
> - **Reference seed (3 docs):** Trả lời "LỚP HỆ THỐNG này đối mặt với thách thức gì, giải bằng pattern nào, và mỗi sản phẩm cụ thể cần điền vào chỗ nào?"
>
> PRD bị **hạ cấp** từ "seed document" xuống thành "configuration input" — nó chỉ là 1 bộ giá trị cụ thể được điền vào Schema (Seed R3).

---

### Seed R1: System Archetype Definition

**Bản chất:** Thay vì mô tả "Video Dubbing App làm gì", mô tả **"Lớp hệ thống Desktop AI Pipeline có đặc điểm kỹ thuật bất biến gì"**.

```markdown
# System Archetype: Desktop AI Pipeline Application

## 1. Định nghĩa Archetype

Một hệ thống thuộc archetype này khi thỏa MÃN TẤT CẢ các tiêu chí:

| # | Tiêu chí bắt buộc | Giải thích |
|---|---|---|
| 1 | Chạy trên desktop (Windows/macOS/Linux) | Không phải web app, không phải mobile |
| 2 | Xử lý AI/ML inference nặng | Cần GPU, model > 1GB, inference > 5 giây |
| 3 | Quy trình nhiều bước (pipeline) | ≥ 3 bước nối tiếp/song song |
| 4 | Đa dạng model/API có thể thay thế | Mỗi bước có ≥ 2 lựa chọn công nghệ |
| 5 | User là end-user, không phải developer | Cần UI thân thiện, error handling tốt |
| 6 | Hỗ trợ cả offline (local model) lẫn online (cloud API) | Hybrid execution |

## 2. Thách Thức Bất Biến (Invariant Challenges)

Mọi hệ thống thuộc archetype này LUÔN đối mặt với:

### Challenge 1: UI Responsiveness Under Heavy Compute
- Bài toán: AI inference chiếm CPU/GPU → UI thread bị block → app đơ
- Tại sao bất biến: Bất kỳ AI model nào (NLP, vision, audio) đều 
  cần ≥ vài giây inference
- Thước đo: UI response time PHẢI < 100ms bất kể AI đang làm gì

### Challenge 2: Technology Volatility
- Bài toán: Model state-of-the-art thay đổi mỗi 3-6 tháng
- Tại sao bất biến: Đúng cho mọi domain AI (NLP, vision, audio, medical)
- Thước đo: Thay model = viết 1 adapter (~200 dòng), không sửa core

### Challenge 3: Resource Scarcity on Single Machine
- Bài toán: GPU VRAM có giới hạn (8-24GB), không thể scale up
- Tại sao bất biến: Desktop = hardware cố định
- Thước đo: Hệ thống PHẢI hoạt động trên GPU 6GB VRAM (degraded mode)

### Challenge 4: Pipeline Reliability
- Bài toán: Pipeline dài → xác suất lỗi tỷ lệ thuận với số bước
- Tại sao bất biến: Bất kỳ pipeline ≥ 3 bước nào cũng có rủi ro
- Thước đo: Lỗi ở bước N → mất tối đa kết quả bước N, không mất 1→(N-1)

### Challenge 5: Environment Fragmentation
- Bài toán: Mỗi AI model cần Python packages khác nhau, có thể xung đột
- Tại sao bất biến: PyTorch, TensorFlow, ONNX có dependency trees phức tạp
- Thước đo: Thêm model mới KHÔNG ảnh hưởng model cũ đang hoạt động

### Challenge 6: Deployment Complexity
- Bài toán: App + AI models + GPU drivers = installer phức tạp nhất
- Tại sao bất biến: AI models luôn lớn (GB), GPU drivers luôn phức tạp
- Thước đo: Core app cài trong < 5 phút, models tải theo nhu cầu

## 3. Dimensions of Variation (Các chiều thay đổi giữa sản phẩm)

| Dimension | Ví dụ giá trị | Ảnh hưởng kiến trúc |
|---|---|---|
| Domain | Audio, Video, Document, Medical | Data contracts, UI widgets |
| Pipeline shape | Linear, DAG, Branching | Pipeline engine config |
| Model types | NLP, CV, Audio, Multimodal | Plugin implementations |
| Interaction mode | Batch / Interactive / Hybrid | UI flow, state machine |
| Scale | Single user / LAN / Cloud | IPC mechanism, deployment |
| License model | Free / Freemium / Enterprise | License manager config |
```

**So sánh với `architecture_properties_v2.md`:**

Tài liệu hiện tại đã làm được **60-70% của Seed R1** — nó mô tả rất tốt các thách thức bất biến. Nhưng nó **trộn lẫn** invariant với product-specific:

| Nội dung trong v2.md | Invariant hay Variable? |
|---|---|
| "UI Thread Sanctity" — bảo vệ UI thread | ✅ **Invariant** — đúng cho mọi Desktop AI Pipeline |
| "Pipeline gồm Demux→ASR→Translate→TTS→Mix→Mux" | ❌ **Variable** — chỉ đúng cho dubbing |
| "Event-Driven Reactivity" — giao tiếp sự kiện | ✅ **Invariant** |
| "WhisperX cần 3.5GB VRAM" | ❌ **Variable** — chỉ đúng cho ASR models |
| "Dependency Inversion" — đảo ngược phụ thuộc | ✅ **Invariant** |
| "Coqui XTTS v2 cho voice cloning" | ❌ **Variable** — chỉ đúng cho dubbing |
| "Process Isolation" — cô lập tiến trình | ✅ **Invariant** |
| "Supabase cho license" | ❌ **Variable** — chỉ 1 lựa chọn cụ thể |

> [!TIP]
> **Để chuyển v2.md thành Reference Architecture Seed R1:** Tách toàn bộ nội dung product-specific (cột "Variable") ra thành ví dụ minh họa (examples), giữ lại phần Invariant làm core. Các ví dụ dubbing trở thành 1 "sample configuration" — không phải bản thiết kế chính.

---

### Seed R2: Architecture Pattern Catalog

**Bản chất:** Thay vì "chọn FastAPI hay Flask?" (quyết định cụ thể), mô tả **"pattern nào giải quyết challenge nào, với trade-off gì"** — rồi mỗi sản phẩm chọn pattern phù hợp.

```markdown
# Architecture Pattern Catalog for Desktop AI Pipeline Apps

## Patterns cho Challenge 1 (UI Responsiveness)

### Pattern 1A: Worker Thread (QThread)
- Cơ chế: Tạo QThread, chạy task nặng trên thread riêng
- Khi nào dùng: Task I/O-bound (đọc file, gọi API)
- Khi nào KHÔNG dùng: Task CPU/GPU-bound (do GIL)
- Effort: Thấp (~50 dòng)

### Pattern 1B: Subprocess + IPC  
- Cơ chế: Spawn subprocess riêng cho AI, giao tiếp qua IPC
- Khi nào dùng: Task CPU/GPU-bound (AI inference)
- Variants:
  - 1B.1: subprocess.Popen + stdin/stdout
  - 1B.2: subprocess + HTTP (FastAPI)    ← Khuyến nghị
  - 1B.3: subprocess + gRPC
- Trade-off: 1B.1 đơn giản nhưng chỉ local; 1B.2 linh hoạt hơn
- Effort: Trung bình (~200-500 dòng)

### Pattern 1C: Message Queue
- Cơ chế: Dùng message broker (ZeroMQ, RabbitMQ)
- Khi nào dùng: Khi cần scale > 1 máy + high throughput
- Khi nào KHÔNG dùng: v1 đơn giản
- Trade-off: Phức tạp hơn, thêm dependency
- Effort: Cao

## Patterns cho Challenge 2 (Technology Volatility)

### Pattern 2A: Plugin Architecture (Interface + Adapter + Registry)
- Cơ chế: Định nghĩa interface → mỗi model = 1 adapter implement
- Bắt buộc: Có — đây là pattern DUY NHẤT đúng cho challenge này
- Variants:
  - 2A.1: Static registry (code-level, đăng ký khi compile)
  - 2A.2: Dynamic registry (file-based, scan folder tìm plugin)
  - 2A.3: Config-driven registry (config file chỉ định plugin)

## Patterns cho Challenge 3 (Resource Scarcity)

### Pattern 3A: Resource Manager + Scheduler
- Cơ chế: Kiểm tra VRAM/RAM trước khi load model, queue task
- ...

### Pattern 3B: Model Lifecycle Manager
- Cơ chế: Load/unload model theo demand, LRU cache
- ...

## Patterns cho Challenge 4 (Pipeline Reliability)

### Pattern 4A: Checkpoint + Resume
- Cơ chế: Lưu state sau mỗi step, resume từ checkpoint khi lỗi
- ...

### Pattern 4B: Saga Pattern (Compensating Transactions)
- Cơ chế: Mỗi step có "undo" action, khi lỗi rollback từng step
- ...

## ... (tương tự cho Challenge 5, 6)
```

**Điểm mấu chốt:** Pattern Catalog **không chọn hộ** — nó trình bày options + trade-offs. Mỗi sản phẩm cụ thể chọn pattern phù hợp với constraints của mình rồi ghi vào Technical Decisions.

---

### Seed R3: Product Configuration Schema

**Bản chất:** Đây là **"form" mà mỗi sản phẩm cụ thể điền vào** để instantiate Reference Architecture thành Product Architecture. PRD, Domain Knowledge, NFR, Business Constraints — tất cả đều trở thành **các trường trong form này.**

```markdown
# Product Configuration Schema
# (Mỗi sản phẩm cụ thể điền vào template này)

## Section 1: Product Identity (Thay PRD)
product_name: "___"
one_liner: "Ứng dụng desktop giúp [ai] làm [gì]"
target_users:
  - persona: "___"
    tech_level: [novice / intermediate / advanced]
    hardware: "GPU ___, RAM ___ GB"

## Section 2: Domain Pipeline (Thay Domain Knowledge)
pipeline_steps:
  - name: "___"
    type: [ai_inference / tool_execution / user_interaction / data_transform]
    input_contract: "___"   # reference to contract definition
    output_contract: "___"
    duration_estimate: "___"
    # --- Variable per step ---
    available_plugins:
      - name: "___"
        type: [local_model / cloud_api / binary_tool]
        resource_requirements:
          vram_mb: ___
          ram_mb: ___
          
## Section 3: Pattern Selections (Thay Technical Decisions)
selected_patterns:
  ui_responsiveness: "1B.2"   # subprocess + HTTP (FastAPI)
  technology_swap: "2A.3"     # Config-driven plugin registry
  resource_management: "3A"   # Resource Manager + Scheduler
  pipeline_reliability: "4A"  # Checkpoint + Resume
  
## Section 4: Quality Targets (Thay NFR)
performance:
  ui_response_ms: ___
  startup_seconds: ___
  pipeline_throughput: "___"
reliability:
  max_data_loss_minutes: ___
  crash_tolerance: "___"

## Section 5: Deployment Config (Thay Business Constraints)
deployment:
  platforms: [windows / macos / linux]
  gpu_minimum: "___"
  installer_max_size_mb: ___
  model_download_strategy: [bundled / on_demand / hybrid]
scale:
  mode: [single_machine / lan_multi_gpu / cloud]
  max_gpu_nodes: ___
monetization:
  model: [free / freemium / subscription / enterprise]
  tiers: [...]
```

---

## Chuỗi Phụ Thuộc Mới (Reference Architecture)

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   TẦNG 0 — SEED (Con người viết 1 LẦN, áp dụng cho N sản phẩm)║
║                                                                  ║
║   R1. System Archetype Definition                               ║
║       "Desktop AI Pipeline App có thách thức bất biến gì?"      ║
║                                                                  ║
║   R2. Architecture Pattern Catalog                              ║
║       "Pattern nào giải quyết thách thức nào, trade-off gì?"    ║
║                                                                  ║
║   R3. Product Configuration Schema                              ║
║       "Mỗi sản phẩm cụ thể cần điền vào chỗ nào?"             ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                          │                                       ║
║                          │ Viết 1 lần                            ║
║                          ▼                                       ║
║                                                                  ║
║   TẦNG 1 — REFERENCE ARCHITECTURE (Bộ tài liệu khuôn mẫu)     ║
║                                                                  ║
║   ├── Architecture Properties (tính chất bất biến)              ║
║   ├── Architecture Blueprint TEMPLATE                           ║
║   ├── Contract Interface TEMPLATES (chỉ interface, không impl)  ║
║   ├── Pipeline Engine Specification                             ║
║   ├── IPC Protocol Specification                                ║
║   ├── Error Handling Framework                                  ║
║   ├── Testing Framework & Strategy TEMPLATE                     ║
║   └── Deployment Framework TEMPLATE                             ║
║                                                                  ║
║   → Đây là BỘ KHUNG, dùng lại cho mọi sản phẩm               ║
║                                                                  ║
╠════════════════════════════════════════════════════════════╤═════╣
║                          │                                │      ║
║              Điền R3     │                    Điền R3     │      ║
║              Config A    │                    Config B    │      ║
║                          ▼                                ▼      ║
║                                                                  ║
║   TẦNG 2 — PRODUCT ARCHITECTURES (Mỗi sản phẩm 1 bộ)          ║
║                                                                  ║
║   ┌─────────────────────┐        ┌─────────────────────┐        ║
║   │ Video Dubbing App   │        │ AI Photo Editor     │        ║
║   │                     │        │                     │        ║
║   │ Config A:           │        │ Config B:           │        ║
║   │ Pipeline:           │        │ Pipeline:           │        ║
║   │  Demux→ASR→Transl   │        │  Import→Detect→     │        ║
║   │  →TTS→Mix→Mux       │        │  Remove→Enhance→    │        ║
║   │ Plugins:            │        │  Export             │        ║
║   │  WhisperX, XTTS     │        │ Plugins:            │        ║
║   │ Scale: LAN          │        │  SAM, SD, GFPGAN    │        ║
║   │                     │        │ Scale: Single       │        ║
║   └─────────────────────┘        └─────────────────────┘        ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                          │                                       ║
║                          ▼                                       ║
║                                                                  ║
║   TẦNG 3 — CODE (Mỗi sản phẩm share framework, khác plugins)  ║
║                                                                  ║
║   ┌──────────────────────────────────────────────────────────┐  ║
║   │  SHARED FRAMEWORK CODE (core/, engine/, ipc/, ui_base/) │  ║
║   │  → Viết 1 lần, dùng cho mọi sản phẩm                   │  ║
║   └────────────────────────┬─────────────────────────────────┘  ║
║                            │                                     ║
║            ┌───────────────┼───────────────┐                    ║
║            ▼               ▼               ▼                    ║
║   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           ║
║   │ Dubbing     │  │ Photo Edit  │  │ Document    │           ║
║   │ Plugins     │  │ Plugins     │  │ Plugins     │           ║
║   │ + Config    │  │ + Config    │  │ + Config    │           ║
║   │ + UI        │  │ + UI        │  │ + UI        │           ║
║   └─────────────┘  └─────────────┘  └─────────────┘           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Đánh Giá Lại `architecture_properties_v2.md` Dưới Góc Nhìn Mới

Với góc nhìn Reference Architecture, tài liệu hiện tại:

| Khía cạnh | Đánh giá |
|---|---|
| **Mô tả thách thức bất biến** | ✅ Xuất sắc — 14 tính chất đều là invariant challenges thật |
| **Tách biệt invariant vs variable** | ❌ Chưa tách — trộn lẫn nguyên tắc với ví dụ cụ thể dubbing |
| **Pattern catalog** | ⚠️ Có một phần (mô tả patterns) nhưng trộn với product decisions |
| **Configuration schema** | ❌ Chưa có — không rõ "chỗ nào mỗi sản phẩm điền vào" |
| **Khả năng tái sử dụng** | ⚠️ 60-70% nội dung tái sử dụng được nếu tách invariant ra |

### Cần làm gì để chuyển đổi?

```
architecture_properties_v2.md (hiện tại)
           │
           │ Refactor
           ▼
┌──────────────────────────────┐     ┌────────────────────────────┐
│ reference_architecture.md    │     │ dubbing_product_config.md  │
│                              │     │                            │
│ Chỉ chứa INVARIANT:         │     │ Chỉ chứa VARIABLE:        │
│ • 14 tính chất bất biến     │     │ • Pipeline: Demux→ASR→...  │
│ • Thách thức chung           │     │ • Models: WhisperX, XTTS   │
│ • Pattern options            │     │ • NFR cụ thể               │
│ • Interface templates        │     │ • Business config          │
│                              │     │                            │
│ Áp dụng cho: N sản phẩm    │     │ Áp dụng cho: 1 sản phẩm   │
└──────────────────────────────┘     └────────────────────────────┘
```

> [!IMPORTANT]
> **Kết luận cuối cùng:**
>
> Bạn hoàn toàn đúng — khi hướng đến thiết kế tiêu chuẩn, bản chất **KHÔNG** xuất phát từ 5 seed cũ (PRD-centric). Mà xuất phát từ **3 seed mới** hướng kỹ thuật:
>
> 1. **System Archetype Definition** — "Lớp hệ thống này là gì, thách thức bất biến là gì?"
> 2. **Architecture Pattern Catalog** — "Pattern nào giải thách thức nào?"
> 3. **Product Configuration Schema** — "Mỗi sản phẩm cụ thể điền gì vào đâu?"
>
> PRD, Domain Knowledge, NFR, Business Constraints — tất cả đều **hạ cấp** thành *giá trị cấu hình* (configuration values) được điền vào Schema, thay vì là seed documents.
>
> `architecture_properties_v2.md` hiện tại đã làm tốt 60-70% Seed R1, nhưng cần **tách invariant khỏi product-specific** để thực sự trở thành Reference Architecture seed.
