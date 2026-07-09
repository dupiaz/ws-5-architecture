# Kế Hoạch: Từ v2.md → Reference Architecture + 3 Seed Documents

---

## Phân Tích 3 Hướng Tiếp Cận

### Hướng 1: Forward (Viết seed từ đầu → derive tài liệu)

```
R1, R2, R3 (viết mới) → reference_architecture.md → dubbing_product_config.md
```

| Ưu | Nhược |
|---|---|
| ✅ Đúng quy trình lý thuyết | ❌ Bỏ phí toàn bộ nội dung v2.md |
| ✅ Seed không bị bias bởi dubbing | ❌ Mất 3-5 ngày viết seed từ zero |
| | ❌ Có thể thiếu insight thực tế mà v2.md đã capture |

### Hướng 2: Reverse (Tách v2.md → suy ngược ra seed)

```
v2.md → tách → reference_architecture.md + dubbing_product_config.md → suy ngược → R1, R2, R3
```

| Ưu | Nhược |
|---|---|
| ✅ Tận dụng 100% nội dung v2.md | ⚠️ Seed có thể bị **dubbing bias** — vô tình thiết kế reference architecture "vừa khít" cho dubbing mà không tổng quát cho domain khác |
| ✅ Nhanh hơn Forward (~2 ngày) | ⚠️ "Suy ngược" đôi khi khó tách bạch: đâu là nguyên tắc tổng quát, đâu là đặc thù dubbing mà vô thức coi là tổng quát |
| ✅ Không mất insight từ v2.md | |

### Hướng 3: Hybrid (Tách → Khái quát hóa → Đúc seed) ← **KHUYẾN NGHỊ**

```
v2.md → [Classify] → [Split] → [Generalize] → [Formalize Seeds]
                                      ↑
                              Kiểm tra bằng
                              domain khác
                              (AI Photo Editor)
```

| Ưu | Nhược |
|---|---|
| ✅ Tận dụng v2.md | ⚠️ Mất thêm 1 bước Generalize |
| ✅ Có bước khái quát hóa → loại dubbing bias | |
| ✅ Có bước validate → đảm bảo thực sự tổng quát | |
| ✅ Tổng thời gian: ~2-3 ngày agent + 1 ngày review | |

> [!IMPORTANT]
> **Tại sao cần bước Generalize (Khái quát hóa)?**
>
> Ví dụ: v2.md nói *"Pipeline gồm 6 bước: Demux→ASR→Translate→TTS→Mix→Mux"*. Khi tách, bạn có thể vô tình đưa *"pipeline luôn có 6 bước"* vào reference — nhưng thực tế AI Photo Editor có thể chỉ có 3 bước. Bước Generalize sẽ chuyển thành *"pipeline có N bước cấu hình được, tối thiểu 2"*.
>
> Nếu không Generalize, reference architecture sẽ trở thành "dubbing architecture với tên generic" — không thực sự reusable.

---

## Kế Hoạch Chi Tiết (Hướng 3: Hybrid)

### Bước 1: Classify — Đánh dấu từng phần v2.md

Đi qua toàn bộ v2.md, đánh dấu mỗi section/paragraph là **[I]** Invariant hay **[V]** Variable:

| Section trong v2.md | Phân loại | Lý do |
|---|---|---|
| **Bảng thuật ngữ** | [I] 70% + [V] 30% | Thuật ngữ như GIL, DAG, IPC = invariant. Thuật ngữ như ASR, TTS, Demux = variable (domain dubbing) |
| **Bối cảnh đặc thù** | [I] 80% + [V] 20% | "Chạy trên 1 máy", "AI inference nặng" = invariant. "Quy trình lồng tiếng 6 bước" = variable |
| **Quy trình Pipeline lồng tiếng** | [V] 100% | Hoàn toàn dubbing-specific |
| **A.1 Separation of Concerns** | [I] 90% | Nguyên tắc tổng quát. Chỉ ví dụ 5 miền trách nhiệm là variable |
| **A.2 Dependency Inversion** | [I] 60% + [V] 40% | Nguyên tắc = invariant. Bảng model ASR/TTS/Translation = variable |
| **A.3 Event-Driven Reactivity** | [I] 85% | Code ví dụ PySide6 = invariant (pattern). ASRWorker cụ thể = variable |
| **A.4 Centralized State** | [I] 95% | Gần như hoàn toàn tổng quát |
| **A.5 Pipeline Composability** | [I] 70% + [V] 30% | DAG concept = invariant. Use case dubbing = variable |
| **A.6 Fault Isolation & Recovery** | [I] 90% | Kịch bản lỗi TTS = variable, nhưng nguyên tắc = invariant |
| **A.7 Contract-First Design** | [I] 80% + [V] 20% | Nguyên tắc = invariant. TranscriptionResult = variable |
| **B.1 UI Thread Sanctity** | [I] 95% | Process model gần như hoàn toàn tổng quát |
| **B.2 Process Isolation** | [I] 90% | Nguyên tắc tổng quát. WhisperX/XTTS ví dụ = variable |
| **B.3 Resource-Aware Scheduling** | [I] 85% | VRAM table cụ thể = variable, cơ chế = invariant |
| **B.4 Environment Isolation** | [I] 95% | Gần như hoàn toàn tổng quát |
| **B.5 Data Locality & Checkpoint** | [I] 70% + [V] 30% | Cấu trúc folder project cụ thể = variable |
| **B.6 Packaging & Distribution** | [I] 85% | Chiến lược "core nhẹ + plugin nặng" = invariant |
| **C. License** | [I] 60% + [V] 40% | Cơ chế license = invariant. Supabase cụ thể = variable |
| **D. Ma trận ưu tiên** | [I] 90% | Thứ tự ưu tiên đúng cho mọi hệ thống cùng archetype |

### Bước 2: Split — Tách thành 2 tài liệu

```
architecture_properties_v2.md (1219 dòng)
           │
           ├──► reference_architecture.md (~800-900 dòng)
           │    • Phần [I]: giữ nguyên, loại bỏ ví dụ dubbing-specific
           │    • Thay ví dụ dubbing bằng placeholder generic
           │    • Thêm ghi chú "Xem Product Config cho ví dụ cụ thể"
           │
           └──► dubbing_product_config.md (~400-500 dòng)  
                • Phần [V]: pipeline 6 bước, model tables, contracts cụ thể
                • Format: Configuration + rationale (tại sao chọn model này)
                • Refer back to reference_architecture.md cho nguyên tắc
```

### Bước 3: Generalize — Khái quát hóa reference

Đi qua `reference_architecture.md`, thay thế mọi đặc thù còn sót:

| Trước (dubbing-specific) | Sau (generalized) |
|---|---|
| "Model Whisper cần 3.5GB VRAM" | "AI model thường cần 1-8GB VRAM tùy size" |
| "Pipeline: Demux→ASR→Translate→TTS→Mix→Mux" | "Pipeline: N bước cấu hình qua config, mỗi bước = 1 PluginStep" |
| "WhisperXPlugin implements ASREngine" | "`ModelAPlugin implements StepEngine`" |
| "User là biên tập viên video" | "User là end-user không chuyên kỹ thuật" |
| "Vocal separation, voice cloning" | "Domain-specific AI tasks" |

**Bước Validate**: Thử áp dụng reference cho "AI Photo Editor":
- Pipeline: Import→Detect→Remove→Enhance→Export ← Có khớp với DAG engine không?
- Plugins: SAM, Stable Diffusion, GFPGAN ← Có khớp với Plugin Architecture không?
- Nếu KHÔNG khớp → reference chưa đủ tổng quát → sửa lại

### Bước 4: Formalize Seeds — Đúc kết 3 Seed Documents

Từ 2 tài liệu đã split + generalize, **đúc ngược** thành 3 seed:

```
reference_architecture.md  ──extract──►  R1: System Archetype Definition
(phần challenge descriptions)             (Thách thức bất biến + dimensions of variation)

reference_architecture.md  ──extract──►  R2: Architecture Pattern Catalog
(phần solutions & patterns)               (Pattern options + trade-offs cho mỗi challenge)

dubbing_product_config.md  ──abstract──► R3: Product Configuration Schema
(biến nội dung cụ thể                     (Template trống mà mỗi sản phẩm điền vào,
 thành form template)                      dubbing config = 1 example filled form)
```

### Bước 5: Validate — Kiểm tra tổng thể

Kiểm tra toàn bộ hệ thống tài liệu:

1. **Completeness Check**: R1 + R2 + R3 seed → agent có đủ context viết reference_architecture.md không?
2. **Instantiation Check**: Reference + R3 filled (dubbing) → agent có đủ context viết 9 GAP documents cho dubbing không?
3. **Generality Check**: Thử điền R3 cho "AI Photo Editor" → reference vẫn đúng không?

---

## Output Dự Kiến

```
docs/
├── seeds/                              ← Seed Documents (con người maintain)
│   ├── R1_system_archetype.md          ← "Desktop AI Pipeline App là gì?"
│   ├── R2_pattern_catalog.md           ← "Pattern nào giải challenge nào?"
│   └── R3_product_config_schema.md     ← "Form template cho mỗi sản phẩm"
│
├── reference/                          ← Reference Architecture (agent derive từ seeds)
│   └── reference_architecture.md       ← Kiến trúc khuôn mẫu (invariant only)
│
├── products/                           ← Product Configs (mỗi sản phẩm 1 bộ)
│   └── dubbing/
│       ├── product_config.md           ← R3 filled cho dubbing
│       └── architecture_properties.md  ← v2.md refactored (chỉ phần dubbing)
│
└── archive/
    └── architecture_properties_v2.md   ← Bản gốc, lưu tham khảo
```

## Tổng Thời Gian Ước Tính

| Bước | Ai làm | Thời gian |
|---|---|---|
| B1: Classify | 🤖 Agent | ~30 phút |
| B2: Split | 🤖 Agent + 🧑 Review | ~2-3 giờ agent + 1 giờ review |
| B3: Generalize | 🤖 Agent + 🧑 Review | ~1-2 giờ agent + 30 phút review |
| B4: Formalize Seeds | 🤖 Agent + 🧑 Review | ~2-3 giờ agent + 1 giờ review |
| B5: Validate | 🤖 Agent + 🧑 Spot-check | ~1 giờ |
| **Tổng** | | **~1-2 ngày (agent) + nửa ngày (review)** |

> [!IMPORTANT]
> **Bạn đồng ý với hướng tiếp cận Hybrid này không?** Nếu đồng ý, tôi sẽ bắt đầu từ **Bước 1 (Classify)** — đi qua toàn bộ v2.md và đánh dấu Invariant/Variable cho từng section, trình bạn review trước khi split.
