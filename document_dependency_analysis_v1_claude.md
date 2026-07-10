# Phân Tích Chuỗi Phụ Thuộc Tài Liệu — Từ Seed Đến System

> **Câu hỏi cốt lõi:** Đâu là tập tài liệu tối thiểu mà CON NGƯỜI phải viết, để từ đó AGENT có thể sinh ra toàn bộ tài liệu kiến trúc + kỹ thuật giúp lập trình viên/agent build được hệ thống?

---

## Phần 1: Dependency Graph — Tài Liệu Nào Cần Tài Liệu Nào?

### Ý 1: Agent viết 9 GAP documents cần gì?

Không phải 9 tài liệu GAP đều ngang hàng nhau. Chúng có **chuỗi phụ thuộc** — tài liệu này là input của tài liệu kia:

```
                    ┌─────────────────────────────────────────┐
                    │     TÀI LIỆU ĐÃ CÓ (hiện tại)        │
                    │                                         │
                    │  architecture_properties_v2.md          │
                    │  (Tính chất kiến trúc + Rationale)      │
                    └──────────────┬──────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
 ┌───────────────┐    ┌────────────────────┐    ┌────────────────────┐
 │ GAP 1         │    │ GAP 2              │    │ GAP 4              │
 │ Architecture  │    │ Contract           │    │ Error Handling     │
 │ Blueprint     │    │ Specification      │    │ Strategy           │
 │ (C4 Diagrams) │    │ (All Interfaces)   │    │ (Error Taxonomy)   │
 └──────┬────────┘    └────────┬───────────┘    └────────┬───────────┘
        │                      │                         │
        ├──────────┬───────────┤                         │
        │          │           │                         │
        ▼          ▼           ▼                         │
 ┌────────────┐ ┌────────────────┐ ┌──────────────────┐  │
 │ GAP 3      │ │ GAP 5          │ │ GAP 6            │  │
 │ Sequence   │ │ Pipeline State │ │ Configuration    │◄─┘
 │ Diagrams   │ │ Machine        │ │ Architecture     │
 └─────┬──────┘ └───────┬────────┘ └────────┬─────────┘
       │                │                    │
       ├────────────────┼────────────────────┤
       │                │                    │
       ▼                ▼                    ▼
 ┌────────────────────────────────────────────────┐
 │ GAP 7: Testing Strategy                        │
 │ GAP 8: Deployment & Update Strategy            │
 │ GAP 9: Developer Experience Guidelines         │
 └────────────────────────────────────────────────┘
```

### Bảng phụ thuộc chi tiết

| GAP | Tài liệu | Cần input từ | Agent có thể tự viết? |
|---|---|---|---|
| **1** | Architecture Blueprint | `architecture_properties_v2.md` + **Seed A, B, C** | ⚠️ 70% — agent cần con người xác nhận ranh giới giữa các component |
| **2** | Contract Specification | `architecture_properties_v2.md` + GAP 1 + **Seed C** | ⚠️ 80% — agent cần con người review domain-specific data fields |
| **3** | Sequence Diagrams | GAP 1 + GAP 2 | ✅ 95% — agent có thể derive flows từ components + contracts |
| **4** | Error Handling Strategy | `architecture_properties_v2.md` + **Seed C, D** | ⚠️ 75% — agent cần con người cho UX requirements cho error messages |
| **5** | Pipeline State Machine | GAP 1 + GAP 2 + **Seed C** | ✅ 90% — phần lớn derivable từ pipeline definition |
| **6** | Configuration Architecture | GAP 1 + GAP 4 + **Seed B, D, E** | ⚠️ 70% — cần biết rõ deployment context, security requirements |
| **7** | Testing Strategy | GAP 1-6 (tất cả phía trên) | ✅ 90% — agent derive test cases từ contracts + flows |
| **8** | Deployment & Update | GAP 1 + GAP 6 + **Seed B, D, E** | ⚠️ 60% — cần nhiều quyết định business (update frequency, support policy) |
| **9** | DX Guidelines | GAP 1-8 (tất cả) + **Seed E** | ✅ 85% — agent tổng hợp conventions từ codebase + decisions |

> [!IMPORTANT]
> **Nhận xét quan trọng:** Không có GAP nào agent viết được 100% mà không cần input từ con người. Nhưng có 1 pattern rõ ràng: các tài liệu ở **tầng trên** (GAP 1, 2, 4, 6, 8) cần nhiều **human decisions** hơn. Các tài liệu ở **tầng dưới** (GAP 3, 5, 7, 9) phần lớn **derivable** từ tầng trên.

### Thứ tự triển khai (Waves)

```
Wave 1 (song song, cần Human review nhiều nhất):
  ├── GAP 1: Architecture Blueprint
  ├── GAP 2: Contract Specification  
  └── GAP 4: Error Handling Strategy

Wave 2 (song song, derive từ Wave 1):
  ├── GAP 3: Sequence Diagrams
  ├── GAP 5: Pipeline State Machine
  └── GAP 6: Configuration Architecture

Wave 3 (tổng hợp từ Wave 1+2):
  ├── GAP 7: Testing Strategy
  └── GAP 8: Deployment Strategy

Wave 4 (cuối cùng):
  └── GAP 9: DX Guidelines
```

---

## Phần 2: Seed Documents — Tài Liệu Gốc Chỉ Con Người Mới Viết Được

### Ý 2: Nếu chưa có gì, cần gì để agent viết TẤT CẢ?

Đây là câu hỏi mấu chốt. Câu trả lời: **Có 5 loại kiến thức mà KHÔNG agent nào tự nghĩ ra được** — vì chúng là **quyết định** của con người, không phải **suy luận** từ dữ liệu:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   5 SEED DOCUMENTS (Chỉ con người viết được)                   │
│   ═══════════════════════════════════════════                   │
│                                                                 │
│   A. Product Requirements Document (PRD)                        │
│      "Sản phẩm này LÀM GÌ, cho AI, và TẠI SAO?"              │
│                                                                 │
│   B. Technical Decisions Record                                 │
│      "TẠI SAO chọn Python, PySide6, Desktop?"                  │
│                                                                 │
│   C. Domain Knowledge Base                                      │
│      "Quy trình dubbing THỰC TẾ hoạt động thế nào?"            │
│                                                                 │
│   D. Non-Functional Requirements (NFR)                          │
│      "Nhanh bao nhiêu là ĐỦ? Ổn định bao nhiêu là ĐỦ?"       │
│                                                                 │
│   E. Business & Operational Constraints                         │
│      "Ai code? Bao nhiêu tiền? Bao lâu? Bán cho ai?"          │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Agent đọc 5 seed documents
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   AGENT SINH RA (có thể tự viết 70-95%):                       │
│                                                                 │
│   ├── architecture_properties.md  (tính chất kiến trúc)        │
│   ├── architecture_blueprint.md   (C4 diagrams, components)    │
│   ├── contract_specification.md   (all interfaces)             │
│   ├── sequence_diagrams.md        (interaction flows)          │
│   ├── error_handling_strategy.md  (error taxonomy)             │
│   ├── pipeline_state_machine.md   (state diagrams)             │
│   ├── configuration_architecture.md                            │
│   ├── testing_strategy.md                                      │
│   ├── deployment_strategy.md                                   │
│   └── dx_guidelines.md                                         │
│                                                                 │
│   → Tổng ~100-150 trang tài liệu kỹ thuật                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Seed A: Product Requirements Document (PRD)

**Tại sao agent không tự viết được:** Agent không biết bạn muốn bán sản phẩm gì, cho ai, giải quyết vấn đề gì. Đây là **tầm nhìn sản phẩm** — chỉ founder/product owner mới có.

**Nội dung cần cung cấp:**

```markdown
# 1. Tổng quan sản phẩm
- Tên sản phẩm: ___
- Mô tả 1 câu: "Ứng dụng desktop giúp [ai] làm [gì] bằng cách [thế nào]"
- Vấn đề giải quyết: Lồng tiếng video hiện tại tốn [bao lâu/bao nhiêu tiền]?
  Sản phẩm giảm xuống còn [bao lâu/bao nhiêu]?

# 2. Đối tượng người dùng (User Personas)
- Persona 1: [Tên], [Nghề], [Mục tiêu], [Kỹ năng kỹ thuật]
  Ví dụ: "Minh, YouTuber, muốn dịch video sang tiếng Anh, 
          không biết code, có PC gaming RTX 3060"
- Persona 2: [Tên], [Nghề], [Mục tiêu], [Kỹ năng kỹ thuật]
  Ví dụ: "Studio ABC, công ty dịch thuật, cần xử lý hàng loạt, 
          có 3 máy GPU trong LAN, có IT admin"

# 3. Feature List (Danh sách tính năng) — chia theo MoSCoW
## Must Have (Bắt buộc cho v1):
- [ ] Tính năng 1: Mô tả cụ thể, user story
- [ ] Tính năng 2: ...

## Should Have (Rất nên có trong v1):
- [ ] ...

## Could Have (Có thể có trong v1, hoặc v2):
- [ ] ...

## Won't Have (Không làm trong v1):
- [ ] ...

# 4. User Flows chính (mô tả bằng lời)
- Flow 1: "User mở app → import video → chọn ngôn ngữ nguồn/đích 
   → chọn giọng đọc → bấm 'Bắt đầu' → xem tiến độ → xem kết quả 
   → chỉnh sửa phụ đề nếu cần → export video"
- Flow 2: ...

# 5. Phân biệt với đối thủ
- Đối thủ 1: [Tên] — thiếu [gì] mà sản phẩm này có
- Đối thủ 2: ...
- USP (Unique Selling Point): ___
```

> [!IMPORTANT]
> **Đây là tài liệu quan trọng nhất.** Không có PRD → agent không biết viết feature nào trước, feature nào sau, feature nào bỏ. Mọi quyết định kiến trúc đều bắt nguồn từ yêu cầu sản phẩm.

---

### Seed B: Technical Decisions Record

**Tại sao agent không tự viết được:** Agent có thể *gợi ý* công nghệ, nhưng **quyết định cuối cùng** phải là của con người — vì nó phụ thuộc vào kỹ năng team, budget, thời gian, và cả sở thích cá nhân.

**Nội dung cần cung cấp:**

```markdown
# 1. Quyết định đã chốt (Non-negotiable)
- Ngôn ngữ chính: Python (lý do: ___)
- UI Framework: PySide6 (lý do: ___)
- Deployment target: Windows Desktop (lý do: ___) 
  Có cần macOS/Linux không? ___
- AI Inference: Local + Cloud hybrid (lý do: ___)

# 2. Quyết định cần cân nhắc thêm
- IPC mechanism: HTTP (FastAPI) vs gRPC vs khác?
  Ưu tiên của bạn: [đơn giản / hiệu năng / mở rộng LAN]?
- Database: SQLite vs khác? Cần lưu gì ngoài project metadata?
- State Management: Custom GlobalStore vs thư viện có sẵn?
- Package Manager: pip vs uv vs poetry vs conda?

# 3. Hardware targets (rất quan trọng cho architecture)
- GPU tối thiểu: ___ (ví dụ: GTX 1060 6GB / RTX 3060 12GB / không cần GPU)
- RAM tối thiểu: ___ GB
- Disk space: ___ GB (cho app + models)
- Cần hỗ trợ CPU-only mode không? ___
- CUDA versions cần hỗ trợ: ___

# 4. Quyết định về Multi-GPU / LAN
- Đối tượng 1 GPU: cụ thể hoạt động thế nào?
- Đối tượng multi-GPU LAN: 
  - Ai setup các máy GPU? (user tự setup / IT admin / auto-discovery?)
  - Các máy GPU chạy OS gì? (Windows / Linux / cả hai?)
  - Network: Tốc độ LAN tối thiểu? (100Mbps / 1Gbps / 10Gbps?)
  - File sharing: SMB / NFS / HTTP upload / khác?

# 5. Thư viện/Framework đã thử và có ý kiến
- Đã thử WhisperX? Ấn tượng/vấn đề gặp: ___
- Đã thử Coqui XTTS? Ấn tượng/vấn đề gặp: ___
- Đã thử FFmpeg? ___
- Thư viện nào KHÔNG muốn dùng và lý do: ___
```

---

### Seed C: Domain Knowledge Base

**Tại sao agent không tự viết được:** Agent biết *lý thuyết* về dubbing, nhưng không biết **thực tế vận hành** — ví dụ: chất lượng voice cloning ở mức nào là "chấp nhận được"? User có cần chỉnh sửa transcript trước khi dịch không? Đây là kiến thức từ **kinh nghiệm thực tế** trong domain.

**Nội dung cần cung cấp:**

```markdown
# 1. Quy trình dubbing thực tế (chi tiết hơn pipeline 6 bước)

## Bước Demux:
- Input formats cần hỗ trợ: [mp4, mkv, avi, mov, ...]
- Output: chỉ tách vocal + background? hay cần tách thêm gì?
- Vocal separation quality: Demucs bắt buộc hay FFmpeg đủ?
- Video lớn nhất cần hỗ trợ: ___ GB / ___ giờ
- Có cần hỗ trợ video có nhiều audio track không? (ví dụ: 
  track tiếng Anh + track tiếng Nhật)

## Bước ASR:
- Ngôn ngữ nguồn cần hỗ trợ: [liệt kê cụ thể]
- Cần word-level timestamp không? Hay sentence-level đủ?
- Cần speaker diarization (phân biệt người nói) không?
- User có cần chỉnh sửa transcript TRƯỚC KHI dịch không?
  (Nếu có → cần editor UI cho transcript)
- Chất lượng ASR nào là "chấp nhận được"? 
  (WER < ___% ? Hay user chỉnh tay là ok?)

## Bước Translation:
- Ngôn ngữ đích cần hỗ trợ: [liệt kê cụ thể]
- Cần giữ nguyên thuật ngữ chuyên ngành không? (glossary feature?)
- User có cần review bản dịch TRƯỚC KHI TTS không?
- Có cần dịch theo context (xem câu trước câu sau) không?

## Bước TTS:
- Voice cloning là BẮT BUỘC hay NICE-TO-HAVE?
- Chất lượng voice clone nào chấp nhận được?
  ("Nghe giống 70% là OK" hay "phải gần giống 95%"?)
- Cần bao nhiêu giọng mẫu để clone? (5 giây / 30 giây / 5 phút?)
- Có cần điều chỉnh tốc độ đọc cho khớp lip-sync không?
- Cần hỗ trợ emotion/intonation không? (vui, buồn, giận...)

## Bước Mix:
- Cần giữ nhạc nền ở mức âm lượng nào? (user điều chỉnh / tự động?)
- Cần time-stretching (giãn/nén) giọng đọc cho khớp timestamp?
- Chất lượng audio output: bitrate, sample rate?

## Bước Mux:
- Output formats: [mp4, mkv, ...]
- Cần giữ subtitle track không?
- Cần giữ original audio track (song song với dubbed track)?
- Video quality: giữ nguyên gốc hay re-encode?

# 2. Edge cases và tình huống đặc biệt
- Video không có giọng nói (chỉ nhạc) → xử lý thế nào?
- Video có nhiều người nói → mỗi người 1 giọng clone hay chung 1 giọng?
- Giọng nói bị chồng nhạc nền lớn → ASR kém → xử lý thế nào?
- Câu nói rất dài (>30 giây) → TTS xử lý thế nào?
- Ngôn ngữ không phổ biến (ví dụ: tiếng Lào) → fallback thế nào?

# 3. Quy trình user thực tế
- User thường xử lý bao nhiêu video/ngày? ___ video
- Độ dài video trung bình? ___ phút
- User có làm việc với project nhiều ngày (mở lại project cũ)?
- User có cần xuất phụ đề SRT/ASS riêng không?
- User có cần batch processing (xử lý hàng loạt) không?
```

> [!NOTE]
> **Tài liệu này quyết định 50% kiến trúc.** Ví dụ: nếu user CẦN chỉnh transcript trước khi dịch → cần thêm "human-in-the-loop" step trong pipeline → thay đổi hoàn toàn Pipeline State Machine. Nếu không biết điều này, agent sẽ thiết kế pipeline chạy tự động đầu-cuối → sai yêu cầu.

---

### Seed D: Non-Functional Requirements (NFR)

**Tại sao agent không tự viết được:** Agent có thể *đề xuất* targets, nhưng chỉ con người mới biết **"đủ tốt" là bao nhiêu** cho sản phẩm cụ thể này với đối tượng cụ thể này.

**Nội dung cần cung cấp:**

```markdown
# 1. Performance Targets (Mục tiêu hiệu năng)
- App startup time (không tính load model): < ___ giây
- UI response time (click → phản hồi): < ___ ms
- Video 10 phút: toàn bộ pipeline hoàn thành trong < ___ phút
  trên GPU ___ (benchmark reference)
- TTS cho 1 câu (15 từ): < ___ giây trên GPU ___

# 2. Reliability Targets (Mục tiêu độ tin cậy)
- Pipeline thất bại giữa chừng: mất tối đa ___ phút công việc
- App crash: trung bình < ___ lần / tuần sử dụng
- Sau crash: khôi phục project state trong < ___ giây

# 3. Usability Requirements (Yêu cầu dễ dùng)
- Người dùng mới (chưa biết app): hoàn thành dubbing video đầu tiên 
  trong < ___ phút (không tính thời gian AI xử lý)
- Cần tutorial/onboarding trong app không?
- Ngôn ngữ giao diện: [Tiếng Việt / Tiếng Anh / cả hai / đa ngôn ngữ]
- Accessibility: cần hỗ trợ người khuyết tật không? (mức nào?)

# 4. Security Requirements (Yêu cầu bảo mật)
- API keys: mức bảo vệ nào? 
  [encrypted file / OS credential store / basic obfuscation]
- User data privacy: audio/video KHÔNG ĐƯỢC gửi đi đâu khi dùng 
  local model? ___
- License: mức chống crack nào? 
  [basic / medium / advanced anti-tamper]
- Có cần audit log (ghi lại ai làm gì, khi nào) không?

# 5. Scalability (Khả năng mở rộng)
- v1 cần hỗ trợ bao nhiêu project đồng thời? ___
- Tương lai cần hỗ trợ bao nhiêu GPU nodes trong LAN? ___
- Cần scale lên cloud (SaaS) trong tương lai không?
- Cần hỗ trợ concurrent users (nhiều user trên 1 máy) không?

# 6. Compatibility (Tương thích)
- Windows versions: [10 / 11 / cả hai]
- Python version target: [3.10 / 3.11 / 3.12]
- GPU: [chỉ NVIDIA / AMD ROCm / Intel Arc / CPU fallback?]
- Disk: [SSD bắt buộc? / HDD chấp nhận được?]
```

---

### Seed E: Business & Operational Constraints

**Tại sao agent không tự viết được:** Kiến trúc phải phục vụ thực tế kinh doanh. Agent không biết team có mấy người, budget bao nhiêu, deadline khi nào.

**Nội dung cần cung cấp:**

```markdown
# 1. Team
- Số lượng developer: ___ người
- Skill set hiện tại: [Python level / Qt experience / AI experience]
- Ai review code? Có senior developer không?
- Có dùng AI agent (Cursor, Copilot, Antigravity...) để code không?
  → Nếu có: agent cần tài liệu gì để code đúng?

# 2. Timeline
- v1 (MVP) target release: ___ (tháng/năm)
- v2 (multi-GPU LAN) target: ___
- Có deadline cứng (ví dụ: demo cho investor) không?

# 3. Budget
- Cloud API costs budget/tháng: $___ (cho development + testing)
- Infrastructure costs: $___ /tháng (Supabase, hosting, CI/CD)
- Có budget mua license cho tools/services không?

# 4. Monetization (Kiếm tiền)
- Mô hình: [Freemium / One-time purchase / Subscription / Enterprise license]
- Giá dự kiến: Free: ___ / Pro: $___/tháng / Enterprise: $___
- Free tier giới hạn gì? [thời lượng video / số lượng / features]
- Kênh phân phối: [website trực tiếp / app store / cả hai]

# 5. Operational
- Ai hỗ trợ user khi gặp lỗi? [founder / support team / community]
- Cần telemetry (thu thập dữ liệu sử dụng ẩn danh) không?
- Cần crash reporting tự động không?
- Update frequency dự kiến: [hàng tuần / hàng tháng / theo nhu cầu]
- Có CI/CD pipeline không? Dùng platform nào? [GitHub Actions / GitLab CI / ...]

# 6. Legal
- License cho phần mềm: [proprietary / open-source / dual license]
- Các AI model sử dụng có license nào cần tuân thủ?
  (ví dụ: Coqui XTTS dùng MPL 2.0 — cần attribution)
- Có cần terms of service / privacy policy không?
```

---

## Tổng Kết: Chuỗi Phụ Thuộc Hoàn Chỉnh

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   TẦNG 0 — SEED (Con người viết, ~20-30 trang)                     ║
║   ════════════════════════════════════════════                       ║
║                                                                      ║
║   A. PRD (Product Requirements)           ← "Làm gì, cho ai?"      ║
║   B. Technical Decisions                  ← "Dùng gì, tại sao?"    ║
║   C. Domain Knowledge                    ← "Domain hoạt động sao?" ║
║   D. Non-Functional Requirements         ← "Tốt bao nhiêu là đủ?" ║
║   E. Business Constraints                ← "Ai, tiền, thời gian?"  ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                          │                                           ║
║                          │ Agent đọc                                 ║
║                          ▼                                           ║
║                                                                      ║
║   TẦNG 1 — KIẾN TRÚC (Agent viết, Human review)                    ║
║   ══════════════════════════════════════════════                     ║
║                                                                      ║
║   ├── Architecture Properties  ← ĐÃ CÓ (v2.md)                    ║
║   ├── Architecture Blueprint   ← Agent viết, Human review ranh giới ║
║   ├── Contract Specification   ← Agent viết, Human review fields    ║
║   └── Error Handling Strategy  ← Agent viết, Human review UX        ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                          │                                           ║
║                          │ Agent derive                              ║
║                          ▼                                           ║
║                                                                      ║
║   TẦNG 2 — THIẾT KẾ CHI TIẾT (Agent viết 90%+, Human spot-check)   ║
║   ═══════════════════════════════════════════════════════════════    ║
║                                                                      ║
║   ├── Sequence Diagrams         ← Derive từ Blueprint + Contracts   ║
║   ├── Pipeline State Machine    ← Derive từ Blueprint + Domain      ║
║   └── Configuration Architecture ← Derive từ Blueprint + NFR        ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                          │                                           ║
║                          │ Agent tổng hợp                            ║
║                          ▼                                           ║
║                                                                      ║
║   TẦNG 3 — VẬN HÀNH (Agent viết 85%+, Human review policy)         ║
║   ═════════════════════════════════════════════════════════          ║
║                                                                      ║
║   ├── Testing Strategy          ← Derive từ Tầng 1 + 2             ║
║   ├── Deployment Strategy       ← Derive từ Tầng 1 + Business      ║
║   └── DX Guidelines             ← Tổng hợp conventions từ tất cả   ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                          │                                           ║
║                          │ Dev/Agent đọc                             ║
║                          ▼                                           ║
║                                                                      ║
║   TẦNG 4 — CODE (Dev/Agent build)                                   ║
║   ═══════════════════════════════                                    ║
║                                                                      ║
║   Lập trình viên / Agent code có ĐỦ context để:                    ║
║   ├── Build đúng kiến trúc                                          ║
║   ├── Control được hệ thống                                         ║
║   ├── Debug khi có lỗi                                              ║
║   ├── Mở rộng thêm plugin mới                                      ║
║   └── Vận hành và bảo trì                                           ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Con số tổng kết

| Tầng | Ai viết | Khối lượng | Effort ước tính |
|---|---|---|---|
| **Tầng 0** (Seed) | 🧑 Con người 100% | ~20-30 trang | 2-5 ngày suy nghĩ + viết |
| **Tầng 1** (Kiến trúc) | 🤖 Agent 70-80% + 🧑 Review | ~40-50 trang | 1-2 ngày agent + 1 ngày review |
| **Tầng 2** (Thiết kế) | 🤖 Agent 90%+ + 🧑 Spot-check | ~30-40 trang | 1 ngày agent + nửa ngày review |
| **Tầng 3** (Vận hành) | 🤖 Agent 85%+ + 🧑 Review policy | ~20-30 trang | 1 ngày agent + nửa ngày review |
| **Tổng** | | **~110-150 trang** | **~5-9 ngày (2-5 ngày human + 3-4 ngày agent)** |

> [!IMPORTANT]
> **Quy tắc vàng:** Con người viết **20-30 trang Seed** → Agent sinh ra **100-120 trang tài liệu kỹ thuật** → Dev/Agent code có đủ context build toàn bộ hệ thống.
>
> Nhưng nếu thiếu Seed hoặc Seed mơ hồ → Agent sẽ **tự bịa giả định** → Kiến trúc sai hướng ngay từ nền tảng → Nợ kỹ thuật tích lũy → Viết lại từ đầu.

---

## Workflow Đề Xuất Cụ Thể

```
Bước 1: BẠN viết 5 Seed Documents (2-5 ngày)
  │
  ├── Không cần viết hoàn hảo. Viết 70% là đủ.
  ├── Chỗ nào chưa chắc → ghi rõ "CHƯA QUYẾT ĐỊNH" 
  │   → agent sẽ đề xuất options cho bạn review.
  └── Format: Markdown, theo template ở trên.
  │
Bước 2: Giao AGENT viết Tầng 1 — Architecture (Wave 1)
  │
  ├── Agent đọc 5 Seed + architecture_properties_v2.md
  ├── Agent viết: Blueprint + Contracts + Error Strategy
  ├── BẠN review và comment (giống đang làm với tôi)
  └── Iterate 1-2 vòng cho đến khi bạn đồng ý
  │
Bước 3: Giao AGENT viết Tầng 2 — Design Detail (Wave 2)
  │
  ├── Agent đọc Seed + Tầng 1
  ├── Agent viết: Sequence Diagrams + State Machine + Config
  └── BẠN spot-check (ít cần review hơn vì derive từ Tầng 1)
  │
Bước 4: Giao AGENT viết Tầng 3 — Operations (Wave 3-4)
  │
  ├── Agent viết: Testing + Deployment + DX
  └── BẠN review policy decisions
  │
Bước 5: BẮT ĐẦU CODE
  │
  └── Dev/Agent có đủ tài liệu để build.
      Mỗi agent code 1 module, đọc cùng 1 bộ tài liệu
      → output nhất quán, không phân kỳ.
```
