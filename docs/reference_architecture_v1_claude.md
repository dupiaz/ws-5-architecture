# Kiến Trúc Tham Chiếu — Desktop AI Pipeline Application

> Tài liệu này định nghĩa các **tính chất kiến trúc bất biến** cho lớp hệ thống **Desktop Application chạy AI Inference Pipeline bằng Python**. Mọi nguyên tắc ở đây áp dụng **bất kể domain nghiệp vụ cụ thể** (video dubbing, photo editing, document processing, medical imaging...).
>
> Đây là **Reference Architecture** — kiến trúc khuôn mẫu. Mỗi sản phẩm cụ thể sẽ có thêm một **Product Configuration** riêng để điền thông tin domain.

---

## Bảng Thuật Ngữ Tổng Hợp

> [!NOTE]
> Bảng này giải nghĩa các thuật ngữ kỹ thuật xuất hiện trong tài liệu, giúp người mới dễ theo dõi. Có thể quay lại tra cứu bất kỳ lúc nào.

| Thuật ngữ | Giải nghĩa dễ hiểu |
|---|---|
| **Inference (Suy luận)** | Quá trình **chạy một model AI để cho ra kết quả**. Khác với Training (huấn luyện) là quá trình dạy model. Inference nặng vì model phải xử lý hàng triệu phép tính toán học trên GPU |
| **Dispatch (Phát lệnh)** | Hành động **gửi một yêu cầu đi** mà **không chờ kết quả trả về**. Giống như gửi tin nhắn rồi đi làm việc khác, thay vì gọi điện và phải đứng chờ người ta trả lời |
| **DAG (Directed Acyclic Graph)** | **Đồ thị có hướng không tuần hoàn** — một sơ đồ mô tả các bước công việc theo thứ tự, trong đó mỗi bước chỉ đi tới (không quay lại). Giải thích chi tiết ở [Mục A.5](#5-pipeline-composability--khả-năng-tổ-hợp-pipeline) |
| **IPC (Inter-Process Communication)** | **Giao tiếp liên tiến trình** — cơ chế để 2 chương trình đang chạy riêng biệt nói chuyện với nhau. Các cách IPC phổ biến: gọi HTTP qua localhost, gRPC, pipe (đường ống stdin/stdout), shared memory |
| **Segfault (Segmentation Fault)** | **Lỗi truy cập bộ nhớ trái phép** — khi chương trình cố đọc/ghi vào vùng bộ nhớ không thuộc về nó. Thường xảy ra trong code C/C++ bên trong các thư viện AI (PyTorch, CUDA). Khi segfault xảy ra, chương trình bị hệ điều hành **ép buộc tắt ngay lập tức** mà không kịp xử lý lỗi (try/catch không bắt được) |
| **GIL (Global Interpreter Lock)** | **Khóa toàn cục của Python** — cơ chế trong Python chỉ cho phép **1 thread chạy Python code tại 1 thời điểm**, kể cả trên máy nhiều lõi CPU. Giải thích chi tiết ở [Mục B.1](#1-ui-thread-sanctity--bảo-vệ-tuyệt-đối-ui-thread) |
| **State (Trạng thái)** | **Dữ liệu hiện tại** mà ứng dụng đang giữ trong bộ nhớ. Ví dụ: project đang mở, pipeline đang chạy bước nào, user đã chọn cấu hình nào... Tất cả gộp lại gọi là "state" của ứng dụng |
| **Event Bus (Xe buýt sự kiện)** | **Kênh giao tiếp trung tâm** — giống như một "bảng thông báo" chung. Ai muốn thông báo gì thì "dán lên bảng" (publish). Ai quan tâm thì "đăng ký theo dõi" (subscribe). Không ai cần biết ai đang đăng ký |
| **Adapter (Bộ chuyển đổi)** | **Lớp trung gian chuyển đổi định dạng**. Giống như ổ cắm điện chuyển đổi 3 chân sang 2 chân — plugin AI bên trong khác format, adapter biến đổi cho khớp với format chuẩn của hệ thống |
| **Interface / Contract (Giao diện / Hợp đồng)** | **Bản cam kết** về hình dạng dữ liệu vào/ra. Bất kỳ plugin nào cũng phải nhận input và trả output đúng format đã cam kết — giống hợp đồng pháp lý |
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
| **REST API** | **Giao tiếp qua HTTP** — gửi request (yêu cầu) đến một URL và nhận response (phản hồi). Giống như gửi đơn hàng qua website và nhận kết quả |
| **gRPC** | Giao thức giao tiếp **nhanh hơn REST** (dùng binary thay vì text), phù hợp cho giao tiếp giữa các service nội bộ. Phức tạp hơn REST khi setup |

> [!NOTE]
> Các thuật ngữ đặc thù domain (ví dụ: ASR, TTS, FFmpeg cho lĩnh vực audio/video) được định nghĩa trong **Product Configuration** của từng sản phẩm cụ thể.

---

## Bối Cảnh Đặc Thù — Tại Sao Desktop AI Pipeline App Khác Biệt

Trước khi đi vào từng tính chất, cần hiểu rõ bối cảnh đặc thù mà kiến trúc này phải phục vụ — vì nó **khác hoàn toàn** với cả web app lẫn desktop app truyền thống:

| Đặc thù | Nghĩa là gì | Hệ quả cho kiến trúc |
|---|---|---|
| **Chạy trên 1 máy duy nhất** của user | Mọi thứ (giao diện, AI, database) đều chạy trên laptop/PC của user. Không có server riêng | Không thể "thêm server" khi thiếu sức mạnh. Phải quản lý tinh tế CPU, RAM, GPU trên 1 máy duy nhất. Phải biết máy user có GPU hay không, có bao nhiêu VRAM |
| **AI inference cực nặng** | Model AI thường cần load 1-8GB vào GPU VRAM, và mỗi lần inference có thể mất từ vài giây đến hàng chục phút | Nếu code AI chạy cùng chỗ với code giao diện, giao diện sẽ **đơ cứng** trong suốt thời gian AI xử lý. Phải tách riêng phần chạy AI ra khỏi phần hiển thị giao diện |
| **Đa dạng model/API** thay đổi liên tục | Model state-of-the-art hôm nay có thể bị thay thế chỉ sau vài tháng. User có thể muốn dùng API cloud thay vì chạy local | Kiến trúc phải cho phép **thay thế** bất kỳ model/API nào mà **không cần viết lại** phần logic chính. Giống thay pin điện thoại — chỉ cần đúng kích thước, hãng nào cũng được |
| **Pipeline nhiều bước** | Quy trình xử lý gồm N bước nối tiếp/song song (cụ thể bao nhiêu bước tùy domain — xem Product Configuration). Mỗi bước có thể mất từ vài giây đến hàng chục phút | Cần cơ chế "save game" (checkpoint) sau mỗi bước. Nếu bước N bị lỗi, chạy lại từ bước N thay vì từ đầu. Mất điện giữa chừng không được mất toàn bộ công việc |
| **User là người dùng cuối**, không phải lập trình viên | User không biết code — họ là chuyên gia trong domain của họ (biên tập viên, bác sĩ, designer...) | App phải ổn định, lỗi phải hiện thông báo dễ hiểu, **tuyệt đối không** hiện lỗi kỹ thuật kiểu `Traceback (most recent call last): ...` |
| **Chạy offline được** nhưng cũng hỗ trợ cloud API | Khi có internet: gọi cloud API (chất lượng cao, tốn phí). Khi không có internet: dùng model chạy local trên máy (miễn phí, chất lượng tùy GPU) | Hệ thống phải hoạt động **giống hệt nhau** dù dùng local model hay cloud API. Pipeline không cần biết đang dùng cái nào — chỉ cần gửi input và nhận output theo format chuẩn |

> [!NOTE]
> **Pipeline cụ thể của từng domain** (bao nhiêu bước, tên từng bước, input/output) được định nghĩa trong **Product Configuration**. Reference Architecture chỉ định nghĩa **cơ chế** chạy pipeline, không định nghĩa pipeline cụ thể.

---

# PHẦN A — KIẾN TRÚC LOGIC (Logical Architecture)

Kiến trúc logic trả lời câu hỏi: **"Các thành phần được tổ chức và giao tiếp với nhau theo nguyên tắc nào?"**

---

## 1. Separation of Concerns — Phân Tách Trách Nhiệm

### Định nghĩa
Mỗi thành phần trong hệ thống chỉ chịu trách nhiệm cho **đúng một khía cạnh** của bài toán. Không có thành phần nào vừa vẽ UI vừa gọi AI model vừa quản lý file.

### Tại sao quan trọng (tổng quát)
Khi trách nhiệm bị trộn lẫn, một thay đổi nhỏ ở chức năng A sẽ vô tình phá vỡ chức năng B. Đây là nguyên nhân số 1 gây ra bug "ở đâu ra" trong các dự án phần mềm.

### Tại sao đặc biệt quan trọng cho kiểu hệ thống này

Hệ thống Desktop AI Pipeline có **ít nhất 5 miền trách nhiệm rất khác biệt về bản chất**:

```
┌─────────────┐   ┌──────────────┐   ┌──────────────┐   ┌─────────────┐   ┌────────────┐
│  Giao diện  │   │  Điều phối   │   │  Nghiệp vụ   │   │  AI/ML      │   │  Hạ tầng   │
│  (Qt/UI)    │   │  (Pipeline)  │   │  (Domain)    │   │  (Inference) │   │  (File/DB) │
│             │   │              │   │              │   │             │   │            │
│ PySide6     │   │ DAG, State   │   │ Domain-      │   │ PyTorch,    │   │ FFmpeg,    │
│ Signals     │   │ Checkpoint   │   │ specific     │   │ CUDA,       │   │ SQLite,    │
│ QSS Theme   │   │ Scheduling   │   │ Logic        │   │ REST APIs   │   │ File I/O   │
└─────────────┘   └──────────────┘   └──────────────┘   └─────────────┘   └────────────┘
```

> [!NOTE]
> Miền **"Nghiệp vụ (Domain)"** thay đổi tùy sản phẩm: có thể là Audio Processing (dubbing), Image Processing (photo editing), hay Document Processing (OCR). Xem **Product Configuration** cho chi tiết domain cụ thể.

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
Các module cấp cao (Orchestrator, Use Case) **không bao giờ phụ thuộc trực tiếp** vào module cấp thấp (model/API cụ thể). Cả hai cùng phụ thuộc vào **một abstraction (interface — bản hợp đồng trung gian) ở giữa**.

### Tại sao đây là tính chất quan trọng nhất cho yêu cầu "linh hoạt model/API"

```
❌ SAI (Gắn chặt - Tight coupling):
   Orchestrator → import specific_model → gọi specific_model.process()
   
   Hậu quả: Muốn đổi model phải sửa Orchestrator
   
✅ ĐÚNG (Đảo ngược phụ thuộc - Dependency Inversion):
   Orchestrator → gọi StepEngine.process()     ← Interface (bản hợp đồng chung)
                                                     ↑
                                                 ModelAPlugin implements StepEngine
                                                 ModelBPlugin implements StepEngine
                                                 CloudAPIPlugin implements StepEngine
```

### Tại sao đặc biệt quan trọng cho kiểu hệ thống này

Thế giới AI thay đổi **cực nhanh** — "state-of-the-art" (tiên tiến nhất) hôm nay có thể bị thay thế chỉ sau vài tháng. Mỗi bước trong pipeline thường có **4-7+ lựa chọn công nghệ** (local models + cloud APIs). Nhân N bước = hàng trăm tổ hợp có thể.

> [!IMPORTANT]
> **Đây chính là lý do Dependency Inversion quan trọng bậc nhất.** Nếu code gắn chặt vào 1 công nghệ, mỗi lần đổi = viết lại. Với Dependency Inversion, đổi bất kỳ = chỉ viết 1 adapter mới (~100-200 dòng code), không sửa gì ở Core.
>
> Danh sách các công nghệ/model cụ thể cho từng bước pipeline được liệt kê trong **Product Configuration**.

### Cách triển khai — Pattern chuẩn

```python
# core/engine_interface.py — INTERFACE (không biết gì về model cụ thể)
from abc import ABC, abstractmethod

class StepEngine(ABC):
    @abstractmethod
    def process(self, input_data: StepInput) -> StepOutput:
        """Trả về kết quả chuẩn hóa, bất kể công nghệ bên dưới."""
        ...

# plugins/step_a/model_x/adapter.py — IMPLEMENTATION
class ModelXAdapter(StepEngine):
    def process(self, input_data):
        # Gọi Model X, biến đổi output thành StepOutput chuẩn
        ...

# plugins/step_a/model_y/adapter.py — THÊM MỚI, KHÔNG SỬA GÌ Ở CORE
class ModelYAdapter(StepEngine):
    def process(self, input_data):
        # Gọi Model Y, biến đổi output thành StepOutput chuẩn
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

Trong hệ thống AI Pipeline, gần như **mọi tác vụ core** đều mất hàng chục giây đến hàng phút:

| Tác vụ | Thời gian điển hình |
|---|---|
| Load AI model vào GPU (VRAM) | 10-60 giây |
| Chạy AI inference cho 1 batch | 10 giây - 30 phút |
| Xử lý media (encode/decode) | 10-120 giây |
| Gọi Cloud API (chờ response) | 2-30 giây |

### Giải pháp: Event-Driven Architecture với PySide6 Signals & Slots

```
UI Thread                    Worker Thread/Process
─────────                    ────────────────────
  │                                   │
  ├── dispatch("START_STEP") ───────► │   ← "Gửi lệnh rồi quay về ngay"
  │   (trả về ngay, UI vẫn mượt)     ├── Load model...
  │                                   ├── Process...
  │ ◄── event("PROGRESS", 50%) ──────┤   ← "Worker báo cáo tiến độ"
  │   (cập nhật progress bar)         │
  │ ◄── event("PROGRESS", 100%) ─────┤
  │ ◄── event("STEP_COMPLETE", data) ─┤   ← "Worker báo xong việc"
  │   (hiển thị kết quả)             │
```

PySide6 **đã có sẵn** cơ chế Event-Driven tuyệt vời gọi là **Signals & Slots**:

- **Signal** = Sự kiện phát ra (giống chuông báo)
- **Slot** = Hàm xử lý khi nhận được signal (giống người nghe chuông rồi làm gì đó)
- **QThread** = Thread riêng biệt để chạy tác vụ nặng mà không ảnh hưởng UI

### Pattern chuẩn: Worker + Signal/Slot

```python
from PySide6.QtCore import QObject, Signal, Slot, QThread


# ═══════════════════════════════════════════════════════════
# WORKER — Chạy trên thread riêng, KHÔNG BAO GIỜ chạm vào UI
# ═══════════════════════════════════════════════════════════
class PipelineStepWorker(QObject):
    """Worker xử lý 1 bước pipeline — chạy trên thread riêng."""

    # Khai báo các Signal (sự kiện) mà worker có thể phát ra
    progress = Signal(int, str)        # (phần trăm, thông báo)
    completed = Signal(object)         # (kết quả xử lý)
    error = Signal(str)                # (thông báo lỗi)

    def __init__(self, input_data, plugin_name: str):
        super().__init__()
        self.input_data = input_data
        self.plugin_name = plugin_name

    @Slot()
    def run(self):
        """Hàm chính — chạy trên Worker Thread, KHÔNG PHẢI UI Thread."""
        try:
            # Bước 1: Load plugin theo tên (Dependency Inversion!)
            self.progress.emit(10, "Đang khởi tạo model...")
            plugin = PluginRegistry.get_plugin(self.plugin_name)

            # Bước 2: Chạy inference (có thể mất rất lâu)
            self.progress.emit(30, "Đang xử lý...")
            result = plugin.process(self.input_data)

            # Bước 3: Phát signal kết quả
            self.progress.emit(100, "Hoàn thành!")
            self.completed.emit(result)

        except Exception as e:
            self.error.emit(f"Lỗi xử lý: {str(e)}")


# ═══════════════════════════════════════════════════════════
# UI VIEW — Chạy trên Main Thread, CHỈ LÀM VIỆC VỚI GIAO DIỆN
# ═══════════════════════════════════════════════════════════
class StepView(QWidget):
    """Giao diện cho 1 bước trong pipeline."""

    def on_start_button_clicked(self):
        """Khi user bấm nút 'Bắt đầu'."""

        # 1. Tạo worker và thread riêng
        self.worker = PipelineStepWorker(
            input_data=self.get_input(),
            plugin_name=self.get_selected_plugin()
        )
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        # 2. Kết nối signals → slots (ai phát gì, ai nhận gì)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.completed.connect(self.on_completed)
        self.worker.error.connect(self.on_error)

        # 3. Bắt đầu! UI KHÔNG BỊ BLOCK — trả về ngay lập tức
        self.thread.start()
        self.start_button.setEnabled(False)
        self.status_label.setText("Đang xử lý...")

    @Slot(int, str)
    def on_progress(self, percent, message):
        """Nhận tiến độ từ worker → cập nhật thanh tiến trình."""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    @Slot(object)
    def on_completed(self, result):
        """Nhận kết quả từ worker → hiển thị."""
        self.display_result(result)
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
> **Điểm mấu chốt:** Khi user bấm nút, `self.thread.start()` trả về **ngay lập tức**. UI vẫn mượt mà. Worker chạy inference trên thread riêng. Mỗi khi worker phát signal `progress`, UI tự động cập nhật progress bar. **Không bao giờ đơ giao diện.**

### Vi phạm sẽ gây ra
- App đơ mỗi khi chạy AI inference
- User mất niềm tin, bỏ app
- Không thể cancel task giữa chừng (vì UI bị block, nút Cancel không click được)

---

## 4. Centralized State Management — Quản Lý Trạng Thái Tập Trung

### Định nghĩa
Toàn bộ trạng thái ứng dụng (project hiện tại, tiến trình pipeline, cấu hình plugin đang chọn...) được lưu tại **một nơi duy nhất** (Global Store). Mọi thành phần đọc/ghi state thông qua Store này.

### Tại sao quan trọng cho Desktop app (khác Web app)

Trong web app, mỗi request (yêu cầu) là stateless (không lưu trạng thái) — server xử lý xong thì quên.

Trong desktop app, **mọi thứ là stateful** (luôn giữ trạng thái):
- User mở project → tất cả các tab phải biết project nào đang mở
- User thay đổi cấu hình → tất cả module liên quan phải biết
- Pipeline đang chạy 60% → tất cả các view phải hiện thanh tiến trình
- User thay đổi API key → tất cả plugin liên quan phải biết

Nếu mỗi feature tự quản lý state riêng, sẽ xảy ra:
- **State inconsistency (trạng thái không đồng bộ):** Feature A nghĩ dùng config X, Feature B nghĩ dùng config Y
- **Spaghetti communication (giao tiếp rối loạn):** Feature A gọi Feature B để hỏi state → Feature B gọi Feature C → vòng lặp phụ thuộc
- **Khó persist/restore (khó lưu/khôi phục):** Khi app restart, phải khôi phục state ở N nơi khác nhau

### Pattern chuẩn: GlobalStore + Signals

```python
from PySide6.QtCore import QObject, Signal


class GlobalStore(QObject):
    """
    Nơi lưu trữ DUY NHẤT toàn bộ trạng thái của ứng dụng.
    
    Mọi feature (tab) đều đọc/ghi state thông qua đây.
    Khi state thay đổi, các Signal tự động thông báo cho UI cập nhật.
    """

    # ── Khai báo Signals: mỗi khi state thay đổi, phát signal ──
    project_changed = Signal(object)
    pipeline_progress = Signal(str, int)    # (step_name, percent)
    selected_plugin_changed = Signal(str, str)  # (step_name, plugin_name)

    def __init__(self):
        super().__init__()
        self._current_project = None
        self._plugin_config = {}    # step_name → plugin_name

    def set_current_project(self, project):
        """Khi user mở project mới → cập nhật state → thông báo TẤT CẢ các tab."""
        self._current_project = project
        self.project_changed.emit(project)

    def set_plugin(self, step_name: str, plugin_name: str):
        """Khi user chọn plugin khác → thông báo."""
        self._plugin_config[step_name] = plugin_name
        self.selected_plugin_changed.emit(step_name, plugin_name)


# ── Sử dụng trong Feature View ──
class FeatureView(QWidget):
    def __init__(self, store: GlobalStore):
        super().__init__()
        self.store = store
        self.store.project_changed.connect(self.on_project_changed)

    def on_project_changed(self, project):
        """Tự động được gọi khi user mở project khác ở BẤT KỲ tab nào."""
        self.title_label.setText(f"Dự án: {project.name}")
```

### Mô hình tổng quan

```
                    ┌─────────────────────┐
                    │    GLOBAL STORE      │
                    │                     │
                    │  current_project    │   ← Duy nhất 1 nơi lưu
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
        │ View A   │ │ View B   │ │ View C   │
        └──────────┘ └──────────┘ └──────────┘
        
    Mỗi View chỉ "đăng ký theo dõi" những state nó cần.
    Khi state thay đổi, View TỰ ĐỘNG cập nhật giao diện.
    Không Feature nào cần biết Feature khác tồn tại.
```

### Vi phạm sẽ gây ra
- Dữ liệu không đồng bộ giữa các màn hình
- **Bug "phantom" (ma)** — loại bug chỉ xảy ra khi mở đúng tổ hợp tab theo đúng thứ tự, cực khó tái tạo khi debug
- Không thể implement Undo/Redo (vì không biết state nằm ở đâu)

---

## 5. Pipeline Composability — Khả Năng Tổ Hợp Pipeline

### Định nghĩa
Quy trình xử lý phải được mô tả dưới dạng **cấu hình** (configuration), không phải **code cứng** (hardcoded). Mỗi bước là một node (điểm nút) trong DAG, có thể thêm/bớt/thay đổi thứ tự.

### DAG là gì? Tại sao lại là DAG?

**DAG = Directed Acyclic Graph = Đồ thị có hướng không tuần hoàn.**

Hãy tưởng tượng bạn vẽ sơ đồ quy trình trên bảng trắng:
- Mỗi **ô** (node) là một bước công việc
- Mỗi **mũi tên** (edge) nối từ ô này sang ô khác, chỉ hướng "làm xong cái này → mới đến cái kia"
- **Không có vòng tròn** — không bao giờ quay lại bước đã làm (vì sẽ thành vòng lặp vô tận)

**Tại sao DAG mà không phải danh sách tuần tự đơn giản?**

Vì một số bước có thể chạy **song song**. DAG cho phép mô tả cả tuần tự lẫn song song trong cùng 1 cấu trúc.

**DAG được dùng ở đâu ngoài dự án này?**

| Lĩnh vực | Ví dụ | Vì sao dùng DAG |
|---|---|---|
| **CI/CD** (triển khai phần mềm) | GitHub Actions, GitLab CI | Build → Test → Deploy, một số bước chạy song song |
| **Xử lý dữ liệu lớn** | Apache Airflow, Apache Spark | ETL pipeline: Extract → Transform → Load, hàng trăm bước |
| **AI/ML Training** | Kubeflow, MLflow | Thu thập data → Tiền xử lý → Train → Evaluate → Deploy |
| **Đồ họa 3D / Video** | Blender, Nuke, DaVinci Resolve | Node-based compositing: các filter/effect nối thành chuỗi |
| **Build hệ thống** | Make, Bazel, Gradle | Compile file A trước, rồi mới link với file B |

### Tại sao quan trọng cho kiểu hệ thống này

Không phải lúc nào user cũng cần chạy full pipeline. Tùy use case, user có thể chỉ cần chạy một phần. Nếu pipeline bị hardcode, mỗi use case = 1 luồng code riêng → code trùng lặp, bug ở chỗ này mà chỗ kia không sửa.

> [!NOTE]
> Danh sách use cases và pipeline configurations cụ thể cho từng sản phẩm nằm trong **Product Configuration**.

### Pattern chuẩn: Config-Driven Pipeline

```python
# Pipeline được mô tả bằng config, không phải code
full_pipeline = Pipeline([
    Step("step_1", module="module_a", plugin="model_x"),
    Step("step_2", module="module_b", plugin="cloud_api_y"),
    Step("step_3", module="module_c", plugin="model_z"),
])

# User chỉ cần 2 bước đầu? Tạo config mới
partial_pipeline = Pipeline([
    Step("step_1", module="module_a", plugin="model_x"),
    Step("step_2", module="module_b", plugin="cloud_api_y"),
])

# Orchestrator chạy bất kỳ pipeline nào theo cùng một cơ chế
orchestrator.execute(full_pipeline, project_context)
```

### Vi phạm sẽ gây ra
- **Mỗi use case mới = viết lại logic điều phối**
- **Không thể cho user tùy chỉnh pipeline qua giao diện**
- Khó implement retry/resume cho từng bước riêng lẻ

---

## 6. Fault Isolation & Recovery — Cô Lập Lỗi và Phục Hồi

### Định nghĩa
Khi một bước trong pipeline thất bại (model crash, API timeout, hết VRAM), hệ thống phải:
1. **Cô lập** lỗi — không lan sang bước khác
2. **Lưu checkpoint** (điểm lưu) — dữ liệu đã xử lý xong không bị mất
3. **Cho phép resume** (tiếp tục) — chạy lại từ bước lỗi, không phải từ đầu

### Tại sao đặc biệt quan trọng cho kiểu hệ thống này

Hãy tưởng tượng kịch bản: User xử lý 1 project lớn. Pipeline đã chạy qua nhiều bước (tổng cộng 60+ phút), rồi gặp lỗi ở bước cuối (API rate limit, hết VRAM, mất mạng...).

**Nếu không có checkpoint:** Mất toàn bộ công việc. User phải chạy lại từ đầu. → User bỏ app.

**Nếu có checkpoint:** Hệ thống lưu trạng thái sau mỗi bước hoàn thành. Resume từ bước lỗi. → User hài lòng.

### Cơ chế cần thiết

```
Pipeline Execution:
  Step 1 ✅ → checkpoint_1.json (lưu output step 1)
  Step 2 ✅ → checkpoint_2.json (lưu output step 2)
  Step 3 ✅ → checkpoint_3.json (lưu output step 3)
  Step 4 ❌ → checkpoint_4_partial.json (lưu phần đã xong)
  
Resume: Đọc checkpoint_4_partial → chỉ chạy lại phần còn lại
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
> **Nguyên lý:** Thay vì thiết kế hệ thống xung quanh **công nghệ cụ thể**, hãy thiết kế xung quanh **hợp đồng dữ liệu** (input/output format). Công nghệ sẽ thay đổi, nhưng bản chất công việc thì không:
> - Bất kể dùng model nào cho bước X, đầu vào và đầu ra luôn có cùng format
> - Adapter trong mỗi plugin chịu trách nhiệm biến đổi output đặc thù → contract chuẩn
>
> **Khi bạn định nghĩa "hợp đồng" trước, bạn đang nói:** "Tôi không quan tâm bên trong dùng công nghệ gì, miễn là đầu vào/đầu ra đúng format này." → Thay đổi công nghệ = thay đổi bên trong plugin, hệ thống bên ngoài không biết, không cần sửa.

### Pattern chuẩn: Dataclass Contract + Adapter

```python
from dataclasses import dataclass

@dataclass
class StepOutput:
    """Contract chuẩn — BẤT KỲ plugin nào cho step này đều phải trả về format này."""
    data: dict
    metadata: dict
    status: str
    processing_time_seconds: float
```

> [!NOTE]
> Data contracts cụ thể cho từng bước pipeline (ví dụ: `TranscriptionResult` cho bước nhận dạng giọng nói, `TranslationResult` cho bước dịch thuật) được định nghĩa trong **Product Configuration**.

### Vi phạm sẽ gây ra
- Mỗi lần thêm plugin mới phải sửa module ở trên
- Data format inconsistency gây bug ở downstream modules
- Không thể test module độc lập

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
│   AI SERVICE #1        │  │   AI SERVICE #2        │
│   (Chạy riêng biệt)   │  │   (Chạy riêng biệt)   │
│                        │  │                        │
│   AI Model A + CUDA    │  │   AI Model B + CUDA    │
│   Môi trường Python    │  │   Môi trường Python    │
│   riêng                │  │   riêng                │
│                        │  │                        │
│   Giao tiếp qua:       │  │   Giao tiếp qua:      │
│   - HTTP (FastAPI)     │  │   - HTTP (FastAPI)     │
│   - SSE (streaming)    │  │   - SSE (streaming)    │
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

- **Crash containment (ngăn chặn sập lan):** Khi model AI gặp **segfault** — hệ điều hành ép tắt chương trình ngay lập tức. Nếu chạy cùng process → cả app chết. Nếu chạy trong subprocess → chỉ subprocess chết, app chính thông báo user "Model bị lỗi, vui lòng thử lại"
- **Dependency isolation:** Mỗi model có thể cần Python environment khác nhau
- **VRAM control:** Có thể giới hạn VRAM per-process để tránh OOM

---

## 2. Process Isolation cho AI Models — Cô Lập Tiến Trình

### Định nghĩa
Mỗi AI model **nặng** chạy trong process (tiến trình) riêng, giao tiếp với app chính qua **IPC** — cụ thể là **HTTP (FastAPI)** trên localhost.

### Tại sao cần thiết

| Vấn đề | Giải pháp bằng Process Isolation |
|---|---|
| **Xung đột thư viện:** Model A cần `numpy==1.24`, Model B cần `numpy==1.26` | Mỗi process có Python env riêng, cài phiên bản khác nhau |
| **Hết bộ nhớ GPU:** 2 model cùng load vào VRAM = OOM | Orchestrator quyết định load/unload per-process |
| **Ngăn sập lan:** CUDA segfault trong model A | Chỉ subprocess chết, app chính bắt lỗi và thông báo user thân thiện |
| **Mở rộng tương lai:** Muốn chạy AI trên remote GPU server trong LAN hoặc cloud | Đổi IPC từ `localhost` → `192.168.x.x` hoặc remote URL, không sửa app chính |

### Cơ chế giao tiếp: FastAPI trên localhost

```
App chính                              AI Subprocess (FastAPI server)
─────────                              ────────────────────────────
    │                                       │
    ├─── HTTP POST /process ──────────────► │
    │    {"input": "path/to/file",         │
    │     "config": {...}}                 │
    │                                       ├── Load model (nếu chưa)
    │                                       ├── Inference (chạy AI)...
    │ ◄── SSE: progress 30% ────────────────┤  (Server gửi tiến độ liên tục)
    │ ◄── SSE: progress 70% ────────────────┤
    │ ◄── HTTP 200: result ─────────────────┤
    │    {"output": {...}}                 │
```

> [!TIP]
> **Tại sao FastAPI?**
>
> | Tiêu chí | FastAPI | Flask |
> |---|---|---|
> | **Async support** | ✅ Có sẵn (native async/await) — quan trọng để xử lý SSE streaming tiến độ | ❌ Cần extension |
> | **Tự động tạo API docs** | ✅ Swagger UI tự động tại `/docs` — debug cực tiện | ❌ Phải cài thêm |
> | **Type validation** | ✅ Pydantic tích hợp — kiểm tra dữ liệu vào/ra tự động, bắt lỗi sớm | ❌ Phải tự viết |
> | **Hiệu năng** | ✅ Nhanh gấp 2-3x Flask | Đủ dùng cho local |
> | **Phù hợp cho project** | ✅ **Rất phù hợp** — cần streaming progress, type-safe contracts | Phù hợp cho prototype |
>
> **Lý do chính:** FastAPI + Pydantic **enforce Contract-First tự động** — khớp hoàn hảo với triết lý kiến trúc.

---

## 3. Resource-Aware Scheduling — Lập Lịch Theo Tài Nguyên

### Định nghĩa
Orchestrator (bộ điều phối) phải **biết** tài nguyên hiện có (VRAM trống, RAM trống, mức sử dụng GPU) trước khi quyết định chạy task tiếp theo.

### Tại sao bắt buộc cho desktop chạy AI

Trên server, có thể scale up bằng thêm GPU. Trên desktop user, **thường chỉ có 1 GPU, 6-24GB VRAM**.

AI model thường cần 1-8GB VRAM mỗi model. Nếu 2 model load đồng thời trên GPU hạn chế → OOM → crash.

**Resource Manager** phải:
1. Kiểm tra VRAM hiện tại (qua `nvidia-smi` hoặc thư viện `pynvml`)
2. Biết mỗi model cần bao nhiêu VRAM (khai báo trong plugin metadata)
3. Ra lệnh **unload** model cũ trước khi **load** model mới
4. Queue (xếp hàng) task nếu không đủ tài nguyên

> [!NOTE]
> Bảng VRAM requirements cụ thể cho từng model nằm trong **Product Configuration**.

### Vi phạm sẽ gây ra
- CUDA Out of Memory → app crash
- Máy user bị chiếm hết RAM → cả hệ thống chậm
- Không thể chạy trên máy GPU yếu

---

## 4. Environment Isolation — Cô Lập Môi Trường

### Định nghĩa
App chính, mỗi local AI plugin, và các công cụ hệ thống có **môi trường chạy tách biệt** — tránh xung đột thư viện (dependency conflict).

### Chiến lược đề xuất

```
application_root/
├── app/                          ← App chính (PySide6, orchestrator, UI)
│   └── venv/                     ← Python venv cho app chính (nhẹ, không có torch)
│
├── services/
│   ├── service_a/
│   │   └── venv/                 ← Isolated venv: torch + model_a + CUDA
│   │   └── server.py             ← FastAPI server, chạy như subprocess
│   │
│   └── service_b/
│       └── venv/                 ← Isolated venv: torch + model_b + CUDA
│       └── server.py             ← FastAPI server, chạy như subprocess
│
├── tools/
│   ├── tool_x.exe                ← Binary, không cần Python
│   └── tool_y.exe                ← Binary, không cần Python
```

### Tại sao Docker cho desktop user?

> [!WARNING]
> **Docker KHÔNG phải lựa chọn tốt cho end-user desktop app.** Yêu cầu user cài Docker Desktop trên Windows là rào cản lớn (cần Hyper-V/WSL2, ~4GB RAM overhead, phức tạp khi setup GPU passthrough). **Isolated venv + subprocess** là giải pháp thực tế hơn cho desktop distribution.
>
> Docker chỉ nên dùng cho development/CI environment, không phải production deployment cho end-user.

---

## 5. Data Locality & Checkpoint — Dữ Liệu Cục Bộ và Điểm Lưu

### Định nghĩa
Mọi dữ liệu trung gian được lưu trên disk theo cấu trúc rõ ràng, cho phép resume pipeline từ bất kỳ bước nào.

### Cấu trúc project folder — Pattern chuẩn

```
storage/projects/{project_id}/
├── metadata.json                 ← Trạng thái pipeline, timestamps, config
├── input/
│   └── {source_file}
├── intermediate/                  ← Dữ liệu trung gian — "save game" sau mỗi bước
│   ├── step_01_{name}/
│   │   ├── {output_files}
│   │   └── status.json           ← {"completed": true, "duration_sec": 12.5}
│   ├── step_02_{name}/
│   │   ├── {output_files}
│   │   └── status.json
│   └── step_N_{name}/
│       ├── {partial_output}      ← Nếu step hỗ trợ partial checkpoint
│       └── status.json           ← {"completed_items": 180, "total": 200}
├── output/
│   └── {final_output_file}
└── logs/
    └── pipeline.log              ← Structured log cho debug
```

### Tại sao cấu trúc này

1. **Resume granularity (độ chi tiết khi tiếp tục):** Step lỗi → chỉ chạy lại phần chưa xong
2. **Debug transparency (debug dễ dàng):** Mở folder intermediate, xem từng bước đã output gì → debug bằng mắt
3. **User inspection (user kiểm tra được):** User có thể xem/sửa output trung gian trước khi chạy bước tiếp theo
4. **Backup/share:** Copy folder project = copy toàn bộ trạng thái

---

## 6. Packaging & Distribution — Đóng Gói và Phân Phối

### Thách thức đặc thù

Desktop app Python + AI models = **bài toán đóng gói phức tạp nhất** trong thế giới Python:

| Thành phần | Kích thước điển hình | Ghi chú |
|---|---|---|
| App chính (PySide6 + logic) | ~150 MB | PyInstaller bundle |
| PyTorch + CUDA runtime | ~2-3 GB | Cần GPU-specific build |
| AI model weights (trọng số) | ~1-5 GB mỗi model | Download lần đầu |
| Tool binaries (FFmpeg, etc.) | ~5-100 MB | Đi kèm installer |

### Chiến lược đề xuất: Core nhẹ + Plugin nặng tải sau

```
Installer (NSIS/Inno Setup):
  1. Cài app chính (~200 MB)           ← Cài nhanh, dùng được ngay (cloud API mode)
  2. First-run wizard:
     - "Bạn có muốn cài AI Model A local?"  → Download venv + model
     - "Bạn có muốn cài AI Model B local?"  → Download venv + model
     - "Hay dùng Cloud API?"                 → Chỉ cần API key, không cài gì thêm
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

### Lựa chọn 1: Supabase

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
| **Offline** | ⚠️ Cần thiết kế thêm offline grace period |

### Lựa chọn 2: Keygen.sh — License API chuyên dụng

| Tiêu chí | Đánh giá |
|---|---|
| **Chi phí** | ✅ Free tier cho solo developer (100 licenses). Paid plans từ $49/tháng |
| **Chuyên biệt** | ✅ Thiết kế riêng cho việc quản lý license phần mềm desktop |
| **Tính năng** | ✅ License keys, machine fingerprinting, feature flags, trial periods |
| **Offline** | ✅ Hỗ trợ offline license validation bằng cryptographic signatures |
| **API** | ✅ REST API rõ ràng, SDK cho Python |
| **Nhược điểm** | ⚠️ Free tier giới hạn 100 licenses — cần trả phí khi scale |

### Lựa chọn 3: Tự xây dựng trên Supabase (Khuyến nghị)

Kết hợp ưu điểm miễn phí của Supabase với sự linh hoạt tự kiểm soát:

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
│  │  ├── licenses (key, tier, features) │    │
│  │  └── activations (machine_id, ...)  │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Edge Functions (Serverless)        │    │
│  │  POST /validate-license             │    │
│  │  POST /activate-license             │    │
│  │  POST /deactivate-license           │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Row Level Security (RLS)           │    │
│  │  Mỗi user chỉ thấy license của mình│    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### License Manager Pattern (Dependency Inversion)

```python
# shared/license/license_manager.py

class LicenseManager:
    """Quản lý bản quyền — kiểm tra local trước, online sau."""

    def __init__(self, backend: LicenseBackend, local_cache_path: str):
        self.backend = backend      # ← Interface, có thể là Supabase hoặc Keygen
        self.cache_path = local_cache_path
        self.OFFLINE_GRACE_DAYS = 7

    def validate(self, license_key: str) -> LicenseInfo:
        """
        1. Kiểm tra cache local trước (nhanh, không cần mạng)
        2. Nếu cache hết hạn → gọi backend kiểm tra online
        3. Nếu không có mạng → cho phép dùng nếu còn trong grace period
        """
        cached = self._check_local_cache()
        if cached and not cached.is_expired():
            return cached

        try:
            result = self.backend.validate_license(license_key)
            self._update_local_cache(result)
            return result
        except ConnectionError:
            if cached and cached.days_since_last_check < self.OFFLINE_GRACE_DAYS:
                return cached
            raise LicenseError("Cần kết nối internet để xác thực bản quyền")

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Kiểm tra feature có được bật cho tier hiện tại không."""
        license = self.validate(self._stored_key)
        return feature_name in license.features_enabled
```

### So sánh tổng hợp

| Tiêu chí | Supabase tự xây | Keygen.sh | Tự host hoàn toàn |
|---|---|---|---|
| **Chi phí khởi đầu** | ✅ $0 | ✅ $0 (100 licenses) | ❌ Cần VPS (~$5-10/tháng) |
| **Chi phí scale** | ✅ Free tier rất lớn | ⚠️ $49/tháng từ 101 licenses | ✅ Chỉ phí hosting |
| **Linh hoạt** | ✅ Toàn quyền thiết kế | ⚠️ Theo framework Keygen | ✅ Toàn quyền |
| **Offline support** | ✅ Tự thiết kế grace period | ✅ Có sẵn | ✅ Tự thiết kế |
| **Bảo trì** | ✅ Supabase lo server | ✅ Keygen lo server | ❌ Tự bảo trì mọi thứ |
| **Chống crack** | ⚠️ Trung bình | ✅ Tốt (machine fingerprint) | ⚠️ Tùy thiết kế |

> [!TIP]
> **Khuyến nghị:** Dùng Supabase làm license server ban đầu. Keygen.sh là backup plan nếu cần anti-piracy mạnh hơn.
>
> Feature tiers cụ thể (Free/Pro/Enterprise features) được định nghĩa trong **Product Configuration**.

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

*Kiến trúc tham chiếu cho lớp hệ thống Desktop AI Pipeline Application — áp dụng bất kể domain nghiệp vụ cụ thể.*
