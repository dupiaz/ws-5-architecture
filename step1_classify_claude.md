# Bước 1: Classify — Phân Loại Invariant / Variable

> Đi qua toàn bộ [architecture_properties_v2.md](file:///d:/antigravity/ws-5-architecture/docs/architecture_properties_v2.md), đánh dấu từng section.

**Quy ước tag:**
- **[I]** = Invariant — giữ lại cho `reference_architecture.md`
- **[V]** = Variable — chuyển sang `dubbing_product_config.md`
- **[I/V]** = Mixed — cần tách: phần nguyên tắc giữ lại, phần ví dụ cụ thể chuyển đi

---

## Phân Loại Chi Tiết

### Phần mở đầu (L1-53)

| # | Section | Lines | Tag | Lý do | Xử lý khi Split |
|---|---|---|---|---|---|
| 1 | **Tiêu đề + Mô tả mở đầu** | L1-3 | **[V]** | Gắn chặt "lồng tiếng video" + "Windows Desktop" | Viết lại tiêu đề generic cho reference. Giữ bản gốc cho dubbing config |
| 2 | **Bảng Thuật Ngữ** | L7-37 | **[I/V]** | Inference, DAG, GIL, IPC, Process, Thread... = invariant. Sox, FFmpeg, ASR, TTS = variable (domain dubbing/audio) | **Reference** giữ thuật ngữ generic (20/26 thuật ngữ). **Dubbing config** thêm bảng thuật ngữ domain: ASR, TTS, Demux, Mux, Sox, FFmpeg |
| 3 | **Bối cảnh đặc thù — Tại sao Desktop AI App khác biệt** | L41-53 | **[I/V]** | 6 hàng trong bảng. 5 hàng đầu mô tả thách thức bất biến (chạy trên 1 máy, AI nặng, model thay đổi, pipeline dài, user end-user). Riêng ví dụ cụ thể ("WhisperX 3-5GB", "biên tập viên video") = variable | **Reference** giữ 5 thách thức, thay ví dụ dubbing bằng ví dụ generic. **Dubbing config** giữ ví dụ cụ thể |
| 4 | **Quy trình Pipeline lồng tiếng — 6 bước** | L56-82 | **[V]** | 100% dubbing-specific: Demux→ASR→Translate→TTS→Mix→Mux | Chuyển hoàn toàn sang **dubbing config**. Reference chỉ nói "pipeline có N bước cấu hình được" |

---

### Phần A — Kiến Trúc Logic (L85-706)

| # | Section | Lines | Tag | Lý do | Xử lý khi Split |
|---|---|---|---|---|---|
| 5 | **A.1 Separation of Concerns — Định nghĩa + Tại sao quan trọng (tổng quát)** | L91-98 | **[I]** | Nguyên tắc thiết kế phần mềm phổ quát | Giữ nguyên |
| 6 | **A.1 — "Tại sao đặc biệt quan trọng cho dự án này" + Sơ đồ 5 miền** | L99-118 | **[I/V]** | Nguyên tắc "nhiều miền trách nhiệm khác biệt" = invariant. Nhưng 5 miền cụ thể (Qt/UI, Pipeline, Dubbing, Inference, File/DB) = variable — domain khác sẽ có miền khác | **Reference** giữ nguyên tắc + sơ đồ generic (thay "Dubbing" bằng "Domain Logic"). **Dubbing config** giữ 5 miền cụ thể |
| 7 | **A.1 — Vi phạm sẽ gây ra** | L119-123 | **[I]** | Đúng cho mọi hệ thống | Giữ nguyên |
| 8 | **A.2 Dependency Inversion — Định nghĩa + Tại sao quan trọng** | L126-145 | **[I/V]** | Nguyên tắc DI = invariant. Ví dụ WhisperX/FasterWhisper/ASREngine = variable (dubbing domain) | **Reference** giữ nguyên tắc + pattern, thay ASREngine bằng `StepEngine` generic. **Dubbing config** giữ bảng model + ví dụ ASR |
| 9 | **A.2 — Bảng công nghệ 4 module (ASR, Translation, TTS, Media)** | L151-199 | **[V]** | 100% dubbing-specific: danh sách WhisperX, DeepL, XTTS, FFmpeg... | Chuyển hoàn toàn sang **dubbing config**. Reference chỉ nói "mỗi step có N plugin alternatives" |
| 10 | **A.2 — Callout IMPORTANT + Code ví dụ ASREngine** | L200-231 | **[I/V]** | Callout "mỗi module có 4-7+ lựa chọn" = invariant pattern. Code `ASREngine` = variable (tên class, method). Nhưng PATTERN (ABC → implement) = invariant | **Reference** giữ pattern (ABC → Adapter). **Dubbing config** giữ ASREngine code cụ thể |
| 11 | **A.3 Event-Driven Reactivity — Định nghĩa + Tại sao sống còn** | L235-260 | **[I/V]** | Nguyên tắc event-driven + giải thích GIL = invariant. Bảng thời gian (WhisperX 15-45s, TTS 5-15 phút) = variable | **Reference** giữ nguyên tắc, thay bảng dubbing bằng bảng generic ("model load: 10-60s, inference: 10s-30min"). **Dubbing config** giữ bảng cụ thể |
| 12 | **A.3 — Sơ đồ UI↔Worker + PySide6 Signals/Slots** | L261-284 | **[I]** | Sơ đồ dispatch/event pattern = invariant. PySide6 Signal/Slot mechanism = invariant (technology choice cho archetype) | Giữ nguyên — PySide6 là phần technology stack invariant cho Desktop Python App archetype |
| 13 | **A.3 — Code ví dụ ASRWorker + SubtitleView** | L285-377 | **[I/V]** | PATTERN (Worker + moveToThread + Signal connect) = invariant. Tên class ASRWorker, SubtitleView, nội dung "nhận dạng giọng nói" = variable | **Reference** giữ pattern, đổi tên thành `PipelineStepWorker` + `GenericStepView`. **Dubbing config** giữ ASRWorker code |
| 14 | **A.4 Centralized State Management** | L386-505 | **[I/V]** | Nguyên tắc + mô hình GlobalStore + sơ đồ = invariant. Ví dụ `voice_list_changed`, `AutoDubbingView`, `Voice Studio` = variable | **Reference** giữ nguyên tắc + pattern (GlobalStore + subscribe), đổi signal names thành generic. **Dubbing config** giữ dubbing-specific state fields |
| 15 | **A.5 Pipeline Composability — DAG concept** | L509-570 | **[I/V]** | DAG definition, giải thích, bảng "DAG dùng ở đâu ngoài dự án" = invariant. Sơ đồ DAG dubbing (Demux→ASR→...) = variable | **Reference** giữ DAG concept + bảng cross-domain. **Dubbing config** giữ sơ đồ DAG dubbing |
| 16 | **A.5 — Use case table + Code Pipeline config** | L572-613 | **[I/V]** | Pattern `Pipeline([Step(...)])` = invariant. 5 use cases dubbing (tạo phụ đề, dịch phụ đề...) = variable | **Reference** giữ pattern `Pipeline + Step` generic. **Dubbing config** giữ 5 use cases |
| 17 | **A.6 Fault Isolation & Recovery** | L617-654 | **[I/V]** | Nguyên tắc checkpoint/resume + cơ chế = invariant. Kịch bản dubbing (Demux 2p, ASR 15p, TTS câu 181) = variable | **Reference** giữ nguyên tắc + checkpoint mechanism. **Dubbing config** giữ kịch bản cụ thể |
| 18 | **A.7 Contract-First Design** | L657-706 | **[I/V]** | Nguyên tắc "thiết kế quanh hợp đồng, không quanh công nghệ" = invariant. `TranscriptionResult`, `Segment` dataclass = variable (dubbing domain contracts) | **Reference** giữ nguyên tắc + pattern (dataclass contract). **Dubbing config** giữ TranscriptionResult cụ thể |

---

### Phần B — Triển Khai Vật Lý (L709-998)

| # | Section | Lines | Tag | Lý do | Xử lý khi Split |
|---|---|---|---|---|---|
| 19 | **B.1 UI Thread Sanctity — Process Model** | L715-800 | **[I]** | Nguyên tắc bảo vệ UI Thread + sơ đồ Process Model (Main → Worker → AI Subprocess) + giải thích GIL = hoàn toàn invariant. Ví dụ WhisperX/XTTS trong sơ đồ có thể generalize thành "AI Service #1/#2" | Giữ gần nguyên, chỉ đổi label "WhisperX" → "AI Model A", "XTTS" → "AI Model B" |
| 20 | **B.2 Process Isolation** | L803-849 | **[I/V]** | Nguyên tắc isolation + bảng vấn đề/giải pháp = invariant. So sánh FastAPI vs Flask = invariant (technology recommendation cho archetype). Ví dụ "WhisperX cần numpy 1.24, XTTS cần numpy 1.26" = variable | **Reference** giữ nguyên tắc + FastAPI recommendation. Đổi ví dụ dependency conflict thành generic |
| 21 | **B.3 Resource-Aware Scheduling** | L852-878 | **[I/V]** | Nguyên tắc VRAM/RAM check + scheduling = invariant. Bảng VRAM (WhisperX 3.5GB, XTTS 2.5GB) = variable | **Reference** giữ mechanism. **Dubbing config** giữ VRAM table |
| 22 | **B.4 Environment Isolation — chiến lược venv** | L882-923 | **[I]** | Chiến lược "isolated venv per service" + folder structure + lý do không dùng Docker = hoàn toàn invariant (đúng cho mọi Desktop AI app) | Giữ gần nguyên, đổi tên folder "whisperx/xtts" thành "service_a/service_b" |
| 23 | **B.5 Data Locality & Checkpoint** | L927-968 | **[I/V]** | Nguyên tắc "mọi intermediate data lưu disk" = invariant. Cấu trúc folder project cụ thể (step_01_demux, step_02_asr...) = variable | **Reference** giữ nguyên tắc + cấu trúc folder generic (step_01, step_02...). **Dubbing config** giữ cấu trúc cụ thể |
| 24 | **B.6 Packaging & Distribution** | L971-998 | **[I/V]** | Chiến lược "core nhẹ + plugin nặng tải sau" = invariant. Bảng kích thước (PyTorch 2-3GB, WhisperX 3GB) = variable | **Reference** giữ chiến lược. **Dubbing config** giữ bảng kích thước cụ thể |

---

### Phần C — License (L1001-1191)

| # | Section | Lines | Tag | Lý do | Xử lý khi Split |
|---|---|---|---|---|---|
| 25 | **C. Hệ thống kiểm tra bản quyền** | L1001-1191 | **[I/V]** | Cơ chế license (validate → cache → offline grace) = invariant pattern. So sánh Supabase/Keygen.sh + code LicenseManager = invariant (reusable cho mọi app). Bảng TIER_FEATURES (free/pro/enterprise features cụ thể) = variable | **Reference** giữ cơ chế license + LicenseManager pattern. **Dubbing config** giữ tier features cụ thể |

---

### Phần D — Ma Trận Ưu Tiên (L1194-1219)

| # | Section | Lines | Tag | Lý do | Xử lý khi Split |
|---|---|---|---|---|---|
| 26 | **D. Ma trận ưu tiên tổng hợp** | L1194-1219 | **[I]** | Thứ tự ưu tiên 14 tính chất = đúng cho mọi hệ thống cùng archetype. Giải thích dễ hiểu + mức ưu tiên = invariant | Giữ nguyên, chỉ đổi "giải nghĩa dễ hiểu" từ dubbing-specific sang generic khi cần |

---

## Thống Kê Tổng Hợp

```
Tổng: 26 sections phân loại

  [I]  thuần Invariant:    9 sections (~65% nội dung)
       #5, #7, #12, #19, #22, #26
       + phần nguyên tắc/pattern trong các section [I/V]
       
  [V]  thuần Variable:     4 sections (~15% nội dung)
       #1 (tiêu đề), #4 (pipeline 6 bước), #9 (bảng model 4 module)
       + phần ví dụ cụ thể trong các section [I/V]
       
  [I/V] Mixed (cần tách):  13 sections (~20% nội dung)
       #2, #3, #6, #8, #10, #11, #13, #14, #15, #16, #17, #18, 
       #20, #21, #23, #24, #25
```

> [!IMPORTANT]
> **Nhận xét:** Phần lớn nội dung v2.md thực chất là **invariant** (~65-80% khi tính cả phần invariant trong các section mixed). Tác giả đã viết rất tốt các nguyên tắc tổng quát — phần variable chủ yếu là **ví dụ minh họa** bằng dubbing domain. Điều này có nghĩa:
> - `reference_architecture.md` sẽ giữ **phần lớn** cấu trúc và nội dung v2.md
> - `dubbing_product_config.md` chủ yếu là **bảng model, pipeline steps, contracts cụ thể, và ví dụ domain**
> - Effort split sẽ nhẹ hơn dự kiến — chủ yếu là thay thế ví dụ, không phải viết lại

## Câu Hỏi Cho Bạn Review

1. **PySide6 nên là Invariant hay Variable?** Tôi phân loại PySide6/Qt Signals-Slots là **invariant** (phần core của archetype "Python Desktop App"). Nếu bạn muốn reference architecture cũng cover PyQt6 hoặc thậm chí Electron/Tauri, thì PySide6 nên là variable. Bạn muốn hướng nào?

2. **FastAPI cho IPC nên là Invariant hay Variable?** Tôi phân loại FastAPI recommendation là **invariant** (nằm trong Pattern Catalog). Nhưng nếu bạn muốn reference cũng cover gRPC hay ZeroMQ, thì FastAPI nên là "recommended option" trong variable. Bạn muốn hướng nào?

3. **Phần License (C):** Có muốn giữ nguyên cả phần so sánh Supabase/Keygen.sh trong reference (như pattern catalog)? Hay chỉ giữ cơ chế abstract (LicenseBackend interface) và chuyển toàn bộ so sánh vendor sang dubbing config?
