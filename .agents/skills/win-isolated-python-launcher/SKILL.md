---
name: win-isolated-python-launcher
description: Khởi tạo môi trường ảo Python cô lập bằng uv và thiết lập tệp run.bat khởi chạy an toàn cho ứng dụng đồ họa trên Windows.
---

# Thiết Lập Môi Trường Python Cô Lập & Bộ Khởi Chạy Windows

Kỹ năng này hướng dẫn cách cô lập môi trường thực thi của một ứng dụng Python Desktop và đóng gói bộ chạy tự động `.bat` bền vững, an toàn trên nền tảng Windows.

---

## 1. Thiết Lập Môi Trường Ảo Cô Lập Với `uv`

Để đảm bảo tính độc lập và tránh xung đột với các phiên bản Python cài sẵn trên hệ thống của người dùng cuối, chúng ta xây dựng môi trường ảo cục bộ `.venv` ngay tại thư mục gốc của repository.

### Quy trình khởi tạo:
1.  **Kiểm tra công cụ `uv`:**
    Chạy lệnh `uv --version`. Nếu chưa cài đặt, tự động chạy lệnh PowerShell sau để cài ngầm:
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
2.  **Khởi tạo virtual environment cục bộ:**
    Di chuyển vào thư mục gốc của repository và tạo thư mục `.venv`:
    ```bash
    uv venv
    ```
    *Lưu ý: Thư mục ảo sẽ mặc định sử dụng phiên bản Python phù hợp nhất có sẵn trên hệ thống.*
3.  **Cài đặt các gói thư viện phụ thuộc:**
    Nếu ứng dụng cần các thư viện bổ sung (như `tkinterdnd2` cho kéo thả giao diện), thực hiện cài đặt cục bộ vào `.venv`:
    ```bash
    uv pip install tkinterdnd2
    ```
    > [!IMPORTANT]
    > **Tránh cài đặt dạng Editable Package (`pip install -e .`):**
    > Đối với các ứng dụng Desktop độc lập chạy script trực tiếp (không phải thư viện phân phối dạng bánh xe wheel), tránh chạy cài đặt dự án dạng editable. Điều này giúp ngăn ngừa các lỗi phát sinh từ trình build cấu hình hệ thống (như Hatchling/PyInstaller) khi không tìm thấy tên module trùng khớp.
4.  **Cấu hình Git loại bỏ môi trường ảo:**
    Đảm bảo thư mục `.venv/` được liệt kê trong tệp `.gitignore` của dự án để tránh đẩy các tệp thực thi nhị phân lên kho mã nguồn.

---

## 2. Thiết Thiết Kế Bộ Khởi Chạy `run.bat` Chuẩn Windows

Tệp tin batch (`.bat`) là điểm chạm đơn giản nhất giúp người dùng cuối click đúp để mở app mà không cần biết các thao tác gõ dòng lệnh. Thiết kế tệp `run.bat` cần tuân thủ các tiêu chuẩn sau:

### Tiêu Chuẩn Thiết Kế Tệp `run.bat` Bền Vững:
1.  **Tự động chuyển vùng làm việc:**
    Sử dụng lệnh `cd /d "%~dp0"` ở đầu file để đảm bảo thư mục hoạt động luôn luôn là thư mục chứa tệp `run.bat` bất kể người dùng khởi chạy từ vị trí nào (ví dụ: click đúp từ Explorer hoặc gọi từ Cmd).
2.  **Kiểm tra sự tồn tại của môi trường ảo:**
    Trước khi gọi chạy, bắt buộc phải kiểm tra file thực thi `.venv\Scripts\python.exe` có tồn tại hay không. Nếu không, hướng dẫn người dùng cách khởi tạo.
3.  **Thực thi trực tiếp bằng Python ảo:**
    Gọi trực tiếp `".venv\Scripts\python.exe" app/main.py` để chạy ứng dụng trong môi trường cô lập tuyệt đối.

### ⚠️ BẪY CÚ PHÁP CMD CẦN TRÁNH (Parenthesis Syntax Bug):
Trong cú pháp lệnh của Windows Command Prompt (Cmd/Batch), khi bạn sử dụng các câu lệnh rẽ nhánh `if` có đóng mở ngoặc đơn dạng:
```batch
if not exist "file" (
    # Khối lệnh bên trong
)
```
Trình phân tích cú pháp Cmd sẽ quét tìm dấu đóng ngoặc đơn `)` để kết thúc khối `if`. 

> [!CAUTION]
> **CẢNH BÁO LỖI:**
> Nếu bên trong khối lệnh trên có câu lệnh `echo` chứa dấu đóng ngoặc đơn như `echo Lỗi (ở .venv) trong repo!`, Cmd sẽ hiểu nhầm dấu `)` này là kết thúc khối `if`, cắt đoạn mã và coi phần chữ còn lại `"trong repo!"` là một lệnh không hợp lệ, dẫn đến lỗi crash app: **`"trong was unexpected at this time"`**.

#### Cách khắc phục:
*   Tránh sử dụng dấu ngoặc đơn `()` trong các dòng `echo` nằm bên trong khối `if/else`.
*   Thay thế bằng ngoặc vuông `[...]` hoặc ngoặc nhọn `{...}` (ví dụ: `echo Khong tim thay [.venv]`).
*   Hoặc sử dụng ký tự escape đặc trưng của Cmd là dấu mũ `^` trước dấu ngoặc: `echo Lỗi ^(.venv^)` để báo cho Cmd bỏ qua.

---

## 3. Mẫu Thiết Kế `run.bat` Chuẩn Hóa

```batch
@echo off
title Ten Ung Dung Chay Python Co Lap

:: Chuyển thư mục hoạt động về nơi chứa file batch hiện tại
cd /d "%~dp0"

:: ── Kiểm tra môi trường ảo nội bộ ───────────────────────────
if not exist ".venv\Scripts\python.exe" (
    echo [!] ERROR: Khong tim thay moi truong Python ao [.venv] trong thu muc!
    echo     Vui long dung uv de khoi tao va cai dat cac dependencies:
    echo     uv venv
    echo     uv pip install <deps>
    echo.
    pause
    exit /b 1
)

echo [*] Dang khoi chay ung dung bang moi truong ao .venv...
echo.
".venv\Scripts\python.exe" app/main.py

echo.
echo [x] Ung dung da dong.
pause
```
