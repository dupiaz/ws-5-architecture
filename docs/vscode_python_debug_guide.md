# 🚀 Hướng Dẫn Toàn Diện: Debug Python Trong VS Code (Dành Cho Người Mới)

Tài liệu này được biên soạn dựa trên kinh nghiệm thực chiến xử lý các lỗi thường gặp khi cấu hình môi trường Debug Python trong VS Code. Mục tiêu là giúp các học viên mới lập trình có thể hiểu sâu bản chất, tự tay cấu hình môi trường chuyên nghiệp (có thể chia sẻ qua GitHub) và làm chủ công cụ gỡ lỗi mạnh mẽ này.

---

## Phần 1: Tại sao phải Debug? (Tạm biệt lệnh `print`)

Khi mới học code, chúng ta thường có thói quen dùng lệnh `print("Chạy đến đây rồi")` hoặc `print(bien_x)` để xem chương trình bị lỗi ở đâu. Cách này thủ công, chậm chạp và khi code xong lại phải đi xóa từng dòng `print` cực kỳ mất thời gian.

**Debug (Gỡ lỗi)** là một tính năng siêu việt của VS Code cho phép bạn:
- Tạm dừng chương trình lại ở bất kỳ dòng code nào bạn muốn (đứng hình thời gian).
- Nhìn xuyên thấu bộ nhớ để xem giá trị của tất cả các biến tại thời điểm đó.
- Cho chương trình chạy chậm lại từng dòng một (Step-by-step) để theo dõi luồng đi của dữ liệu.

---

## Phần 2: Cấu hình Môi trường Debug "Chuẩn Chuyên Nghiệp" (Portable)

Nhiều người mới thường gặp lỗi **"The Python path in your debug configuration is invalid"** hoặc bấm F5 thì **Debug tắt phụt ngay lập tức**. 

Nguyên nhân thường do:
1. File cấu hình nhận diện sai thư mục gốc (Workspace Root).
2. Đường dẫn chứa dấu gạch chéo ngược (`\`) gây lỗi trên một số máy.
3. Cấu hình "chết" bằng đường dẫn tuyệt đối (VD: `C:\data\...`), làm cho người khác tải code về (Clone từ GitHub) không thể debug được.

### Giải pháp 2 Bước (Best Practice):
Chúng ta sẽ tách việc khai báo môi trường Python và việc khai báo chạy Debug ra làm 2 file riêng biệt bên trong thư mục `.vscode` ở thư mục gốc của dự án.

#### Bước 2.1: Tạo file `.vscode/settings.json`
Mục đích của file này là ép VS Code luôn luôn dùng môi trường ảo (`.venv`) của dự án thay vì Python cài chung trên máy tính. Bằng cách sử dụng biến `${workspaceFolder}`, cấu hình này sẽ tự động linh hoạt (portable) dù bạn copy dự án đi đâu.

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/repos/srt-translator-refactored/.venv/Scripts/python.exe"
}
```

#### Bước 2.2: Tạo file `.vscode/launch.json`
Đây là file quy định khi bấm F5 thì VS Code sẽ chạy file nào. Chú ý chúng ta sẽ **KHÔNG** khai báo lại đường dẫn python ở đây nữa (vì đã khai báo ở `settings.json` rồi), giúp tránh hoàn toàn lỗi Invalid Path.

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Debug SRT Translator",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/repos/srt-translator-refactored/app/main.py",
            "console": "integratedTerminal",
            "justMyCode": true,
            "cwd": "${workspaceFolder}/repos/srt-translator-refactored"
        }
    ]
}
```

> **🔥 Lưu ý quan trọng về "Single-Instance Lock":** 
> Nếu ứng dụng của bạn có cơ chế chặn mở nhiều cửa sổ cùng lúc, hãy đảm bảo bạn **ĐÃ TẮT** tất cả các cửa sổ app đang chạy ngầm trước khi bấm F5. Nếu không, app Debug bật lên sẽ phát hiện có app cũ đang chạy và tự động tắt ngay lập tức (lỗi Debug tắt phụt không báo trước).

---

## Phần 3: 3 Bước Bắt Đầu Một Phiên Debug

1. **Đặt Breakpoint (Điểm dừng):** Mở file Python bạn muốn kiểm tra (VD: `main.py`). Đưa chuột sang sát lề trái của số dòng và click chuột. Một chấm tròn đỏ 🔴 sẽ xuất hiện. Đây là vạch kẻ đường, báo cho hệ thống biết: *"Đến đây phải phanh lại!"*.
2. **Khởi động:** Nhấn phím **F5** (Hoặc qua tab Run & Debug bấm nút Play màu xanh lá).
3. **Đứng hình:** Chương trình sẽ chạy và dừng lại tại dòng có chấm đỏ. Dòng code đó sẽ được highlight màu vàng. Bây giờ thời gian đã bị ngưng đọng, nhường quyền kiểm soát cho bạn.

---

## Phần 4: Giải Mã Giao Diện Của "Bảng Điều Khiển" Debug

Khi hệ thống đã dừng lại ở chấm đỏ, hãy nhìn sang cột bên trái của VS Code. Đây là trung tâm phân tích của bạn, bao gồm 4 khu vực:

### 1. Variables (Các biến trong bộ nhớ)
Giúp bạn nhìn thấy mọi dữ liệu hiện có mà không cần lệnh `print`.
- **Locals (Cục bộ):** Các biến đang tồn tại bên trong cái hàm (function) mà bạn đang dừng lại.
- **Globals (Toàn cục):** Các biến dùng chung được khai báo ở đầu file.
*(Mẹo: Bạn có thể click đúp vào giá trị của biến ở đây để sửa sống nó luôn mà không cần viết lại code!)*

### 2. Watch (Theo dõi tập trung)
Khi bộ nhớ có hàng trăm biến, bạn sẽ rất hoa mắt. Hãy bấm dấu `+` ở khu vực Watch, gõ tên biến bạn quan tâm nhất vào. Nó sẽ luôn ghim biến đó ở đây để bạn tiện theo dõi sự biến đổi của nó qua từng dòng code.

### 3. Call Stack (Ngăn xếp/Dấu vết gọi hàm)
Trả lời cho câu hỏi: *"Làm thế quái nào chương trình lại đi lạc vào cái hàm này được nhỉ?"*
Nó hiển thị một danh sách từ dưới lên trên. Nhìn vào đó bạn sẽ biết: File A gọi hàm B, hàm B lại gọi tiếp hàm C. Bạn có thể click vào từng dòng trong danh sách để xem ngược lại tiến trình lịch sử.

### 4. Breakpoints (Quản lý điểm dừng)
Liệt kê tất cả các chấm đỏ bạn đã đặt trong toàn bộ dự án. Bạn có thể tạm thời vô hiệu hóa một chấm đỏ bằng cách bỏ dấu tích (✔) thay vì phải xóa nó đi.

---

## Phần 5: Thanh Điều Hướng Chạy Từng Dòng (Step-by-Step)

Khi ở chế độ Debug, một thanh công cụ nhỏ xíu sẽ trôi lơ lửng trên cùng màn hình. Đây là bánh lái để bạn điều khiển dòng thời gian:

*   ▶️ **F5 (Continue - Chạy tiếp):** Nhả phanh! Cho chương trình chạy tốc độ cao bình thường cho đến khi đụng phải một chấm đỏ (Breakpoint) khác mới dừng lại.
*   🔄 **F10 (Step Over - Đi qua):** Thực thi dòng code hiện tại và nhảy xuống dòng code bên dưới. **Nếu dòng đó là một hàm, nó sẽ chạy vèo qua hàm đó** mà không đi sâu vào bên trong xem hàm đó được viết như thế nào.
*   ⬇️ **F11 (Step Into - Đi sâu vào):** Giống F10, nhưng nếu gặp một hàm, nó sẽ **chui sâu vào tận bên trong** file chứa hàm đó để bạn soi từng ngóc ngách của hàm.
*   ⬆️ **Shift + F11 (Step Out - Thoát ra):** Bạn lỡ tay bấm F11 chui vào một hàm dài ngoằng và thấy chán? Bấm nút này để chạy vèo cho hết hàm đó và nhảy ra ngoài lại.
*   🔁 **Ctrl + Shift + F5 (Restart):** Bắt đầu phiên debug lại từ con số 0.
*   ⏹️ **Shift + F5 (Stop):** Ngắt cầu dao, tắt toàn bộ phiên Debug.

---
**Chúc bạn có những giờ phút Debug vui vẻ. Nắm vững kỹ năng này, bạn đã bước một chân vào thế giới của những Lập trình viên thực thụ!**
