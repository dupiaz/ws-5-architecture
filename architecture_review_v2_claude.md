# Đánh Giá Toàn Diện: architecture_properties_v2.md

> Đánh giá dưới góc nhìn của một kiến trúc sư hệ thống phần mềm lão luyện, chuyên thiết kế hệ thống hiệu năng cao, dễ bảo trì, ít nợ kỹ thuật và dễ mở rộng.

---

## 1. Tài Liệu Này Là Loại Gì?

**Phân loại:** Đây là tài liệu **Architecture Decision Record + Architecture Properties Specification** (Tài liệu ghi nhận quyết định kiến trúc kết hợp đặc tả các tính chất kiến trúc).

Cụ thể hơn, tài liệu này nằm ở **tầng trung gian** giữa:

| Tầng tài liệu | Tài liệu này có? | Mức độ |
|---|---|---|
| **Vision & Strategy** (Tầm nhìn & chiến lược sản phẩm) | ⚠️ Có một phần (mô tả pipeline, user personas) | Sơ lược |
| **Architecture Properties / Quality Attributes** (Tính chất kiến trúc) | ✅ **Đây là trọng tâm** | Chi tiết tốt |
| **Architecture Decision Records (ADR)** (Ghi nhận quyết định kiến trúc) | ✅ Có (giải thích *tại sao* chọn Event-Driven, DI, Process Isolation...) | Khá tốt |
| **Technical Architecture Document (TAD)** (Tài liệu kiến trúc kỹ thuật) | ⚠️ Có phác thảo (sơ đồ process model, folder structure) | Sơ bộ |
| **Detailed Design Document (DDD)** | ❌ Không có | Thiếu hoàn toàn |
| **API/Contract Specification** | ⚠️ Có ví dụ minh họa nhưng chưa đầy đủ | Mẫu thử |

### Đánh giá tổng quan

> [!IMPORTANT]
> Đây là một tài liệu **giáo dục kiến trúc (Architecture Education)** xuất sắc, kết hợp giữa *lý thuyết thiết kế* và *ngữ cảnh domain cụ thể*. Tác giả rõ ràng có kinh nghiệm thực chiến với cả Python desktop app và AI inference pipeline.

**Điểm mạnh nổi bật:**
- Giải thích **"tại sao"** (rationale) rất tốt — đây là yếu tố quan trọng nhất mà phần lớn tài liệu kiến trúc bỏ qua
- Bảng thuật ngữ toàn diện — giúp bridge knowledge gap giữa người kỹ thuật và phi kỹ thuật
- Sơ đồ ASCII trực quan, dễ hiểu, không phụ thuộc công cụ bên ngoài
- Code examples có context thực tế, không abstract quá mức
- Ma trận ưu tiên cuối tài liệu rất hữu ích cho việc phân chia giai đoạn triển khai (phasing)

---

## 2. Tài Liệu Này Có Đủ Để Lập Trình Viên / Agent Hiểu Và Build Hệ Thống?

### Câu trả lời ngắn: **KHÔNG ĐỦ**

### Câu trả lời chi tiết:

Tài liệu này giống như có **bản vẽ tổng thể** (master plan) của một tòa nhà chung cư — bạn biết nó phải có bao nhiêu tầng, phải chống động đất cấp mấy, phải có thang máy hay thang bộ, phải dùng kết cấu thép hay bê tông cốt thép. Nhưng bạn **chưa có**:
- Bản vẽ chi tiết từng tầng (floor plan)
- Bản vẽ kết cấu (structural plan)
- Bản vẽ điện nước (MEP plan)
- Danh sách vật tư và nhà cung cấp (BOM)
- Quy trình thi công (construction plan)

### Phân tích GAP chi tiết — 9 khoảng trống quan trọng

---

#### GAP 1: 🔴 Thiếu Architecture Blueprint (Bản Vẽ Kiến Trúc Tổng Thể)

**Tài liệu mô tả *nguyên tắc* nhưng chưa mô tả *hình hài cụ thể* của hệ thống.**

| Có trong tài liệu | Thiếu |
|---|---|
| "Cần Separation of Concerns" | Cụ thể hệ thống có bao nhiêu layer? Tên từng layer? |
| "Cần Event-Driven" | Event Bus cụ thể là custom-built hay dùng thư viện có sẵn? Schema event thế nào? |
| "Cần Process Isolation" | Bao nhiêu process? Process nào spawn trước? Lifecycle của mỗi process? |
| "Cần Centralized State" | State tree cụ thể gồm những gì? Phân slice thế nào? Persistence strategy? |

**Hệ quả nếu không bổ sung:** Lập trình viên / agent sẽ **tự sáng tạo** cấu trúc → mỗi người/agent hiểu khác nhau → mất tính nhất quán (consistency) → nợ kỹ thuật tích lũy từ sprint đầu tiên.

**Cần bổ sung:**
- **Component Diagram** (C4 Level 2-3): Mô tả chính xác từng component, boundary, dependency
- **Package/Module Structure**: Cây thư mục đầy đủ với mô tả trách nhiệm từng package
- **Data Flow Diagram**: Luồng dữ liệu end-to-end cho mỗi use case chính

---

#### GAP 2: 🔴 Thiếu API & Contract Specification Đầy Đủ

Tài liệu nhắc đến Contract-First Design (rất đúng!) nhưng **chỉ cho ví dụ 1 contract** (`TranscriptionResult` cho ASR). Hệ thống có **ít nhất 6 contract chính**:

| Contract | Có trong tài liệu? | Quan trọng? |
|---|---|---|
| ASR Input/Output | ✅ Có ví dụ `TranscriptionResult` | Rất |
| Translation Input/Output | ❌ Chưa có | Rất |
| TTS Input/Output | ❌ Chưa có | Rất |
| Demux/Mux Input/Output | ❌ Chưa có | Quan trọng |
| Audio Mix Input/Output | ❌ Chưa có | Quan trọng |
| Pipeline Step Interface | ⚠️ Có sơ bộ (class `Step`) nhưng chưa chi tiết | Cực kỳ quan trọng |
| Event Schema (Event Bus messages) | ❌ Chưa có | Rất |
| Plugin Registration/Discovery Contract | ❌ Chưa có | Rất |

**Hệ quả nếu không bổ sung:** Mỗi lập trình viên / agent tự thiết kế contract → contract không tương thích giữa các module → integration hell (địa ngục tích hợp).

**Cần bổ sung:**
- **Tài liệu Contract Specification** hoàn chỉnh cho tất cả interface giữa các module
- Định nghĩa bằng Python dataclass hoặc Pydantic model, bao gồm validation rules, optional fields, versioning strategy

---

#### GAP 3: 🔴 Thiếu Sequence Diagrams (Sơ Đồ Tuần Tự)

Tài liệu có 1 sơ đồ tương tác UI↔Worker khá tốt (mục Event-Driven). Nhưng hệ thống có **hàng chục luồng tương tác phức tạp** chưa được mô tả:

- **Startup sequence**: App khởi động → Load config → Validate license → Init stores → Init plugin registry → Show UI
- **Pipeline execution flow**: User bấm "Bắt đầu" → Orchestrator nhận lệnh → Kiểm tra resource → Spawn subprocess → Chạy từng step → Checkpoint → Emit progress → Handle error/retry → Complete
- **Plugin hot-swap**: User đổi ASR plugin giữa chừng → Unload model cũ → Free VRAM → Load model mới
- **Error recovery flow**: Step thất bại → Checkpoint → Hiện dialog "Thử lại / Bỏ qua / Chạy lại từ đầu" → Resume
- **License validation flow**: Startup check → Cache check → Online verify → Offline grace → Feature gating
- **IPC lifecycle**: Main process ↔ AI subprocess: spawn, healthcheck, request/response, crash detection, restart

**Hệ quả nếu không bổ sung:** Agent sẽ triển khai theo cách nó "tưởng tượng" luồng xử lý → race condition, resource leak, deadlock — **loại bug khó debug nhất**.

---

#### GAP 4: 🟡 Thiếu Error Taxonomy & Error Handling Strategy

Tài liệu nhắc "Fault Isolation & Recovery" nhưng chưa phân loại lỗi cụ thể. Trong hệ thống AI desktop, có **ít nhất 5 nhóm lỗi** với chiến lược xử lý hoàn toàn khác nhau:

| Nhóm lỗi | Ví dụ | Chiến lược |
|---|---|---|
| **Recoverable AI Error** | API rate limit, timeout | Auto-retry với exponential backoff |
| **Fatal AI Error** | CUDA OOM, segfault | Kill subprocess, thông báo user, gợi ý giải pháp |
| **Data Error** | Audio file corrupt, unsupported format | Validate trước khi đưa vào pipeline, skip segment |
| **Infrastructure Error** | Disk full, permission denied | Pre-flight check, thông báo rõ ràng |
| **User Error** | API key sai, chọn model quá lớn cho GPU | Validate ngay khi nhập, không cho bắt đầu pipeline |

**Cần bổ sung:**
- Error code catalog
- Error handling strategy per error type
- User-facing error message guidelines
- Logging strategy (structured logging format, log levels, sensitive data redaction)

---

#### GAP 5: 🟡 Thiếu State Machine Diagram Cho Pipeline

Tài liệu mô tả pipeline như DAG (đúng!) nhưng chưa mô tả **state machine** của mỗi pipeline execution:

```
IDLE → VALIDATING → QUEUED → RUNNING → [step states] → COMPLETED
                                  ↓
                              PAUSED ←→ RUNNING
                                  ↓
                              FAILED → RETRYING → RUNNING
                                  ↓
                              CANCELLED
```

Và state machine của mỗi Step:

```
PENDING → INITIALIZING → RUNNING → COMPLETED
                            ↓
                        FAILED → RETRYING → RUNNING
                            ↓
                        SKIPPED
```

**Hệ quả nếu không bổ sung:** Lập trình viên sẽ thiếu xử lý các edge case: user cancel giữa chừng, resume sau crash, retry cụ thể step nào, v.v.

---

#### GAP 6: 🟡 Thiếu Configuration Architecture

Tài liệu nhắc đến config nhiều nơi (plugin config, pipeline config, project config) nhưng chưa trả lời:

- Config nằm ở đâu? 1 file hay nhiều file? Format gì (TOML, YAML, JSON)?
- Config có phân tầng không? (system defaults → user preferences → project-specific)
- Config validation xảy ra ở đâu, khi nào?
- Sensitive config (API keys) lưu và bảo vệ thế nào? (Windows Credential Store? Encrypted file?)
- Config migration khi nâng cấp app version?

---

#### GAP 7: 🟡 Thiếu Testing Strategy

Tài liệu hoàn toàn **không nhắc đến testing**. Đây là khoảng trống đáng lo ngại cho một hệ thống phức tạp:

- **Unit Testing**: Test từng adapter/plugin riêng lẻ, mock AI inference
- **Integration Testing**: Test pipeline end-to-end với lightweight mock services
- **UI Testing**: Test PySide6 widgets (QTest framework)
- **Contract Testing**: Ensure mỗi plugin tuân thủ contract (dùng abstract test class)
- **Performance Testing**: Benchmark inference time, VRAM usage, UI responsiveness

**Cần bổ sung:**
- Testing pyramid strategy
- Mock/Stub strategy cho AI inference (critical — vì bạn không muốn CI/CD phải có GPU)
- Test fixture guidelines (sample audio files, expected outputs)

---

#### GAP 8: 🟡 Thiếu Deployment & Update Strategy Chi Tiết

Tài liệu có phác thảo packaging strategy (NSIS/Inno Setup + first-run wizard) nhưng chưa trả lời:

- **Auto-update mechanism**: App tự cập nhật thế nào? Delta update hay full update?
- **Model versioning**: Khi model weights có phiên bản mới, cơ chế update/rollback?
- **Database migration**: SQLite schema thay đổi giữa các version?
- **Plugin versioning**: Plugin API version compatibility? Backward compatibility policy?
- **Telemetry & Crash Reporting**: Thu thập lỗi từ user (opt-in) để cải thiện chất lượng?

---

#### GAP 9: 🟢 Thiếu Developer Experience (DX) Guidelines

- **Coding standards**: Python code style, naming conventions, docstring format
- **Git workflow**: Branching strategy, commit message format, PR review process
- **Local development setup**: Cách setup dev environment nhanh nhất
- **Architecture decision log**: Nơi ghi nhận các quyết định kỹ thuật tương lai (ADR template)
- **Contribution guide**: Cách thêm plugin mới từ A→Z

---

### Tổng hợp: Tài liệu cần bổ sung

| # | Tài liệu cần bổ sung | Mức độ cấp thiết | Ai hưởng lợi |
|---|---|---|---|
| 1 | **Architecture Blueprint** (Component Diagram C4, Package Structure) | 🔴 Bắt buộc | Dev + Agent |
| 2 | **Contract Specification** đầy đủ cho tất cả module interfaces | 🔴 Bắt buộc | Dev + Agent |
| 3 | **Sequence Diagrams** cho các luồng chính | 🔴 Bắt buộc | Dev + Agent |
| 4 | **Error Handling & Logging Strategy** | 🟡 Rất nên có | Dev + QA |
| 5 | **Pipeline State Machine** specification | 🟡 Rất nên có | Dev + Agent |
| 6 | **Configuration Architecture** | 🟡 Rất nên có | Dev + DevOps |
| 7 | **Testing Strategy** | 🟡 Rất nên có | Dev + QA |
| 8 | **Deployment & Update Strategy** | 🟡 Rất nên có | Dev + DevOps |
| 9 | **Developer Experience Guidelines** | 🟢 Nên có | Dev onboarding |

---

## 3. Ý Kiến Riêng Từ Góc Nhìn Kiến Trúc Sư Hệ Thống

### 🏆 Những Điều Tài Liệu Làm Rất Tốt

**1. Rationale-First Approach (Giải thích "tại sao" trước)**

Đây là phẩm chất hiếm và cực kỳ giá trị. Phần lớn tài liệu kiến trúc chỉ nói "phải làm thế này" mà không giải thích tại sao. Tài liệu này giải thích rõ ràng hậu quả của từng vi phạm, giúp developer hiểu sâu thay vì chỉ tuân thủ máy móc.

**2. Domain-Specific Analysis (Phân tích đặc thù domain)**

Việc đặt mọi tính chất kiến trúc trong bối cảnh cụ thể "Python Desktop + AI Inference" thay vì nói chung chung là rất thực tế. Bảng so sánh VRAM usage, thời gian inference, danh sách model alternatives — tất cả đều cho thấy tác giả hiểu rõ bài toán.

**3. Bảng thuật ngữ và giải thích dễ hiểu**

Cách giải thích GIL bằng ẩn dụ "phòng họp 1 micro", DAG bằng sơ đồ trực quan — giúp bridge gap giữa senior architect và junior developer hiệu quả.

---

### ⚠️ Những Điểm Cần Cân Nhắc Lại

**1. Process Isolation: Nên bắt đầu từ v1 hay v2?**

Tài liệu đề xuất mỗi AI model chạy trong subprocess riêng với FastAPI server. Với yêu cầu hỗ trợ **2 đối tượng** (1 GPU local + multi-GPU trong LAN), **nên bắt đầu từ v2 (HTTP/gRPC) ngay từ đầu** — vì:

> [!IMPORTANT]
> **Lý do chọn v2 trực tiếp:**
> - `multiprocessing.Queue/Pipe` (v1) **chỉ hoạt động trên cùng 1 máy** — không thể gửi task sang GPU trên máy khác trong LAN
> - HTTP/gRPC (v2) hoạt động **đồng nhất** cho cả local subprocess (`127.0.0.1:8001`) lẫn remote machine (`192.168.1.50:8001`) — chỉ đổi địa chỉ IP
> - Chi phí triển khai v2 **không cao hơn nhiều** so với v1 khi dùng FastAPI (thêm ~200-300 dòng boilerplate), nhưng **tránh được việc viết lại** toàn bộ IPC layer khi mở rộng sang LAN
> - v1 (`multiprocessing`) **không giải quyết được** vấn đề Python environment isolation giữa các plugin — vẫn chạy chung interpreter

Chi tiết so sánh cơ chế giao tiếp v1 vs v2 và cách mỗi phương pháp xử lý Python environment isolation → xem [Phụ Lục A](#phụ-lục-a--deep-dive-process-isolation--ipc-mechanisms).

**Roadmap triển khai đề xuất (đã cập nhật):**

| Phase | Scope | IPC | Python Env |
|---|---|---|---|
| **v1** | Single machine, 1 GPU | HTTP localhost (FastAPI) | Isolated venv per service |
| **v2** | LAN multi-GPU | HTTP/gRPC qua LAN, service discovery | Isolated venv, có thể khác OS |
| **v3** | Cloud/Enterprise | Container orchestration (Docker Compose / K8s) | Container image per service |

**2. Supabase Cho License — Rủi Ro Vendor Lock-in**

Tài liệu recommend Supabase khá mạnh mẽ, nhưng:

- Supabase Edge Functions dùng Deno runtime — nếu logic license phức tạp, sẽ bị giới hạn
- Supabase free tier có thể thay đổi policy (đã xảy ra với nhiều BaaS khác)
- Nên thiết kế License Manager theo **Dependency Inversion** (như chính tài liệu đề xuất!) — tạo `LicenseBackend` interface, Supabase chỉ là 1 implementation

Ví dụ code cụ thể với 2 implementation (Supabase + Keygen.sh) → xem [Phụ Lục B](#phụ-lục-b--licensebackend-dependency-inversion-example).

**3. Thiếu Quantitative Quality Targets (Mục Tiêu Chất Lượng Định Lượng)**

Tài liệu nói "UI không được đơ" nhưng chưa định nghĩa:

| Metric | Cần định nghĩa cụ thể |
|---|---|
| UI Responsiveness | Frame budget: mỗi UI update < 16ms (60fps)? < 33ms (30fps)? |
| Startup Time | App cold start < ? giây (không tính model load) |
| Memory Footprint | App chính (không có AI model) < ? MB RAM |
| Pipeline Throughput | Xử lý ? phút video / giờ thực |
| Error Recovery Time | Resume from checkpoint < ? giây |
| Max Concurrent Projects | Hỗ trợ ? project mở đồng thời |

Không có số liệu cụ thể → không thể verify kiến trúc đạt yêu cầu hay không.

**4. Chưa Đề Cập Đến Vấn Đề Bảo Mật Đủ Sâu**

Ngoài license, hệ thống có nhiều attack surface cần xem xét:

- **API Key Storage**: User nhập OpenAI/ElevenLabs API key — lưu ở đâu? Plaintext trong config file là **không chấp nhận được**. Cần Windows DPAPI / Credential Store
- **Arbitrary Code Execution**: AI model từ HuggingFace có thể chứa malicious code (pickle deserialization attack). Cần sandboxing hoặc ít nhất model verification
- **Local HTTP Server**: FastAPI server listen trên localhost — cần bind chính xác `127.0.0.1`, không `0.0.0.0`. Cần authentication token giữa main app và subprocess
- **User Data Privacy**: Audio/video của user có chứa nội dung nhạy cảm — cần policy rõ ràng về data không gửi đi đâu (khi dùng local model), và disclosure khi gửi lên cloud API

**5. Accessibility (Khả Năng Tiếp Cận) Hoàn Toàn Vắng Mặt**

Desktop app cho end-user cần xem xét:

- Keyboard navigation cho toàn bộ UI
- Screen reader support (PySide6 có hỗ trợ Qt Accessibility)
- High contrast mode, font size scaling
- Multi-language UI (i18n/l10n) — khác với translation pipeline

**6. Chưa Address Vấn Đề Python Ecosystem Fragility**

Tài liệu đề cập lo ngại "công nghệ lõi và môi trường Python thay đổi chóng mặt" nhưng chưa đưa ra chiến lược cụ thể:

> [!WARNING]
> **Rủi ro thực tế với Python ecosystem:**
> - PySide6 release cycle không đồng bộ với Qt release → breaking changes tiềm ẩn
> - PyTorch CUDA compatibility matrix phức tạp (PyTorch 2.x chỉ support CUDA 11.8/12.1/12.4)
> - `pip` dependency resolution vẫn là nightmare cho AI projects (torch + numpy + scipy version conflicts)
> - Model API (HuggingFace transformers, Coqui TTS) thay đổi breaking changes giữa minor versions

**Chiến lược nên bổ sung:**
- **Lock file strategy**: `pip-tools` hoặc `uv` với lock files chặt
- **CI matrix testing**: Test trên nhiều Python version (3.10, 3.11, 3.12) và PyTorch version
- **Abstraction boundary**: Core app KHÔNG import torch/transformers trực tiếp — chỉ qua subprocess boundary
- **Graceful degradation**: Nếu một plugin không tương thích, hệ thống vẫn hoạt động với các plugin khác

**7. Performance Architecture Chưa Được Mô Tả**

Với app xử lý video/audio, performance architecture là critical:

- **Streaming vs Batch**: TTS nên stream từng segment hay batch? Audio mixing nên stream pipe hay load toàn bộ vào RAM?
- **Caching Strategy**: Model weights cached ở đâu? Inference results cached không? Cache invalidation?
- **Memory Management**: Khi nào garbage collect? Python GC không đáng tin cho large objects — cần explicit `del` + `gc.collect()` + `torch.cuda.empty_cache()`
- **Disk I/O Optimization**: Intermediate files dùng SSD-friendly format? WAV (uncompressed, fast read) vs FLAC (compressed, slow read)?

---

### 💡 Khuyến Nghị Cuối Cùng: Roadmap Tài Liệu

Nếu tôi là kiến trúc sư trưởng của dự án này, tôi sẽ xây dựng **bộ tài liệu kiến trúc theo thứ tự sau**:

```
Phase 1 — Foundation (Trước khi viết code)
├── ✅ [ĐÃ CÓ] Architecture Properties (tài liệu hiện tại)
├── 📄 [CẦN TẠO] Architecture Blueprint (C4 diagrams, component boundaries)
├── 📄 [CẦN TẠO] Contract Specification (tất cả interface definitions)
└── 📄 [CẦN TẠO] Project Structure & Coding Standards

Phase 2 — Design (Trong khi code v1)
├── 📄 [CẦN TẠO] Sequence Diagrams (top 5 critical flows)
├── 📄 [CẦN TẠO] Pipeline State Machine specification
├── 📄 [CẦN TẠO] Error Handling Strategy
└── 📄 [CẦN TẠO] Configuration Architecture

Phase 3 — Quality (Trước khi release v1)
├── 📄 [CẦN TẠO] Testing Strategy
├── 📄 [CẦN TẠO] Security Guidelines
├── 📄 [CẦN TẠO] Performance Targets & Benchmarks
└── 📄 [CẦN TẠO] Deployment & Update Strategy

Phase 4 — Scale (Post v1)
├── 📄 [CẦN TẠO] Plugin Development Guide
├── 📄 [CẦN TẠO] Contribution Guidelines
└── 📄 [CẦN TẠO] Operational Runbook (troubleshooting, monitoring)
```

---

### Điểm Đánh Giá Tổng Hợp

| Tiêu chí | Điểm (1-10) | Nhận xét |
|---|---|---|
| **Chất lượng nội dung** | 9/10 | Xuất sắc — rationale rõ ràng, domain-aware, thực tế |
| **Độ bao phủ kiến trúc** | 5/10 | Chỉ cover properties, chưa cover structure & behavior |
| **Khả năng dùng để build** | 3/10 | Agent/dev sẽ phải "đoán" rất nhiều chi tiết quan trọng |
| **Khả năng dùng để review/audit** | 8/10 | Rất tốt cho việc review quyết định kiến trúc |
| **Khả năng dùng để onboard** | 7/10 | Tốt cho người mới hiểu *tại sao* hệ thống thiết kế như vậy |
| **Độ dễ bảo trì tài liệu** | 8/10 | Cấu trúc rõ ràng, dễ cập nhật |

> [!IMPORTANT]
> **Tóm lại:** Tài liệu này là một **nền tảng kiến trúc xuất sắc** — nhưng nó là *tầng 1 trong tòa nhà 4 tầng*. Để lập trình viên hoặc AI agent có thể build hệ thống một cách nhất quán và đúng đắn, cần bổ sung **ít nhất 3 tài liệu nữa**: Architecture Blueprint, Contract Specification, và Sequence Diagrams. Thiếu 3 tài liệu này, mọi người/agent sẽ tự diễn giải theo cách riêng → divergence (phân kỳ) từ sprint đầu tiên → nợ kỹ thuật ngay từ ngày 1.

---
---

# CÁC PHỤ LỤC BỔ SUNG (Theo Comment Của Bạn)

---

## Phụ Lục A — Deep-Dive: Process Isolation & IPC Mechanisms

> Trả lời câu hỏi: *"Với 2 đối tượng (1 GPU và multi-GPU LAN), nên bắt đầu từ v1 hay v2? Nếu v1 không dùng HTTP thì giao tiếp bằng gì? Vấn đề Python environment khác nhau giữa các plugin xử lý thế nào?"*

### Bối cảnh: 2 đối tượng người dùng

```
┌────────────────────────────────────┐     ┌────────────────────────────────────┐
│       ĐỐI TƯỢNG 1: Single GPU      │     │       ĐỐI TƯỢNG 2: Multi-GPU LAN   │
│                                    │     │                                    │
│  ┌──────────┐   ┌──────────────┐   │     │  ┌──────────┐   ┌──────────────┐   │
│  │ App UI   │   │ AI Services  │   │     │  │ App UI   │   │ AI Services  │   │
│  │ (Main)   │   │ (Subprocess) │   │     │  │ (Main)   │   │ (Local GPU)  │   │
│  └──────────┘   └──────────────┘   │     │  └──────────┘   └──────────────┘   │
│           1 máy duy nhất            │     │       Máy chính (Workstation)       │
└────────────────────────────────────┘     │                                    │
                                          │         ┌──── LAN ─────┐           │
                                          │         ▼              ▼           │
                                          │  ┌────────────┐ ┌────────────┐    │
                                          │  │ GPU Node 2 │ │ GPU Node 3 │    │
                                          │  │ (RTX 3090) │ │ (RTX 4080) │    │
                                          │  │ AI Service │ │ AI Service │    │
                                          │  └────────────┘ └────────────┘    │
                                          └────────────────────────────────────┘
```

### So sánh 3 cơ chế IPC chi tiết

#### Cơ chế 1: `multiprocessing.Queue / Pipe` (v1 ban đầu tôi đề xuất)

```python
# === CƠ CHẾ HOẠT ĐỘNG ===
from multiprocessing import Process, Queue
import pickle

def ai_worker(task_queue: Queue, result_queue: Queue):
    """Chạy trong subprocess — CÓ crash isolation."""
    while True:
        task = task_queue.get()            # Block chờ task
        try:
            result = run_inference(task)    # Chạy AI
            result_queue.put(result)        # Gửi kết quả về
        except Exception as e:
            result_queue.put(ErrorResult(e))

# Main process
task_q = Queue()
result_q = Queue()
worker = Process(target=ai_worker, args=(task_q, result_q))
worker.start()

task_q.put({"audio": "path/to/file.wav", "lang": "vi"})  # Gửi task
result = result_q.get()  # Block chờ kết quả
```

| Ưu điểm | Nhược điểm |
|---|---|
| ✅ Đơn giản, ít code | ❌ **CHỈ hoạt động trên 1 máy** — Queue dùng OS pipe/shared memory |
| ✅ Crash isolation (subprocess chết, main sống) | ❌ **Dùng CHUNG Python interpreter** — tức subprocess kế thừa Python env của parent process |
| ✅ Không cần network stack | ❌ Không thể gửi task sang máy khác trong LAN |
| ✅ Debug dễ hơn (cùng IDE) | ❌ Serialization bằng `pickle` — không type-safe, khó debug data corruption |
|  | ❌ Không có streaming progress (Queue chỉ gửi message hoàn chỉnh) |

> [!CAUTION]
> **Vấn đề Python Environment của v1:**
>
> `multiprocessing.Process` tạo subprocess bằng cách **fork/spawn từ process cha**. Subprocess sẽ dùng **cùng Python interpreter, cùng sys.path, cùng installed packages** với process cha.
>
> Điều này có nghĩa:
> - Nếu app chính dùng Python 3.11 + numpy 1.24, thì subprocess cũng dùng Python 3.11 + numpy 1.24
> - **KHÔNG THỂ** cho WhisperX subprocess dùng numpy 1.24 trong khi XTTS subprocess dùng numpy 1.26
> - **KHÔNG THỂ** cho mỗi plugin có venv riêng biệt
>
> **Workaround duy nhất:** Dùng `subprocess.Popen` thay vì `multiprocessing.Process`, trỏ đến Python binary trong venv riêng. Nhưng khi đó bạn mất API `Queue/Pipe` và phải tự thiết kế IPC → lúc này chi phí **không khác gì dùng HTTP**.

#### Cơ chế 2: `subprocess.Popen` + stdin/stdout Pipe

```python
# === CƠ CHẾ HOẠT ĐỘNG ===
import subprocess
import json

# Spawn subprocess với PYTHON RIÊNG (venv riêng!)
proc = subprocess.Popen(
    ["services/whisperx/venv/Scripts/python.exe", "services/whisperx/worker.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Gửi task qua stdin (JSON text)
task = json.dumps({"audio": "path/to/file.wav", "lang": "vi"})
proc.stdin.write(task.encode() + b"\n")
proc.stdin.flush()

# Đọc kết quả từ stdout
line = proc.stdout.readline()
result = json.loads(line)
```

| Ưu điểm | Nhược điểm |
|---|---|
| ✅ **Python env riêng biệt** — mỗi service trỏ đến venv riêng | ❌ **CHỈ hoạt động trên 1 máy** — stdin/stdout là OS pipe |
| ✅ Crash isolation hoàn toàn | ❌ Giao tiếp tuần tự (1 message tại 1 thời điểm) |
| ✅ Không cần network stack | ❌ Khó gửi streaming progress (stdout bị buffer) |
| ✅ JSON serialization = human-readable | ❌ Khó mở rộng: thêm endpoint mới = thêm if/else parsing |
|  | ❌ **Không thể gửi task sang máy khác** |

> [!NOTE]
> Cơ chế này giải quyết được vấn đề Python env nhưng **vẫn bị giới hạn ở 1 máy**. Nếu bạn cần multi-GPU LAN, sẽ phải viết lại lớp IPC → waste effort.

#### Cơ chế 3: HTTP/gRPC Server (v2 — **Khuyến nghị bắt đầu từ đây**)

```python
# === services/whisperx/server.py — Mỗi AI service là 1 FastAPI app ===
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()
model = None  # Lazy load

@app.post("/transcribe")
async def transcribe(request: TranscribeRequest):
    global model
    if model is None:
        model = load_whisperx_model()  # Load 1 lần, cache trong memory
    
    result = model.transcribe(request.audio_path, language=request.language)
    return TranscriptionResult.from_whisperx(result)  # Contract-first!

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None, "vram_used_mb": get_vram()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Bind 0.0.0.0 cho LAN access
```

```python
# === app/core/engine_client.py — App chính gọi AI service ===
import httpx

class EngineClient:
    """Client thống nhất — không quan tâm service ở local hay remote."""
    
    def __init__(self, base_url: str):
        # base_url = "http://127.0.0.1:8001" (local)
        #          = "http://192.168.1.50:8001" (remote GPU trên LAN)
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300)  # 5 phút timeout cho AI
    
    async def transcribe(self, audio_path: str, language: str) -> dict:
        response = await self.client.post(
            f"{self.base_url}/transcribe",
            json={"audio_path": audio_path, "language": language}
        )
        return response.json()
    
    async def health_check(self) -> bool:
        try:
            r = await self.client.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except:
            return False
```

| Ưu điểm | Nhược điểm |
|---|---|
| ✅ **Hoạt động đồng nhất** local + LAN + remote | ⚠️ Cần network stack (nhưng FastAPI+uvicorn rất nhẹ) |
| ✅ **Python env riêng hoàn toàn** — mỗi service có venv riêng | ⚠️ Latency thêm ~5-15ms (không đáng kể so với inference 30s+) |
| ✅ Swagger UI tự động → debug/test trực tiếp trên browser | ⚠️ Cần quản lý lifecycle (start/stop service) |
| ✅ Streaming progress qua SSE | ⚠️ Cần service discovery cho LAN mode |
| ✅ Type-safe contract (Pydantic) |  |
| ✅ Tương lai: đổi sang gRPC cho performance mà không đổi kiến trúc |  |

### Kết luận: Tại sao v2 (HTTP) là điểm bắt đầu đúng

```
    Đầu tư 1 lần vào HTTP/FastAPI
            │
            ├──► Single GPU user: service chạy localhost
            │    EngineClient("http://127.0.0.1:8001")
            │
            ├──► Multi-GPU LAN user: service chạy trên máy khác
            │    EngineClient("http://192.168.1.50:8001")
            │
            └──► Tương lai Cloud: service chạy trên cloud
                 EngineClient("https://gpu.myservice.com:8001")
    
    Trong cả 3 trường hợp, code app chính KHÔNG THAY ĐỔI GÌ.
    Chỉ đổi 1 dòng: base_url trong config.
```

> [!TIP]
> **Overhead của HTTP so với `multiprocessing.Queue`:**
> - HTTP localhost round-trip: ~5-15ms
> - AI inference cho 1 câu TTS: ~10,000-30,000ms
> - **Tỷ lệ overhead: 0.05% — hoàn toàn không đáng lo**
>
> Chi phí thực sự là **effort phát triển**: viết FastAPI server mất thêm ~1-2 ngày so với `multiprocessing`, nhưng tiết kiệm **hàng tuần** khi mở rộng sang LAN.

### Kiến trúc đề xuất cho LAN Multi-GPU

```
┌──────────────────────────────────────────────────────┐
│                    MÁY CHÍNH (Workstation)             │
│                                                       │
│  ┌─────────────┐    ┌──────────────────────────────┐  │
│  │  App UI     │    │  Service Registry (Config)    │  │
│  │  (PySide6)  │    │                              │  │
│  │             │    │  asr:                        │  │
│  │  ┌────────┐ │    │    url: http://127.0.0.1:8001│  │
│  │  │Orchest-│ │    │    type: local               │  │
│  │  │rator   │─┼───►│  tts:                        │  │
│  │  └────────┘ │    │    url: http://192.168.1.50:  │  │
│  │             │    │         8002                  │  │
│  └─────────────┘    │    type: remote_lan           │  │
│                     │  translation:                 │  │
│  ┌─────────────┐    │    url: https://api.deepl.com │  │
│  │ Local ASR   │    │    type: cloud_api            │  │
│  │ Service     │    └──────────────────────────────┘  │
│  │ :8001       │                                      │
│  │ (WhisperX)  │                                      │
│  │ [venv riêng]│                                      │
│  └─────────────┘                                      │
└──────────────────────────────────────────────────────┘
                            │ LAN (192.168.1.x)
                            │
          ┌─────────────────┼─────────────────┐
          ▼                                   ▼
┌──────────────────┐                ┌──────────────────┐
│  MÁY GPU #2       │                │  MÁY GPU #3       │
│  192.168.1.50      │                │  192.168.1.51      │
│                    │                │                    │
│  ┌──────────────┐  │                │  ┌──────────────┐  │
│  │ TTS Service  │  │                │  │ TTS Service  │  │
│  │ :8002        │  │                │  │ :8002        │  │
│  │ (XTTS v2)   │  │                │  │ (F5-TTS)     │  │
│  │ [venv riêng] │  │                │  │ [venv riêng] │  │
│  │ RTX 3090     │  │                │  │ RTX 4080     │  │
│  └──────────────┘  │                │  └──────────────┘  │
└──────────────────┘                └──────────────────┘
```

### Cách xử lý file audio/video qua LAN

> [!WARNING]
> **Vấn đề quan trọng:** Khi AI service chạy trên máy khác, nó không truy cập được file trên máy chính bằng path `C:\Users\...`. Cần 1 trong 2 giải pháp:

| Giải pháp | Cách hoạt động | Ưu/Nhược |
|---|---|---|
| **SMB Share (Windows File Sharing)** | Mount folder project qua `\\192.168.1.10\projects` | ✅ Đơn giản, Windows native. ⚠️ Chậm cho file lớn, phụ thuộc network |
| **Upload qua HTTP** | App gửi file audio kèm request `POST /transcribe` (multipart) | ✅ Không phụ thuộc SMB. ⚠️ Tốn bandwidth, cần upload/download |
| **NFS/Shared Storage** | Máy chính export folder, máy GPU mount NFS | ✅ Performance tốt. ⚠️ Cần setup Linux-style, phức tạp trên Windows |

**Đề xuất:** Dùng **SMB Share** cho v2 (Windows native, dễ setup) + fallback HTTP upload cho file nhỏ. Config trong Service Registry:

```json
{
  "tts": {
    "url": "http://192.168.1.50:8002",
    "type": "remote_lan",
    "shared_path": "\\\\192.168.1.10\\dubbing_projects",
    "file_transfer": "smb"
  }
}
```

---

## Phụ Lục B — LicenseBackend Dependency Inversion Example

> Trả lời câu hỏi: *"Cho ví dụ mẫu dùng ít nhất 2 implement LicenseBackend (Supabase + nền tảng tương tự) để giải quyết rủi ro vendor lock-in."*

### Thiết kế Interface (Contract)

```python
# shared/license/backends/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class LicenseTier(Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class LicenseInfo:
    """Contract chuẩn — BẤT KỲ backend nào cũng phải trả về đúng format này."""
    license_key: str
    tier: LicenseTier
    features_enabled: list[str]
    machine_id: str
    expires_at: datetime
    last_verified_at: datetime  # Lần cuối xác thực online thành công
    is_active: bool

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def days_since_last_check(self) -> int:
        return (datetime.utcnow() - self.last_verified_at).days


class LicenseBackend(ABC):
    """
    INTERFACE — Hợp đồng mà MỌI license backend phải tuân thủ.
    
    App chính CHỈ nói chuyện với interface này.
    Không bao giờ import supabase, keygen, hay bất kỳ SDK cụ thể nào.
    """

    @abstractmethod
    async def validate_license(self, license_key: str, machine_id: str) -> LicenseInfo:
        """Gọi server xác thực license. Raise LicenseError nếu invalid."""
        ...

    @abstractmethod
    async def activate_license(self, license_key: str, machine_id: str) -> LicenseInfo:
        """Kích hoạt license trên máy này. Raise nếu đã hết slot."""
        ...

    @abstractmethod
    async def deactivate_license(self, license_key: str, machine_id: str) -> bool:
        """Gỡ kích hoạt (khi user chuyển máy). Return True nếu thành công."""
        ...

    @abstractmethod
    async def check_feature(self, license_key: str, feature_name: str) -> bool:
        """Kiểm tra feature cụ thể có được bật không."""
        ...


class LicenseError(Exception):
    """Base exception cho mọi lỗi license."""
    pass

class LicenseInvalidError(LicenseError):
    pass

class LicenseExpiredError(LicenseError):
    pass

class LicenseQuotaExceededError(LicenseError):
    """Đã kích hoạt trên quá nhiều máy."""
    pass
```

### Implementation 1: Supabase Backend

```python
# shared/license/backends/supabase_backend.py

from supabase import create_client, Client
from .base import LicenseBackend, LicenseInfo, LicenseTier, LicenseError, LicenseInvalidError


class SupabaseLicenseBackend(LicenseBackend):
    """
    License backend dùng Supabase.
    
    Ưu điểm: Miễn phí, đa năng (auth + analytics + license), self-host được.
    Nhược điểm: Phụ thuộc Supabase service, Edge Functions dùng Deno.
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)

    async def validate_license(self, license_key: str, machine_id: str) -> LicenseInfo:
        try:
            # Gọi Edge Function trên Supabase
            result = self.client.functions.invoke(
                "validate-license",
                invoke_options={
                    "body": {
                        "license_key": license_key,
                        "machine_id": machine_id,
                    }
                }
            )
            data = result  # Supabase trả về dict
            
            if not data.get("valid"):
                raise LicenseInvalidError(data.get("reason", "License không hợp lệ"))
            
            # Biến đổi response Supabase → Contract chuẩn LicenseInfo
            return LicenseInfo(
                license_key=license_key,
                tier=LicenseTier(data["tier"]),
                features_enabled=data["features"],
                machine_id=machine_id,
                expires_at=datetime.fromisoformat(data["expires_at"]),
                last_verified_at=datetime.utcnow(),
                is_active=True,
            )
        except Exception as e:
            if isinstance(e, LicenseError):
                raise
            raise LicenseError(f"Không thể kết nối Supabase: {e}")

    async def activate_license(self, license_key: str, machine_id: str) -> LicenseInfo:
        result = self.client.functions.invoke(
            "activate-license",
            invoke_options={
                "body": {
                    "license_key": license_key,
                    "machine_id": machine_id,
                }
            }
        )
        data = result
        if data.get("error") == "quota_exceeded":
            raise LicenseQuotaExceededError(
                f"License đã kích hoạt trên {data['current_activations']}/{data['max_activations']} máy."
            )
        return LicenseInfo(
            license_key=license_key,
            tier=LicenseTier(data["tier"]),
            features_enabled=data["features"],
            machine_id=machine_id,
            expires_at=datetime.fromisoformat(data["expires_at"]),
            last_verified_at=datetime.utcnow(),
            is_active=True,
        )

    async def deactivate_license(self, license_key: str, machine_id: str) -> bool:
        result = self.client.functions.invoke(
            "deactivate-license",
            invoke_options={"body": {"license_key": license_key, "machine_id": machine_id}}
        )
        return result.get("success", False)

    async def check_feature(self, license_key: str, feature_name: str) -> bool:
        # Dùng direct database query thay vì Edge Function (nhanh hơn)
        result = self.client.table("licenses") \
            .select("features_enabled") \
            .eq("license_key", license_key) \
            .single() \
            .execute()
        features = result.data.get("features_enabled", [])
        return feature_name in features or "*" in features
```

### Implementation 2: Keygen.sh Backend

```python
# shared/license/backends/keygen_backend.py

import httpx
from .base import LicenseBackend, LicenseInfo, LicenseTier, LicenseError, LicenseInvalidError


class KeygenLicenseBackend(LicenseBackend):
    """
    License backend dùng Keygen.sh — nền tảng chuyên biệt cho license management.
    
    Ưu điểm: Chuyên nghiệp, offline validation bằng crypto signature,
             machine fingerprint tốt, chống crack mạnh.
    Nhược điểm: Free tier giới hạn 100 licenses, API format khác Supabase.
    """

    KEYGEN_API = "https://api.keygen.sh/v1/accounts"

    def __init__(self, account_id: str, product_token: str):
        self.account_id = account_id
        self.headers = {
            "Authorization": f"Bearer {product_token}",
            "Accept": "application/vnd.api+json",
        }

    async def validate_license(self, license_key: str, machine_id: str) -> LicenseInfo:
        async with httpx.AsyncClient() as client:
            # Keygen dùng JSON:API format — khác hoàn toàn Supabase
            response = await client.post(
                f"{self.KEYGEN_API}/{self.account_id}/licenses/actions/validate-key",
                headers=self.headers,
                json={
                    "meta": {
                        "key": license_key,
                        "scope": {"fingerprint": machine_id},
                    }
                },
            )
            data = response.json()

            # Keygen trả về validation code
            validation_code = data.get("meta", {}).get("code")
            if validation_code not in ("VALID", "TOO_MANY_MACHINES"):
                raise LicenseInvalidError(
                    f"License không hợp lệ: {data.get('meta', {}).get('detail', 'Unknown')}"
                )

            # Biến đổi Keygen response → Contract chuẩn LicenseInfo
            license_data = data.get("data", {}).get("attributes", {})
            metadata = license_data.get("metadata", {})

            return LicenseInfo(
                license_key=license_key,
                tier=LicenseTier(metadata.get("tier", "free")),
                features_enabled=metadata.get("features", []),
                machine_id=machine_id,
                expires_at=datetime.fromisoformat(license_data["expiry"]),
                last_verified_at=datetime.utcnow(),
                is_active=license_data.get("status") == "ACTIVE",
            )

    async def activate_license(self, license_key: str, machine_id: str) -> LicenseInfo:
        async with httpx.AsyncClient() as client:
            # Bước 1: Validate key để lấy license ID
            validate_resp = await client.post(
                f"{self.KEYGEN_API}/{self.account_id}/licenses/actions/validate-key",
                headers=self.headers,
                json={"meta": {"key": license_key}},
            )
            license_id = validate_resp.json()["data"]["id"]

            # Bước 2: Tạo machine activation
            activate_resp = await client.post(
                f"{self.KEYGEN_API}/{self.account_id}/machines",
                headers=self.headers,
                json={
                    "data": {
                        "type": "machines",
                        "attributes": {"fingerprint": machine_id},
                        "relationships": {
                            "license": {"data": {"type": "licenses", "id": license_id}}
                        },
                    }
                },
            )

            if activate_resp.status_code == 422:
                raise LicenseQuotaExceededError("Đã vượt quá số máy cho phép.")

            return await self.validate_license(license_key, machine_id)

    async def deactivate_license(self, license_key: str, machine_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            # Keygen: tìm machine theo fingerprint rồi DELETE
            machines_resp = await client.get(
                f"{self.KEYGEN_API}/{self.account_id}/machines",
                headers=self.headers,
                params={"fingerprint": machine_id},
            )
            machines = machines_resp.json().get("data", [])
            for machine in machines:
                await client.delete(
                    f"{self.KEYGEN_API}/{self.account_id}/machines/{machine['id']}",
                    headers=self.headers,
                )
            return len(machines) > 0

    async def check_feature(self, license_key: str, feature_name: str) -> bool:
        info = await self.validate_license(license_key, machine_id="")
        return feature_name in info.features_enabled or "*" in info.features_enabled
```

### LicenseManager — Lớp điều phối (không biết backend nào)

```python
# shared/license/license_manager.py

import json
from pathlib import Path
from .backends.base import LicenseBackend, LicenseInfo, LicenseError


class LicenseManager:
    """
    Quản lý license — KHÔNG BIẾT đang dùng Supabase hay Keygen hay backend nào.
    
    Chỉ nói chuyện với LicenseBackend interface.
    → Đổi backend = đổi 1 dòng config, không sửa code ở đây.
    """

    OFFLINE_GRACE_DAYS = 7

    def __init__(self, backend: LicenseBackend, cache_dir: Path):
        self.backend = backend                    # ← Interface, không phải class cụ thể!
        self.cache_file = cache_dir / "license_cache.json"

    async def validate(self, license_key: str, machine_id: str) -> LicenseInfo:
        """
        Logic thống nhất bất kể backend:
        1. Kiểm tra cache local (nhanh, offline)
        2. Nếu cache hết hạn → gọi backend online
        3. Nếu offline → grace period
        """
        # 1. Cache check
        cached = self._load_cache()
        if cached and not cached.is_expired() and cached.days_since_last_check < 1:
            return cached  # Cache còn tươi → dùng luôn, không gọi network

        # 2. Online validation
        try:
            info = await self.backend.validate_license(license_key, machine_id)
            self._save_cache(info)
            return info
        except ConnectionError:
            # 3. Offline grace period
            if cached and cached.days_since_last_check < self.OFFLINE_GRACE_DAYS:
                return cached  # Cho phép dùng offline tối đa 7 ngày
            raise LicenseError(
                "Cần kết nối internet để xác thực bản quyền. "
                f"Lần xác thực cuối: {cached.days_since_last_check} ngày trước."
                if cached else "Chưa từng xác thực bản quyền trên máy này."
            )

    def is_feature_enabled(self, cached_info: LicenseInfo, feature_name: str) -> bool:
        """Kiểm tra feature — dùng cache, không gọi network."""
        return feature_name in cached_info.features_enabled or "*" in cached_info.features_enabled

    def _load_cache(self) -> LicenseInfo | None:
        if not self.cache_file.exists():
            return None
        try:
            data = json.loads(self.cache_file.read_text())
            return LicenseInfo(**data)
        except (json.JSONDecodeError, KeyError):
            return None

    def _save_cache(self, info: LicenseInfo):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(info.__dict__, default=str))
```

### Factory — Tạo backend theo config

```python
# shared/license/factory.py

from .backends.base import LicenseBackend
from .backends.supabase_backend import SupabaseLicenseBackend
from .backends.keygen_backend import KeygenLicenseBackend
from .license_manager import LicenseManager


def create_license_manager(config: dict) -> LicenseManager:
    """
    Factory — tạo LicenseManager với backend phù hợp theo config.
    
    Config ví dụ:
    {
        "license_backend": "supabase",
        "supabase_url": "https://xxx.supabase.co",
        "supabase_key": "eyJ...",
    }
    hoặc:
    {
        "license_backend": "keygen",
        "keygen_account_id": "abc-123",
        "keygen_product_token": "prod-xxx",
    }
    """
    backend_type = config["license_backend"]

    if backend_type == "supabase":
        backend = SupabaseLicenseBackend(
            supabase_url=config["supabase_url"],
            supabase_key=config["supabase_key"],
        )
    elif backend_type == "keygen":
        backend = KeygenLicenseBackend(
            account_id=config["keygen_account_id"],
            product_token=config["keygen_product_token"],
        )
    else:
        raise ValueError(f"Unknown license backend: {backend_type}")

    return LicenseManager(
        backend=backend,
        cache_dir=Path(config.get("cache_dir", "~/.dubbing_app/license")),
    )
```

### Sơ đồ tổng quan

```
┌─────────────────────────────────────────────────────────┐
│                    APP CHÍNH                            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              LicenseManager                      │   │
│  │                                                  │   │
│  │  validate() → cache check → backend.validate()   │   │
│  │  is_feature_enabled() → check cached info        │   │
│  │                                                  │   │
│  │  ⚠️ KHÔNG biết backend cụ thể là gì!             │   │
│  │     Chỉ gọi interface LicenseBackend             │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │                                        │
│                 ▼                                        │
│  ┌──────────────────────────────┐                        │
│  │    LicenseBackend (ABC)     │ ← Interface / Contract  │
│  │                              │                        │
│  │  validate_license()          │                        │
│  │  activate_license()          │                        │
│  │  deactivate_license()        │                        │
│  │  check_feature()             │                        │
│  └──────────┬───────────────────┘                        │
│             │                                            │
│     ┌───────┴──────────┐                                 │
│     │                  │                                 │
│     ▼                  ▼                                 │
│  ┌────────────┐  ┌────────────┐  ┌─ ─ ─ ─ ─ ─ ─ ┐      │
│  │ Supabase   │  │ Keygen.sh  │  │ Tương lai:    │      │
│  │ Backend    │  │ Backend    │    LemonSqueezy         │
│  │            │  │            │  │ Paddle         │      │
│  │ supabase-py│  │ httpx      │    Self-hosted          │
│  └────────────┘  └────────────┘  └─ ─ ─ ─ ─ ─ ─ ┘      │
│       │                │                                 │
└───────┼────────────────┼─────────────────────────────────┘
        │                │
        ▼                ▼
   Supabase Cloud    Keygen.sh Cloud
```

> [!TIP]
> **Lợi ích thực tế:**
> - **Ngày 1:** Dùng Supabase (miễn phí, nhanh setup)
> - **6 tháng sau:** Supabase đổi pricing? → Viết `KeygenLicenseBackend`, đổi 1 dòng config → **0 thay đổi ở app chính**
> - **1 năm sau:** Muốn self-host? → Viết `SelfHostedLicenseBackend` (gọi API server riêng), đổi config → **vẫn 0 thay đổi ở app chính**
>
> Đây chính là sức mạnh của Dependency Inversion — tài liệu architecture_properties_v2.md nói rất đúng về nguyên tắc, nhưng cần áp dụng **nhất quán** cho mọi thành phần, kể cả License.
