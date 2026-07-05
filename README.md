# Hệ thống Quản lý Đào tạo VUS (VUS ERP Custom Addons)

Kho chứa toàn bộ các phân hệ (custom modules) tùy biến dành cho hệ thống quản trị đào tạo, tuyển sinh và marketing của VUS trên nền tảng **Odoo 17.0**.

---

## 📂 1. Cấu trúc và Chức năng các phân hệ

Hệ thống được thiết kế hoàn toàn theo mô hình hướng đối tượng mô-đun hóa, bao gồm các phân hệ cốt lõi sau:

1. **`vus_student`**: Quản lý thông tin học viên & giảng viên.
   - Kế thừa danh mục đối tác `res.partner`.
   - Quản lý trạng thái học viên (`potential` - Tiềm năng, `waiting` - Chờ xếp lớp, `studying` - Đang học, `reserved` - Bảo lưu, `completed` - Hoàn thành).
   - Tách biệt hai menu **Học viên** và **Giảng viên** vào menu cha mới mang tên **Nhân sự** với mức ưu tiên cao (`sequence="5"`).
2. **`vus_course`**: Quản lý danh mục khóa học.
   - Định nghĩa model `vus.course`. Lưu học phí gốc, trình độ (Starter, Beginner, Intermediate, Advanced,...), số buổi, số giờ học của khóa học.
   - **Tối ưu hóa**: Thêm Nút thông minh **Lớp học** hiển thị tổng số lớp và điều hướng nhanh sang danh sách lớp thuộc khóa học.
3. **`vus_class`**: Quản lý thông tin lớp học.
   - Định nghĩa model `vus.class`. Lưu trữ thông tin ngày khai giảng, phòng học, giáo viên phụ trách, lịch học, sĩ số tối đa của lớp học.
   - **Tối ưu hóa**: Thêm Nút thông minh **Học viên** hiển thị sĩ số thực tế và điều hướng nhanh sang danh sách học viên đang theo học.
4. **`vus_enrollment`**: Phân hệ ghi danh khóa học và tích hợp kế toán tự động.
   - Định nghĩa phiếu ghi danh `vus.enrollment`. Tự động tính học phí từ khóa học.
   - **Tích hợp Kế toán**: Khi xác nhận phiếu ghi danh, hệ thống tự động tạo hóa đơn khách hàng (`out_invoice`) bên phân hệ Kế toán chuẩn của Odoo và liên kết trực tiếp trên phiếu ghi danh. Trạng thái phiếu tự động chuyển thành **Đã thanh toán** khi hóa đơn được thanh toán.
5. **`vus_attendance`**: Quản lý điểm danh học viên hàng loạt theo buổi học (Mới).
   - Định nghĩa bảng điểm danh theo buổi `vus.attendance.sheet` giúp điểm danh nhanh cả lớp chỉ bằng 1 Click.
   - Định nghĩa dòng điểm danh chi tiết `vus.attendance` liên kết với lớp và phiếu ghi danh của học viên. Tích hợp lịch sử điểm danh trực quan ngay trên tab thông tin của phiếu ghi danh.
6. **`vus_marketing`**: Quản lý chiến dịch Marketing tùy chỉnh hoàn toàn.
   - Định nghĩa model chiến dịch `vus.marketing.campaign` lưu trữ mã chiến dịch, chỉ tiêu lead, ngân sách, chi phí thực tế.
   - Kế thừa `crm.lead` để theo dõi nguồn khách hàng (Facebook, Website, Sự kiện,...), liên kết chiến dịch và nhật ký chăm sóc khách hàng.
   - Tự động thống kê số lead thực tế, số lượt chuyển đổi thành công và tỷ lệ chuyển đổi học viên.
7. **`vus_placement_test`**: Quản lý lịch kiểm tra đầu vào và chấm điểm.
   - Định nghĩa buổi kiểm tra `vus.placement.test` và kết quả thi chi tiết `vus.placement.test.line`.
   - Ghi nhận điểm 4 kỹ năng Nghe, Nói, Đọc, Viết, tính tổng điểm và đề xuất khóa học phù hợp.
   - Nút chức năng **Ghi danh** nhanh tự động tạo phiếu ghi danh dựa trên khóa học đề xuất.
8. **`vus_promotion`**: Quản lý Học bổng & Ưu đãi học phí.
   - Định nghĩa mã giảm giá/học bổng `vus.promotion` (giảm theo % hoặc số tiền cố định VND).
   - Tự động tính toán số tiền được giảm giá trên phiếu ghi danh học viên, đồng thời kiểm tra điều kiện thời hạn sử dụng và số lượt dùng tối đa.
9. **`vus_dashboard`**: Báo cáo phân tích KPI tuyển sinh.
   - Định nghĩa mô hình SQL View `vus.recruitment.report` kết nối dữ liệu từ Lead, Thi đầu vào, Phiếu ghi danh và Kế toán.
   - Cung cấp giao diện phân tích Pivot và Biểu đồ KPI trực quan về doanh thu tuyển sinh, tỷ lệ chuyển đổi Lead và hiệu quả của các chiến dịch Marketing.
10. **`vus_education_management`**: Module đóng gói (Bundle).
    - Phụ thuộc và tự động kích hoạt cài đặt đồng bộ toàn bộ các module con trên.

---

## 🛠️ 2. Yêu cầu hệ thống

* **Phiên bản Odoo**: Odoo 17.0 (Community hoặc Enterprise).
* **Python**: Phiên bản 3.10 trở lên.
* **Dependencies chuẩn**: `crm`, `account` (Kế toán), `contacts` (Danh bạ), `mail`.

---

## 🚀 3. Hướng dẫn cài đặt và Cài dữ liệu mẫu

### Bước 1: Cấu hình addons_path trong `odoo.conf`
Đảm bảo thư mục dự án đã được khai báo trong file cấu hình máy chủ Odoo:
```ini
addons_path = C:\Program Files\Odoo 17.0.20260615\server\odoo\addons,c:\Program Files\Odoo 17.0.20260615\server\custom_addons
```

### Bước 2: Nâng cấp và Cài đặt toàn bộ Module qua CLI
Chạy dòng lệnh PowerShell (dưới quyền Administrator) để cài đặt đồng bộ toàn bộ các module thông qua module bundle:
```powershell
& "C:\Program Files\Odoo 17.0.20260615\python\python.exe" "C:\Program Files\Odoo 17.0.20260615\server\odoo-bin" -c "C:\Program Files\Odoo 17.0.20260615\server\odoo.conf" -d Vus_odoo -i vus_education_management --stop-after-init
```

### Bước 3: Khởi động lại dịch vụ Odoo
```powershell
Restart-Service -Name "odoo-server-17.0"
```

### Bước 4: Tạo dữ liệu mẫu để chạy thử nghiệm
Để phục vụ việc kiểm thử nhanh toàn bộ luồng nghiệp vụ mà không cần nhập thủ công từ đầu, hãy chạy script nạp dữ liệu mẫu được tích hợp sẵn:
```powershell
$env:PYTHONPATH="C:\Program Files\Odoo 17.0.20260615\server"; $env:PYTHONIOENCODING="utf-8"; & "C:\Program Files\Odoo 17.0.20260615\python\python.exe" "c:\Program Files\Odoo 17.0.20260615\server\custom_addons\scratch\generate_demo_data.py"
```
*Lưu ý: Script trên sẽ tự động tạo Giảng viên, Học viên mẫu, Khóa học, Lớp học, Lịch thi đầu vào, Chiến dịch Marketing và Mã ưu đãi để bạn kiểm thử ngay lập tức.*

---

## 📖 4. Hướng dẫn Luồng hoạt động chính để kiểm thử

Để kiểm thử hệ thống từ đầu đến cuối, thực hiện theo các bước sau:

1. **Quản lý Marketing**:
   - Truy cập menu **Marketing** → **Chiến dịch Marketing** → Kiểm tra chiến dịch mẫu **Chiến dịch Tuyển sinh Hè 2026** (trạng thái *Đang chạy*).
   - Truy cập **CRM**, kiểm tra các Leads mẫu đã được phân công nguồn tuyển sinh và gán vào chiến dịch này.
2. **Kiểm tra đầu vào**:
   - Vào menu **Tuyển sinh & Đăng ký** → **Kiểm tra đầu vào** → Chọn lịch thi mẫu **Kiểm tra trình độ IELTS tháng 7**.
   - Xem bảng điểm của các thí sinh (ví dụ: Le Hoang C, Pham Minh D), nhấn nút **Xác nhận điểm** để chốt kết quả và đổi trạng thái thí sinh sang *Chờ xếp lớp*.
   - Nhấn nút **Ghi danh (icon người +)** ở cuối dòng điểm của thí sinh để tự động tạo Phiếu ghi danh.
3. **Ghi danh & Áp dụng Ưu đãi**:
   - Trên giao diện Phiếu ghi danh nháp mới mở ra, chọn **Lớp học đăng ký** (ví dụ: *IELTS Foundation Class A*).
   - Chọn **Chương trình ưu đãi/Học bổng** (ví dụ: *HE2026_10* - giảm 10%). Kiểm tra số tiền giảm giá và tổng tiền học phí phải nộp được khấu trừ tự động.
4. **Xác nhận & Sinh hóa đơn tự động**:
   - Click **Xác nhận & Tạo hóa đơn**.
   - Trạng thái phiếu ghi danh chuyển sang *Chờ thanh toán*.
   - Click vào link màu xanh tại trường **Hóa đơn liên kết** để mở hóa đơn bán ra bên phân hệ Kế toán. Khi hóa đơn được ghi nhận thanh toán hoàn tất, phiếu ghi danh sẽ tự động chuyển sang trạng thái *Đã thanh toán*.
5. **Điểm danh lớp học hàng loạt theo buổi (Mới)**:
   - Vào menu **Điểm danh** → **Điểm danh theo buổi** → Nhấn **Mới**.
   - Chọn **Lớp học** (ví dụ: *IELTS Foundation Class A*), nhập **Buổi học** (ví dụ: *Buổi 1*).
   - Nhấn **Tải danh sách học viên** để tự động nạp toàn bộ học viên đang học trong lớp với trạng thái mặc định "Có mặt".
   - Chỉnh sửa trạng thái cho học viên vắng/trễ/phép nếu cần và nhấn **Xác nhận điểm danh** để chốt chuyên cần. Lịch sử điểm danh sẽ hiển thị trên tab **Điểm danh** của từng Phiếu ghi danh của học viên.
6. **Sử dụng các Nút thông minh (Smart Buttons) điều hướng nhanh (Mới)**:
   - Mở form **Khóa học**, click nút **Lớp học** ở góc trên bên phải để xem nhanh danh sách lớp thuộc khóa học này.
   - Mở form **Lớp học**, click nút **Học viên** ở góc trên bên phải để xem nhanh danh sách học viên thuộc lớp học này.
7. **Kiểm soát sĩ số (Xếp lớp)**:
   - Mở lớp học *IELTS Intensive Class A* (sĩ số tối đa là 10). Nếu lớp đã đủ 10 học viên đã thanh toán, hãy thử tạo thêm một phiếu ghi danh mới vào lớp này và nhấn xác nhận. Hệ thống sẽ chặn lại và đưa ra thông báo cảnh báo lớp đã đầy.
8. **Báo cáo KPI**:
   - Truy cập menu **Báo cáo KPI** để theo dõi số lượng Lead, số lượt thi đầu vào, số lượt ghi danh thành công và tổng doanh thu dưới dạng biểu đồ hoặc bảng phân tích Pivot.
