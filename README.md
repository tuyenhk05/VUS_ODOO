# VUS Odoo 17 Custom Addons

Kho chứa các module tùy biến dành cho hệ thống quản lý học viên và ghi danh của VUS trên nền tảng Odoo 17.

## 📂 Cấu trúc thư mục

* **`vus_student`**: Phân hệ cốt lõi quản lý thông tin học viên VUS.
  * Kế thừa `res.partner`.
  * Thêm thuộc tính Là học viên VUS (`is_student`), Mã học viên (`student_code`), Ngày sinh (`dob`), và Trạng thái học viên (`student_status` - Khách hàng tiềm năng, Chờ xếp lớp, Đang học, Bảo lưu, Đã hoàn thành).
  * Tích hợp cơ chế ẩn hiện động các thông tin học viên chuẩn Odoo 17.
* **`vus_enrollment`**: Phân hệ ghi danh khóa học và tích hợp kế toán tự động.
  * Danh mục khóa học (`vus.course`) với học phí gốc.
  * Phiếu ghi danh (`vus.enrollment`) tự động tính toán học phí từ khóa học đăng ký.
  * Tự động sinh hóa đơn khách hàng bán ra (`out_invoice`) bên phân hệ Kế toán khi xác nhận ghi danh và liên kết trực tiếp trên giao diện phiếu ghi danh.

---

## 🛠️ Yêu cầu cài đặt

* **Hệ điều hành**: Windows / Linux / macOS.
* **Phiên bản Odoo**: Odoo 17.0 (Community hoặc Enterprise).
* **Dependencies**: Module `account` (Kế toán Odoo) và `contacts` (Danh bạ Odoo).

---

## 🚀 Hướng dẫn cài đặt và cấu hình

### Bước 1: Sao chép mã nguồn vào thư mục addons của Odoo
Sao chép cả hai thư mục `vus_student` và `vus_enrollment` vào thư mục `custom_addons` của bạn.

### Bước 2: Cấu hình tệp `odoo.conf`
Đảm bảo rằng đường dẫn `custom_addons` đã được khai báo trong file cấu hình `odoo.conf`:
```ini
addons_path = C:\Program Files\Odoo 17.0.20260615\server\odoo\addons,C:\Program Files\Odoo 17.0.20260615\server\custom_addons
```

### Bước 3: Khởi động lại dịch vụ Odoo
* **Trên Windows**: Mở **Services** -> Tìm `odoo-server-17.0` -> Click **Restart**.
* **Bằng dòng lệnh (CLI)**:
  ```powershell
  Restart-Service -Name "odoo-server-17.0"
  ```

### Bước 4: Kích hoạt module trong Odoo
1. Bật **Developer Mode** (Chế độ nhà phát triển) trên Odoo.
2. Truy cập ứng dụng **Apps** (Ứng dụng).
3. Nhấp vào nút **Update Apps List** (Cập nhật danh sách ứng dụng) -> Click **Update**.
4. Xóa bộ lọc `Apps` mặc định ở thanh tìm kiếm, tìm kiếm từ khóa `vus_`.
5. Bấm **Activate** để cài đặt cả hai module `vus_student` và `vus_enrollment`.

---

## 📖 Hướng dẫn sử dụng chi tiết

### 1. Đánh dấu Học viên VUS
1. Vào ứng dụng **Contacts (Danh bạ)** -> Nhấn **New**.
2. Tại ô **Tags** -> Bật gạt nút **"Là học viên VUS"**.
3. Nhập **Mã học viên**, **Ngày sinh** và lưu lại.

### 2. Thiết lập Khóa học
1. Vào ứng dụng **VUS** -> Chọn **Khóa học** -> Nhấn **New**.
2. Nhập thông tin Khóa học và **Học phí gốc** -> Lưu lại.

### 3. Ghi danh & Sinh hóa đơn tự động
1. Vào ứng dụng **VUS** -> Chọn **Phiếu ghi danh** -> Nhấn **New**.
2. Chọn **Học viên** đã tạo ở Bước 1 và **Khóa học** ở Bước 2.
3. Số tiền học phí sẽ tự động được điền. Nhấn lưu để ở trạng thái **Nháp**.
4. Nhấn nút **"Xác nhận & Tạo hóa đơn"** ở góc trái phía trên:
   - Trạng thái phiếu chuyển thành **Đã xác nhận**.
   - Một hóa đơn khách hàng (`out_invoice`) mới được tạo tự động bên Kế toán.
   - Click vào link màu xanh tại trường **Hóa đơn liên kết** để chuyển thẳng tới hóa đơn kế toán và đối soát.
