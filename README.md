# Hệ thống Quản lý Đào tạo VUS (VUS ERP Custom Addons)

Bộ phân hệ mở rộng (Custom Addons) được phát triển trên nền tảng **Odoo 17.0** nhằm tối ưu hóa và số hóa toàn diện quy trình vận hành đào tạo, tuyển sinh, marketing, kế toán học phí và chăm sóc học viên cho hệ thống Anh Văn Hội Việt Mỹ (VUS).

---

## 📂 1. Cấu trúc và Chức năng các phân hệ

Dự án được module hóa thành các phân hệ độc lập, liên kết chặt chẽ qua các mối quan hệ nghiệp vụ:

1. **`vus_student`**: Quản lý thông tin học viên & giảng viên.
   - Kế thừa danh mục đối tác chuẩn `res.partner`.
   - Quản lý chi tiết vòng đời học viên thông qua các trạng thái: `Potential` (Tiềm năng), `Waiting` (Chờ xếp lớp), `Studying` (Đang học), `Reserved` (Bảo lưu), `Completed` (Hoàn thành).
   - Tối ưu hóa giao diện: Tạo menu **Nhân sự** riêng biệt gom nhóm Học viên và Giảng viên để dễ dàng truy xuất.
2. **`vus_course`**: Quản lý danh mục khóa học (`vus.course`).
   - Lưu trữ thông tin học phí gốc, cấp độ (Starter, Beginner, Intermediate, Advanced,...), số buổi học, thời lượng học.
   - **Nút thông minh (Smart Button)**: Xem nhanh số lượng lớp học đang mở thuộc khóa học và điều hướng nhanh sang danh sách lớp đó.
3. **`vus_class`**: Quản lý thông tin lớp học (`vus.class`).
   - Ghi nhận ngày khai giảng, phòng học, lịch học, giảng viên phụ trách, sĩ số tối đa.
   - **Nút thông minh (Smart Button)**: Xem sĩ số học viên thực tế và điều hướng nhanh sang danh sách học viên đang theo học.
4. **`vus_enrollment`**: Phân hệ ghi danh khóa học và liên kết kế toán tự động (`vus.enrollment`).
   - Tự động lấy thông tin học phí từ khóa học được cấu hình.
   - **Tích hợp Kế toán tự động**: Khi xác nhận phiếu ghi danh, hệ thống tự động tạo hóa đơn khách hàng (`out_invoice`) bên phân hệ Kế toán chuẩn của Odoo và liên kết trực tiếp trên phiếu ghi danh. Trạng thái phiếu tự động chuyển thành **Đã thanh toán** khi hóa đơn được thanh toán đầy đủ.
5. **`vus_attendance`**: Quản lý điểm danh học viên hàng loạt theo buổi học (`vus.attendance`).
   - Cung cấp giao diện điểm danh theo buổi (`vus.attendance.sheet`), cho phép tải nhanh danh sách học viên từ lớp học và điểm danh hàng loạt bằng 1-Click.
   - Lưu trữ lịch sử chuyên cần chi tiết của từng học viên trực tiếp trên phiếu ghi danh.
6. **`vus_marketing`**: Quản lý chiến dịch Marketing và theo dõi Leads (`vus.marketing.campaign`).
   - Theo dõi ngân sách chiến dịch, chi phí thực tế, chỉ tiêu Lead.
   - Kế thừa `crm.lead` để liên kết chiến dịch và nguồn (Facebook, Website, Sự kiện,...).
   - Tự động thống kê số lead thực tế, số lượng chuyển đổi thành công và tỷ lệ chuyển đổi học viên.
7. **`vus_placement_test`**: Quản lý lịch kiểm tra đầu vào và chấm điểm (`vus.placement.test`).
   - Ghi nhận điểm số 4 kỹ năng (Nghe, Nói, Đọc, Viết) và đề xuất khóa học phù hợp dựa trên tổng điểm.
   - Hỗ trợ nút hành động nhanh **Ghi danh (Enroll)** để tự động tạo phiếu ghi danh dựa trên đề xuất thi đầu vào.
8. **`vus_promotion`**: Quản lý Học bổng & Ưu đãi học phí (`vus.promotion`).
   - Định nghĩa mã giảm giá/học bổng (giảm theo % hoặc số tiền cố định VND).
   - Áp dụng kiểm tra điều kiện thời hạn sử dụng và số lượt dùng tối đa, tự động khấu trừ tiền học phí trên phiếu ghi danh.
9. **`vus_dashboard`**: Báo cáo phân tích KPI tuyển sinh.
   - Sử dụng mô hình SQL View `vus.recruitment.report` kết hợp dữ liệu từ CRM Lead, Thi đầu vào, Phiếu ghi danh và Hóa đơn kế toán.
   - Giao diện báo cáo Pivot và biểu đồ trực quan về doanh thu tuyển sinh, tỷ lệ chuyển đổi lead và hiệu quả marketing.
10. **`vus_education_management`**: Module đóng gói (Bundle).
    - Phụ thuộc và tự động kích hoạt cài đặt đồng bộ toàn bộ 9 module con ở trên.

---

## 🛠️ 2. Yêu cầu hệ thống trước khi cài đặt

Để chạy thành công dự án này, máy tính của bạn cần đáp ứng các điều kiện sau:

* **Odoo**: Phiên bản **Odoo 17.0** (Community hoặc Enterprise).
* **Python**: Phiên bản **3.10** trở lên.
* **Hệ quản trị CSDL**: **PostgreSQL** 12 trở lên.
* **Các module tiêu chuẩn của Odoo** (Cần được cài đặt sẵn trên Database của bạn):
  * `contacts` (Danh bạ)
  * `crm` (Quản lý khách hàng tiềm năng)
  * `account` (Kế toán chuẩn Odoo)
  * `mail` (Hệ thống thảo luận)

---

## 🚀 3. Hướng dẫn Cài đặt & Khởi chạy chi tiết

Khi tải (clone) dự án này về máy, bạn thực hiện theo các bước sau để cấu hình và chạy dự án:

### Bước 1: Cấu hình `addons_path` cho máy chủ Odoo

Bạn cần khai báo thư mục `custom_addons` vừa tải về vào tệp cấu hình của Odoo (`odoo.conf`) để Odoo có thể tìm thấy các module tùy chỉnh này.

1. Tìm tệp `odoo.conf` trên máy chủ của bạn (Thường nằm trong thư mục gốc cài đặt Odoo hoặc thư mục cấu hình `/etc/odoo/`).
2. Mở file và tìm dòng `addons_path`. Thêm đường dẫn tuyệt đối đến thư mục `custom_addons` vào cuối dòng, phân tách bằng dấu phẩy `,`.

*Ví dụ trên Windows:*
```ini
addons_path = C:\Program Files\Odoo 17.0.20260615\server\odoo\addons,C:\du-an-cua-ban\custom_addons
```

*Ví dụ trên Linux / Docker:*
```ini
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom_addons
```

---

### Bước 2: Khởi động lại dịch vụ Odoo

Mỗi khi thay đổi file cấu hình `odoo.conf` hoặc thêm module mới, bạn cần khởi động lại dịch vụ Odoo để cập nhật:

* **Trên Windows (Sử dụng PowerShell dưới quyền Administrator):**
  ```powershell
  Restart-Service -Name "odoo-server-17.0"
  ```
  *(Hoặc mở ứng dụng `Services` của Windows, tìm dịch vụ `odoo-server-17.0` và bấm **Restart**)*

* **Trên Linux:**
  ```bash
  sudo systemctl restart odoo
  ```

* **Trên Docker:**
  ```bash
  docker restart <ten_container_odoo>
  ```

---

### Bước 3: Cài đặt Module lên Database

#### Cách 1: Cài đặt trực tiếp từ giao diện Web (Khuyên dùng)
1. Đăng nhập vào giao diện Odoo bằng tài khoản Administrator.
2. Truy cập **Cài đặt** (Settings) -> Kích hoạt **Chế độ nhà phát triển** (Developer Mode).
3. Đi tới menu **Ứng dụng** (Apps).
4. Click vào nút **Cập nhật danh sách ứng dụng** (Update Apps List) trên thanh menu phụ và xác nhận cập nhật.
5. Tìm kiếm từ khóa `vus_education_management` trong ô tìm kiếm (Lưu ý: Tắt bộ lọc mặc định `Apps` nếu không tìm thấy).
6. Nhấn nút **Kích hoạt** (Activate/Install). Hệ thống sẽ tự động cài đặt module bundle này kèm theo toàn bộ 9 module con phụ thuộc.

#### Cách 2: Cài đặt nhanh qua Command Line Interface (CLI)
Bạn có thể cài đặt trực tiếp thông qua lệnh python khởi chạy odoo-bin (Chạy với quyền Admin hoặc User cấu hình):
```powershell
# Chạy lệnh mẫu (hãy điều chỉnh đường dẫn Python, odoo-bin và odoo.conf tương ứng trên máy của bạn)
& "C:\Đường_dẫn_đến_Python\python.exe" "C:\Đường_dẫn_đến_Odoo\odoo-bin" -c "C:\Đường_dẫn_đến_Odoo\odoo.conf" -d Tên_Database_Của_Bạn -i vus_education_management --stop-after-init
```

---

### Bước 4: Khởi tạo dữ liệu mẫu (Demo Data) để kiểm thử nhanh

Để phục vụ kiểm thử nhanh toàn bộ luồng nghiệp vụ mà không cần tạo thủ công hàng tá thông tin học viên, giảng viên, lớp học... dự án có tích hợp sẵn script nạp dữ liệu mẫu tại đường dẫn `custom_addons/scratch/generate_demo_data.py`.

#### ⚠️ QUAN TRỌNG: Cấu hình script trước khi chạy
Trước khi chạy script, hãy mở file `custom_addons/scratch/generate_demo_data.py` bằng trình soạn thảo mã nguồn và điều chỉnh 2 biến cấu hình ở đầu file (Dòng 6 và Dòng 10) sao cho trùng khớp với môi trường local của bạn:

```python
# Mở file scratch/generate_demo_data.py và chỉnh sửa:
config_file = r"C:\Đường_dẫn_thực_tế_đến_file\odoo.conf"
db_name = 'Tên_Database_Thực_tế_Của_Bạn'
```

#### Chạy script nạp dữ liệu mẫu:
Mở Terminal/PowerShell và thực thi lệnh sau:

* **Trên Windows:**
  ```powershell
  $env:PYTHONPATH="C:\Program Files\Odoo 17.0.20260615\server"; $env:PYTHONIOENCODING="utf-8"; & "C:\Program Files\Odoo 17.0.20260615\python\python.exe" "c:\Đường_dẫn_đến_thư_mục_chứa\custom_addons\scratch\generate_demo_data.py"
  ```
  *(Lưu ý: Thay đổi đường dẫn thư mục cài đặt Odoo và thư mục `custom_addons` trong lệnh trên cho đúng với thực tế máy của bạn).*

* **Trên Linux:**
  ```bash
  export PYTHONPATH="/usr/lib/python3/dist-packages/odoo"
  export PYTHONIOENCODING="utf-8"
  python3 /path/to/custom_addons/scratch/generate_demo_data.py
  ```

Sau khi script hoàn thành và báo `DỮ LIỆU MẪU ĐÃ ĐƯỢC TẠO THÀNH CÔNG!`, bạn đã có sẵn đầy đủ dữ liệu chạy thử.

---

## 📖 4. Hướng dẫn Luồng kiểm thử nghiệp vụ chính (End-to-End Flow)

Hãy thực hiện kiểm thử hệ thống theo trình tự nghiệp vụ chuẩn của một trung tâm Anh ngữ như sau:

```mermaid
graph TD
    A[CRM & Marketing Campaign] --> B[Placement Test - Thi Đầu Vào]
    B --> C[Recommended Course - Đề xuất khóa học]
    C --> D[Quick Enroll - Ghi danh nhanh]
    D --> E[Apply Promotion - Áp dụng ưu đãi]
    E --> F[Confirm & Auto Invoice - Xác nhận & Tạo Hóa đơn]
    F --> G[Payment & Auto Paid - Thanh toán hóa đơn]
    G --> H[Class Assignment & Capacity Check]
    H --> I[Attendance Sheet - Điểm danh theo buổi]
    G --> J[KPI Dashboard - Phân tích KPI Tuyển sinh]
```

### Bước 1: Quản lý Marketing & Chiến dịch
* Vào menu **Marketing** -> **Chiến dịch Marketing** -> Kiểm tra chiến dịch mẫu **Chiến dịch Tuyển sinh Hè 2026** (Trạng thái: *Đang chạy*).
* Truy cập **CRM**, kiểm tra các Leads mẫu đã được phân công nguồn tuyển sinh (Facebook, Website...) và tự động liên kết với chiến dịch này.

### Bước 2: Tổ chức Thi đầu vào & Chấm điểm
* Vào menu **Tuyển sinh & Đăng ký** -> **Kiểm tra đầu vào** -> Chọn lịch thi mẫu **Kiểm tra trình độ IELTS tháng 7**.
* Xem danh sách thí sinh làm bài và điểm số 4 kỹ năng (Nghe, Nói, Đọc, Viết). Click **Xác nhận điểm** để chuyển đổi trạng thái thí sinh sang *Chờ xếp lớp*.
* Nhấn nút **Ghi danh (icon người +)** ở cuối dòng điểm của thí sinh để chuyển hướng tự động tạo Phiếu ghi danh.

### Bước 3: Tạo Phiếu ghi danh & Áp dụng Ưu đãi
* Trên phiếu ghi danh nháp vừa tạo, chọn **Lớp học đăng ký** (ví dụ: *IELTS Foundation Class A*).
* Chọn **Chương trình ưu đãi/Học bổng** (ví dụ: mã *HE2026_10* - giảm 10% hoặc *SCHOLAR_1M* - giảm 1.000.000 VND).
* Hệ thống sẽ tự động tính toán số tiền được giảm giá và cập nhật tổng tiền học phí thực tế của học viên.

### Bước 4: Xác nhận Ghi danh & Liên kết Kế toán
* Click **Xác nhận & Tạo hóa đơn**. Phiếu ghi danh chuyển sang trạng thái *Chờ thanh toán*.
* Click vào liên kết hóa đơn màu xanh tại trường **Hóa đơn liên kết** để mở hóa đơn bán ra tương ứng bên phân hệ Kế toán chuẩn Odoo.
* Tiến hành ghi nhận thanh toán hoàn tất cho hóa đơn này bên Kế toán. Quay lại phiếu ghi danh, bạn sẽ thấy trạng thái đã tự động đổi sang **Đã thanh toán** nhờ cơ chế đồng bộ tự động.

### Bước 5: Kiểm soát Sĩ số Lớp học
* Mở lớp học *IELTS Intensive Class A* (sĩ số tối đa quy định là 10). Nếu lớp đã đủ 10 học viên đã thanh toán, hãy thử tạo thêm một phiếu ghi danh mới vào lớp này và nhấn xác nhận. Hệ thống sẽ chặn lại và đưa ra thông báo cảnh báo lớp đã đầy để tránh quá tải sĩ số.

### Bước 6: Điểm danh Lớp học hàng loạt
* Vào menu **Điểm danh** -> **Điểm danh theo buổi** -> Nhấn **Tạo mới**.
* Chọn **Lớp học** (ví dụ: *IELTS Foundation Class A*), nhập **Buổi học** (ví dụ: *Buổi 1*).
* Nhấn nút **Tải danh sách học viên** để tự động nạp toàn bộ học viên đang học trong lớp với trạng thái mặc định là "Có mặt".
* Chỉnh sửa trạng thái cho học viên vắng/trễ/phép nếu cần và nhấn **Xác nhận điểm danh** để chốt chuyên cần. Lịch sử điểm danh sẽ hiển thị trên tab **Điểm danh** của từng Phiếu ghi danh học viên.

### Bước 7: Xem Báo cáo KPI & Dashboard tuyển sinh
* Truy cập menu **Báo cáo KPI**.
* Theo dõi các chỉ số trực quan dưới dạng biểu đồ hoặc bảng phân tích Pivot: tổng doanh thu học phí thu được, tỷ lệ chuyển đổi từ Lead sang Học viên thực tế và hiệu quả doanh thu mang lại của từng Chiến dịch Marketing.

---

## 🛠️ 5. Hướng dẫn xử lý sự cố thường gặp (Troubleshooting)

| Vấn đề | Nguyên nhân phổ biến | Cách khắc phục |
| :--- | :--- | :--- |
| **Không tìm thấy module custom trong danh sách ứng dụng** | Sai đường dẫn `addons_path` trong file `odoo.conf` hoặc chưa kích hoạt chế độ Developer Mode để "Cập nhật ứng dụng". | Kiểm tra kỹ đường dẫn trong `odoo.conf`. Đảm bảo khởi động lại dịch vụ Odoo trước khi nhấn nút "Cập nhật danh sách ứng dụng". |
| **Lỗi thiếu module dependency (`account`, `crm`...)** | Database hiện tại của bạn là database trống chưa được cài các ứng dụng cốt lõi của Odoo. | Hãy vào menu **Ứng dụng** (Apps) cài đặt trước các module **CRM**, **Invoicing / Accounting**, **Contacts** trước khi cài đặt `vus_education_management`. |
| **Lỗi chạy script `generate_demo_data.py`** | Sai đường dẫn tệp `config_file` hoặc sai tên `db_name` cấu hình ở dòng 6 & 10 của script. | Mở file script và sửa chính xác đường dẫn đến file `odoo.conf` trên máy của bạn và tên cơ sở dữ liệu (Database) đang dùng. |
| **Lỗi Encoding khi chạy script trên PowerShell** | PowerShell mặc định sử dụng encoding ASCII/ANSI nên bị lỗi ký tự Tiếng Việt. | Hãy chạy lệnh thiết lập `$env:PYTHONIOENCODING="utf-8"` trước khi gọi lệnh chạy script Python (như hướng dẫn ở Bước 4). |
| **Không tự động sinh được hóa đơn khi bấm xác nhận Ghi danh** | Do hệ thống kế toán của Odoo trên Database chưa được thiết lập Sổ nhật ký bán hàng (Sale Journal) mặc định. | Truy cập **Kế toán** -> **Cấu hình** -> Thiết lập ít nhất một Sổ nhật ký loại "Bán hàng" (Sale Journal). |

---
*Chúc bạn cài đặt và trải nghiệm hệ thống thành công! Nếu gặp bất kỳ khó khăn nào trong quá trình cài đặt, vui lòng liên hệ nhóm phát triển dự án.*
