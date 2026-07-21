# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID, fields
import datetime
import csv
import os

config_file = r"C:\Program Files\Odoo 17.0.20260615\server\odoo.conf"
odoo.tools.config.parse_config(['-c', config_file])

db_name = 'Vus_odoo'
registry = odoo.registry(db_name)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    print("=========================================")
    print("1. DỌN DẸP TOÀN BỘ DỮ LIỆU MẪU CŨ")
    print("=========================================")
    
    # 1. Xóa các dòng điểm danh và bảng điểm danh
    env['vus.attendance'].search([]).unlink()
    env['vus.attendance.sheet'].search([]).unlink()
    print("✔ Đã xóa Điểm danh.")

    # 2. Xóa hoạt động Odoo (Activity) liên quan đến class sessions
    env['mail.activity'].search([('res_model', '=', 'vus.class.session')]).unlink()

    # 3. Xóa phiếu báo vắng và chi tiết dạy thay/bù
    env['vus.teacher.leave.line'].search([]).unlink()
    env['vus.teacher.leave'].search([]).unlink()
    print("✔ Đã xóa Báo vắng & Dạy bù.")

    # 4. Xóa các buổi học chi tiết
    env['vus.class.session'].search([]).unlink()
    print("✔ Đã xóa Buổi học chi tiết.")

    # 5. Xóa đăng ký ca dạy rảnh của giáo viên
    env['vus.teacher.registration'].search([]).unlink()
    print("✔ Đã xóa Đăng ký lịch rảnh giáo viên.")

    # 6. Xóa phiếu ghi danh học viên và các hóa đơn kế toán liên kết
    enrollments = env['vus.enrollment'].search([])
    invoices = enrollments.mapped('invoice_id')
    for inv in invoices:
        if inv.state == 'posted':
            inv.button_draft()
        inv.button_cancel()
    invoices.unlink()
    enrollments.unlink()
    print("✔ Đã xóa Phiếu ghi danh và Hóa đơn liên kết.")

    # 7. Xóa CRM Leads
    env['crm.lead'].search([]).unlink()
    print("✔ Đã xóa Leads CRM.")

    # 8. Xóa kết quả thi và các buổi thi thử xếp lớp
    env['vus.placement.test.line'].search([]).unlink()
    env['vus.placement.test'].search([]).unlink()
    print("✔ Đã xóa Điểm thi xếp lớp.")

    # 9. Xóa các lớp học
    env['vus.class'].search([]).unlink()
    print("✔ Đã xóa Lớp học.")

    # 10. Xóa các Chiến dịch Marketing
    env['vus.marketing.campaign'].search([]).unlink()
    env['vus.marketing.channel'].search([]).unlink()
    env['vus.marketing.audience'].search([]).unlink()
    print("✔ Đã xóa Chiến dịch Marketing, Kênh & Đối tượng.")

    # 11. Xóa các chương trình ưu đãi
    env['vus.promotion'].search([]).unlink()
    print("✔ Đã xóa Chương trình ưu đãi.")

    # 12. Xóa các partner học viên/giáo viên phụ (Giữ các partner liên kết với tài khoản hệ thống)
    user_partners = env['res.users'].search([]).mapped('partner_id')
    # Xóa học viên cũ (không phải user)
    students_to_delete = env['res.partner'].search([
        ('id', 'not in', user_partners.ids),
        '|', '|', ('is_student', '=', True), ('is_teacher', '=', True), ('student_status', '!=', False)
    ])
    # Thay vì xóa cứng gây lỗi ràng buộc Kế toán của Odoo, ta ẩn và vô hiệu hóa các đối tác học viên/giáo viên mẫu cũ
    students_to_delete.write({
        'is_student': False,
        'is_teacher': False,
        'student_status': False,
        'active': False
    })
    print("✔ Đã dọn dẹp (vô hiệu hóa & lưu trữ) các đối tác học viên/giáo viên mẫu cũ.")

    # 13. Xóa các khóa học
    env['vus.course'].search([]).unlink()
    print("✔ Đã xóa Khóa học.")

    # 14. Xóa các kỳ học
    env['vus.academic.term'].search([]).unlink()
    print("✔ Đã xóa Kỳ học.")

    # 15. Xóa ca học cũ
    env['vus.time.slot'].search([]).unlink()
    print("✔ Đã xóa Ca học cũ.")

    print("\n=========================================")
    print("2. TẠO DỮ LIỆU MẪU CHUẨN THỰC TẾ (ĐỘ BAO PHỦ 80%)")
    print("=========================================")

    # 2.1. Khởi tạo các Ca học (time slots) đa dạng
    slot_model = env['vus.time.slot']
    slot_data = [
        {'days_group': 'mwf', 'shift': 'ca1', 'start_time': 17.5, 'end_time': 19.0},     # T2-4-6 Ca 1 (17:30 - 19:00)
        {'days_group': 'mwf', 'shift': 'ca2', 'start_time': 19.25, 'end_time': 20.75},   # T2-4-6 Ca 2 (19:15 - 20:45)
        {'days_group': 'tts', 'shift': 'ca1', 'start_time': 17.5, 'end_time': 19.0},     # T3-5-7 Ca 1 (17:30 - 19:00)
        {'days_group': 'tts', 'shift': 'ca2', 'start_time': 19.25, 'end_time': 20.75},   # T3-5-7 Ca 2 (19:15 - 20:45)
        {'days_group': 'ss', 'shift': 'ca1', 'start_time': 8.0, 'end_time': 9.5},        # T7-CN Ca 1 (08:00 - 09:30)
        {'days_group': 'ss', 'shift': 'ca2', 'start_time': 9.75, 'end_time': 11.25},     # T7-CN Ca 2 (09:45 - 11:15)
        {'days_group': 'ss', 'shift': 'ca3', 'start_time': 14.0, 'end_time': 15.5},      # T7-CN Ca 3 (14:00 - 15:30)
        {'days_group': 'ss', 'shift': 'ca4', 'start_time': 15.75, 'end_time': 17.25}     # T7-CN Ca 4 (15:45 - 17:15)
    ]
    slots = {}
    for sd in slot_data:
        sl = slot_model.create(sd)
        slots[f"{sd['days_group']}_{sd['shift']}"] = sl
    print(f"✔ Đã tạo {len(slots)} Ca học học chuẩn.")

    # 2.2. Khởi tạo các Kỳ học (academic terms)
    term_model = env['vus.academic.term']
    term_summer = term_model.create({
        'name': 'Kỳ Hè 2026',
        'start_date': '2026-06-01',
        'end_date': '2026-08-31',
        'registration_deadline': '2026-05-25',
        'state': 'active'
    })
    term_autumn = term_model.create({
        'name': 'Kỳ Thu 2026',
        'start_date': '2026-09-01',
        'end_date': '2026-11-30',
        'registration_deadline': '2026-08-20',
        'state': 'registration'
    })
    term_winter = term_model.create({
        'name': 'Kỳ Đông 2026',
        'start_date': '2026-12-01',
        'end_date': '2027-02-28',
        'registration_deadline': '2026-11-20',
        'state': 'draft'
    })
    print("✔ Đã tạo 3 Kỳ học mẫu.")

    # 2.3. Khởi tạo các Khóa học (courses)
    course_model = env['vus.course']
    courses_data = [
        {'course_name': 'IELTS Foundation', 'code': 'IELTS-FD', 'level': 'intermediate', 'base_price': 4500000.0, 'duration_weeks': 8, 'sessions_per_week': 3, 'state': 'confirmed'},
        {'course_name': 'IELTS Academic', 'code': 'IELTS-AC', 'level': 'upper', 'base_price': 5500000.0, 'duration_weeks': 12, 'sessions_per_week': 3, 'state': 'confirmed'},
        {'course_name': 'IELTS Intensive', 'code': 'IELTS-IT', 'level': 'advanced', 'base_price': 7000000.0, 'duration_weeks': 12, 'sessions_per_week': 3, 'state': 'confirmed'},
        {'course_name': 'Super Minds 1', 'code': 'SM-01', 'level': 'starter', 'base_price': 3200000.0, 'duration_weeks': 10, 'sessions_per_week': 2, 'state': 'confirmed'},
        {'course_name': 'Super Minds 2', 'code': 'SM-02', 'level': 'starter', 'base_price': 3500000.0, 'duration_weeks': 10, 'sessions_per_week': 2, 'state': 'confirmed'},
        {'course_name': 'Super Minds 3', 'code': 'SM-03', 'level': 'beginner', 'base_price': 3800000.0, 'duration_weeks': 10, 'sessions_per_week': 2, 'state': 'confirmed'},
        {'course_name': 'English for Teens 1', 'code': 'ET-01', 'level': 'elementary', 'base_price': 4000000.0, 'duration_weeks': 12, 'sessions_per_week': 2, 'state': 'confirmed'},
        {'course_name': 'English for Communication', 'code': 'EC-01', 'level': 'elementary', 'base_price': 3000000.0, 'duration_weeks': 8, 'sessions_per_week': 2, 'state': 'confirmed'}
    ]
    courses = {}
    for cd in courses_data:
        c = course_model.create(cd)
        courses[cd['code']] = c
    print(f"✔ Đã tạo {len(courses)} Khóa học tuyển sinh.")

    # 2.4. Tìm/Cập nhật Giáo viên từ các tài khoản đăng nhập và tạo Giáo viên mới
    partner_model = env['res.partner']
    
    # Giáo viên chính Mr. John Smith gán với user teacher
    user_teacher = env['res.users'].search([('login', '=', 'teacher@vus.edu.vn')], limit=1)
    if user_teacher:
        teacher_john = user_teacher.partner_id
        teacher_john.write({'name': 'Thầy John Smith', 'is_teacher': True, 'email': 'teacher@vus.edu.vn'})
    else:
        teacher_john = partner_model.create({'name': 'Thầy John Smith', 'is_teacher': True, 'email': 'teacher@vus.edu.vn'})

    # Các giáo viên khác
    teacher_hong = partner_model.create({'name': 'Cô Lê Thị Hồng', 'is_teacher': True, 'email': 'lethihong@vus.edu.vn', 'phone': '0901112223'})
    teacher_nhan = partner_model.create({'name': 'Thầy Nguyễn Hữu Nhân', 'is_teacher': True, 'email': 'nguyenhuunhan@vus.edu.vn', 'phone': '0901112224'})
    teacher_lan = partner_model.create({'name': 'Cô Trần Thị Lan', 'is_teacher': True, 'email': 'tranthilan@vus.edu.vn', 'phone': '0901112225'})
    teacher_david = partner_model.create({'name': 'Thầy David Lee', 'is_teacher': True, 'email': 'davidlee@vus.edu.vn', 'phone': '0901112226'})
    
    teachers_list = [teacher_john, teacher_hong, teacher_nhan, teacher_lan, teacher_david]
    print(f"✔ Đã thiết lập {len(teachers_list)} Giảng viên chuyên môn.")

    # 2.5. Khởi tạo Đăng ký lịch dạy rảnh (để tránh lỗi Validation khi gán lớp học)
    reg_model = env['vus.teacher.registration']
    
    # Giáo viên đăng ký toàn bộ khung giờ để dễ xếp lớp mẫu
    all_slot_ids = [slot.id for slot in slots.values()]
    for term in [term_summer, term_autumn]:
        for teacher in teachers_list:
            reg_model.create({
                'term_id': term.id,
                'teacher_id': teacher.id,
                'time_slot_ids': [(6, 0, all_slot_ids)],
                'min_sessions': 12,
                'state': 'approved'
            })
    print("✔ Đã phê duyệt Đăng ký lịch rảnh dạy cho các Giảng viên.")

    # 2.5.5. Khởi tạo Kênh Marketing & Đối tượng mục tiêu
    channel_model = env['vus.marketing.channel']
    aud_model = env['vus.marketing.audience']
    
    chan_fb = channel_model.create({'name': 'Facebook Ads', 'code': 'FB'})
    chan_gg = channel_model.create({'name': 'Google Ads', 'code': 'GG'})
    chan_tt = channel_model.create({'name': 'TikTok Ads', 'code': 'TT'})
    chan_email = channel_model.create({'name': 'Email Marketing', 'code': 'EMAIL'})
    chan_event = channel_model.create({'name': 'Hội thảo / Sự kiện', 'code': 'EVENT'})
    
    aud_kids = aud_model.create({'name': 'Học sinh tiểu học (5-11 tuổi)', 'description': 'Khóa Super Minds'})
    aud_teens = aud_model.create({'name': 'Học sinh cấp 2-3 (11-15 tuổi)', 'description': 'Khóa English for Teens'})
    aud_ielts = aud_model.create({'name': 'Học sinh/Sinh viên luyện thi IELTS', 'description': 'Khóa IELTS'})
    aud_adults = aud_model.create({'name': 'Người đi làm', 'description': 'Khóa Tiếng Anh Giao Tiếp'})
    print("✔ Đã khởi tạo các Kênh Marketing & Đối tượng mục tiêu.")

    # 2.6. Khởi tạo các Chiến dịch Marketing
    campaign_model = env['vus.marketing.campaign']
    campaigns = [
        campaign_model.create({
            'name': 'Chiến dịch Tuyển sinh Hè 2026',
            'code': 'VUS-HE-2026',
            'budget': 50000000.0,
            'actual_cost': 45000000.0,
            'target_leads': 100,
            'state': 'running',
            'start_date': '2026-05-01',
            'end_date': '2026-08-31',
            'channel_ids': [(6, 0, [chan_fb.id, chan_gg.id])],
            'audience_ids': [(6, 0, [aud_kids.id, aud_teens.id, aud_ielts.id])],
            'description': '<p>Quảng cáo Facebook/Google thu hút học viên nhí và luyện thi IELTS dịp hè.</p>'
        }),
        campaign_model.create({
            'name': 'Chiến dịch Thu Khai Trường 2026',
            'code': 'VUS-THU-2026',
            'budget': 40000000.0,
            'actual_cost': 30000000.0,
            'target_leads': 80,
            'state': 'running',
            'start_date': '2026-08-01',
            'end_date': '2026-10-31',
            'channel_ids': [(6, 0, [chan_fb.id, chan_tt.id, chan_email.id])],
            'audience_ids': [(6, 0, [aud_kids.id, aud_teens.id])],
            'description': '<p>Sự kiện Back to School, tặng balo và học bổng tuyển sinh.</p>'
        }),
        campaign_model.create({
            'name': 'Hội thảo Luyện thi IELTS 8.0',
            'code': 'VUS-IELTS-2026',
            'budget': 20000000.0,
            'actual_cost': 18000000.0,
            'target_leads': 40,
            'state': 'completed',
            'start_date': '2026-04-10',
            'end_date': '2026-04-30',
            'channel_ids': [(6, 0, [chan_event.id, chan_email.id])],
            'audience_ids': [(6, 0, [aud_ielts.id])],
            'description': '<p>Hội thảo chia sẻ phương pháp học từ cựu học viên VUS.</p>'
        }),
        campaign_model.create({
            'name': 'Chiến dịch Tiếng Anh Giao Tiếp',
            'code': 'VUS-COMM-2026',
            'budget': 15000000.0,
            'actual_cost': 0.0,
            'target_leads': 30,
            'state': 'draft',
            'start_date': '2026-10-01',
            'end_date': '2026-12-31',
            'channel_ids': [(6, 0, [chan_fb.id, chan_gg.id])],
            'audience_ids': [(6, 0, [aud_adults.id])]
        })
    ]
    print(f"✔ Đã tạo {len(campaigns)} Chiến dịch Marketing với Kênh & Đối tượng liên kết.")

    # 2.7. Khởi tạo Lớp học (classes)
    class_model = env['vus.class']
    
    classes_data = [
        # Kỳ Hè 2026
        {
            'class_name': 'IELTS Foundation Class A',
            'class_code': 'IELTS-FD-A',
            'course_id': courses['IELTS-FD'].id,
            'term_id': term_summer.id,
            'time_slot_id': slots['mwf_ca1'].id,
            'start_date': '2026-06-01',
            'classroom': 'Phòng 101',
            'max_students': 20,
            'payment_deadline': '2026-05-30',
            'state': 'draft'
        },
        {
            'class_name': 'IELTS Foundation Class B',
            'class_code': 'IELTS-FD-B',
            'course_id': courses['IELTS-FD'].id,
            'term_id': term_summer.id,
            'time_slot_id': slots['tts_ca1'].id,
            'start_date': '2026-06-02',
            'classroom': 'Phòng 102',
            'max_students': 20,
            'payment_deadline': '2026-05-31',
            'state': 'draft'
        },
        {
            'class_name': 'IELTS Academic Class A',
            'class_code': 'IELTS-AC-A',
            'course_id': courses['IELTS-AC'].id,
            'term_id': term_summer.id,
            'time_slot_id': slots['mwf_ca2'].id,
            'start_date': '2026-06-01',
            'classroom': 'Phòng 103',
            'max_students': 20,
            'payment_deadline': '2026-05-30',
            'state': 'draft'
        },
        {
            'class_name': 'IELTS Academic Class B',
            'class_code': 'IELTS-AC-B',
            'course_id': courses['IELTS-AC'].id,
            'term_id': term_summer.id,
            'time_slot_id': slots['tts_ca2'].id,
            'start_date': '2026-06-02',
            'classroom': 'Phòng 104',
            'max_students': 20,
            'payment_deadline': '2026-05-31',
            'state': 'draft'
        },
        {
            'class_name': 'Super Minds 1 Class A',
            'class_code': 'SM1-A',
            'course_id': courses['SM-01'].id,
            'term_id': term_summer.id,
            'time_slot_id': slots['ss_ca1'].id,
            'start_date': '2026-06-06',
            'classroom': 'Phòng 105',
            'max_students': 15,
            'payment_deadline': '2026-06-05',
            'state': 'draft'
        },
        {
            'class_name': 'Super Minds 1 Class B',
            'class_code': 'SM1-B',
            'course_id': courses['SM-01'].id,
            'term_id': term_summer.id,
            'time_slot_id': slots['ss_ca2'].id,
            'start_date': '2026-06-06',
            'classroom': 'Phòng 106',
            'max_students': 15,
            'payment_deadline': '2026-06-05',
            'state': 'draft'
        },
        {
            'class_name': 'Super Minds 2 Class A',
            'class_code': 'SM2-A',
            'course_id': courses['SM-02'].id,
            'term_id': term_summer.id,
            'time_slot_id': slots['ss_ca3'].id,
            'start_date': '2026-06-06',
            'classroom': 'Phòng 107',
            'max_students': 15,
            'payment_deadline': '2026-06-05',
            'state': 'draft'
        },
        # Kỳ Thu 2026
        {
            'class_name': 'English for Teens Class A',
            'class_code': 'ET1-A',
            'course_id': courses['ET-01'].id,
            'term_id': term_autumn.id,
            'time_slot_id': slots['mwf_ca1'].id,
            'start_date': '2026-09-02',
            'classroom': 'Phòng 108',
            'max_students': 20,
            'payment_deadline': '2026-08-30',
            'state': 'draft'
        },
        {
            'class_name': 'English for Teens Class B',
            'class_code': 'ET1-B',
            'course_id': courses['ET-01'].id,
            'term_id': term_autumn.id,
            'time_slot_id': slots['tts_ca1'].id,
            'start_date': '2026-09-03',
            'classroom': 'Phòng 109',
            'max_students': 20,
            'payment_deadline': '2026-08-31',
            'state': 'draft'
        },
        {
            'class_name': 'English for Communication Class A',
            'class_code': 'EC1-A',
            'course_id': courses['EC-01'].id,
            'term_id': term_autumn.id,
            'time_slot_id': slots['mwf_ca2'].id,
            'start_date': '2026-09-02',
            'classroom': 'Phòng 110',
            'max_students': 20,
            'payment_deadline': '2026-08-30',
            'state': 'draft'
        }
    ]

    classes_dict = {}
    print("-> Tạo các Lớp học nháp, sau đó mở lớp (tự động sinh closing_date) và tự động xếp giáo viên tối ưu...")
    for c_vals in classes_data:
        c_rec = class_model.create(c_vals)
        c_rec.action_open_class() # Mở lớp và tạo chi tiết buổi học
        c_rec.action_assign_optimal_teacher() # Tự động phân bổ giáo viên đồng đều
        classes_dict[c_rec.class_code] = c_rec
        print(f"   ✔ Lớp '{c_rec.class_name}' -> Xếp Giảng viên: {c_rec.teacher_id.name} (Hạn đóng lớp: {c_rec.closing_date})")

    # 2.8. Khởi tạo danh sách Học viên với Tên thật và CRM Leads (Độ bao phủ lớn: 50 Học viên)
    student_names = [
        "Nguyễn Minh Anh", "Lê Hoàng Nam", "Trần Thị Mai", "Phạm Minh Trí", "Vũ Hoàng Nam",
        "Đặng Thu Thảo", "Ngô Gia Bảo", "Bùi Thị Hạnh", "Dương Minh Quốc", "Hoàng Thanh Lâm",
        "Phan Văn Huy", "Đỗ Thị Diễm", "Võ Văn Hậu", "Nguyễn Đình Trọng", "Trần Duy Mạnh",
        "Phạm Đức Huy", "Lương Xuân Trường", "Nguyễn Công Phượng", "Nguyễn Quang Hải", "Đoàn Văn Hậu",
        "Vũ Văn Thanh", "Nguyễn Phong Hồng Duy", "Trần Minh Vương", "Phan Văn Đức", "Phạm Tuấn Hải",
        "Nguyễn Tiến Linh", "Nguyễn Hoàng Đức", "Đỗ Hùng Dũng", "Quế Ngọc Hải", "Bùi Tiến Dũng",
        "Đặng Văn Lâm", "Trần Văn Hùng", "Phạm Thu Hà", "Lê Thị Thu", "Nguyễn Văn Toàn",
        "Trần Văn Kiên", "Lê Văn Xuân", "Phạm Tuấn Tài", "Nguyễn Thanh Bình", "Bùi Hoàng Việt Anh",
        "Nguyễn Hoàng Nam", "Lê Văn Đô", "Huỳnh Công Đến", "Nguyễn Văn Tùng", "Trần Văn Đạt",
        "Nguyễn Hữu Thắng", "Nhâm Mạnh Dũng", "Hồ Thanh Minh", "Lê Minh Bình", "Trần Danh Trung"
    ]
    
    # Tạo học viên
    students = []
    for idx, name in enumerate(student_names):
        if idx < 15:
            audience_val = [(6, 0, [aud_kids.id])]
        elif idx < 30:
            audience_val = [(6, 0, [aud_teens.id])]
        elif idx < 45:
            audience_val = [(6, 0, [aud_ielts.id])]
        else:
            audience_val = [(6, 0, [aud_adults.id])]
            
        std = partner_model.create({
            'name': name,
            'email': f"hocvien{idx+1}@gmail.com",
            'phone': f"0987{idx+1:06d}",
            'is_student': True,
            'student_status': 'potential',
            'is_company': False,
            'marketing_audience_ids': audience_val
        })
        students.append(std)
        
    print(f"✔ Đã tạo danh sách {len(students)} Học viên tiềm năng với tên tiếng Việt thật.")

    # Tạo Leads crm phân bổ cho các chiến dịch
    lead_model = env['crm.lead']
    leads = []
    
    # 20 Leads cho chiến dịch Hè (campaigns[0])
    for i in range(20):
        leads.append(lead_model.create({
            'name': f"Tư vấn khóa học Hè - {students[i].name}",
            'partner_id': students[i].id,
            'vus_campaign_id': campaigns[0].id,
            'lead_source': 'facebook' if i % 2 == 0 else 'web',
            'follow_up_notes': 'Quan tâm học phí khóa học dịp hè.'
        }))
        
    # 20 Leads cho chiến dịch Thu (campaigns[1])
    for i in range(20, 40):
        leads.append(lead_model.create({
            'name': f"Tư vấn khóa khai giảng - {students[i].name}",
            'partner_id': students[i].id,
            'vus_campaign_id': campaigns[1].id,
            'lead_source': 'direct' if i % 2 == 0 else 'referral',
            'follow_up_notes': 'Học viên muốn nhận ưu đãi tặng Balo Back to school.'
        }))
        
    # 10 Leads cho sự kiện IELTS Workshop (campaigns[2])
    for i in range(40, 50):
        leads.append(lead_model.create({
            'name': f"Tư vấn sau sự kiện IELTS - {students[i].name}",
            'partner_id': students[i].id,
            'vus_campaign_id': campaigns[2].id,
            'lead_source': 'event',
            'follow_up_notes': 'Lead đăng ký sau buổi hội thảo học thuật của VUS.'
        }))
        
    print(f"✔ Đã liên kết và tạo {len(leads)} Cơ hội kinh doanh (Leads CRM).")

    # 2.9. Tạo Phiếu ghi danh (Enrollment) và tự động ghi nhận doanh thu
    enrollment_model = env['vus.enrollment']
    
    distribution = [
        (classes_dict['IELTS-FD-A'], students[0:8]),
        (classes_dict['IELTS-FD-B'], students[8:14]),
        (classes_dict['IELTS-AC-A'], students[14:21]),
        (classes_dict['IELTS-AC-B'], students[21:26]),
        (classes_dict['SM1-A'], students[26:32]),
        (classes_dict['SM1-B'], students[32:36]),
        (classes_dict['SM2-A'], students[36:42]),
        (classes_dict['ET1-A'], students[42:47]),
        (classes_dict['ET1-B'], students[47:50]),
    ]
    
    # Tạo các phiếu ghi danh
    enrolls_list = []
    for cls, std_list in distribution:
        for idx, std in enumerate(std_list):
            target_state = 'paid' if idx % 4 != 0 else ('confirmed' if idx % 2 == 0 else 'draft')
            # Tạo phiếu ghi danh ở dạng draft để kích hoạt luồng thanh toán hóa đơn
            enr = enrollment_model.create({
                'student_id': std.id,
                'course_id': cls.course_id.id,
                'class_id': cls.id,
                'amount': cls.course_id.base_price,
                'state': 'draft'
            })
            enrolls_list.append(enr)
            
            # Xác nhận để tự động sinh hóa đơn (account.move)
            if target_state in ['confirmed', 'paid']:
                enr.action_confirm()
                
            # Thanh toán hóa đơn nếu trạng thái mong muốn là 'paid'
            if target_state == 'paid':
                invoice = enr.invoice_id
                if invoice:
                    payment_register = env['account.payment.register'].with_context(
                        active_model='account.move',
                        active_ids=invoice.ids
                    ).create({
                        'payment_date': fields.Date.today(),
                        'amount': invoice.amount_residual,
                    })
                    payment_register.action_create_payments()
                std.write({'is_student': True, 'student_status': 'studying'})
            
    print(f"✔ Đã tạo và xếp lớp thành công cho {len(enrolls_list)} Học viên.")

    # 2.10. Tạo các Buổi kiểm tra xếp lớp (Placement Tests) mẫu
    test_model = env['vus.placement.test']
    test_line_model = env['vus.placement.test.line']
    
    pt1 = test_model.create({
        'name': 'Buổi kiểm tra xếp lớp IELTS Tháng 5',
        'date': datetime.datetime.now() - datetime.timedelta(days=20),
        'teacher_id': teacher_john.id,
        'classroom': 'Room 101',
        'max_participants': 15,
        'state': 'completed'
    })
    
    test_line_model.create({'test_id': pt1.id, 'partner_id': students[14].id, 'listening_score': 65, 'reading_score': 70, 'writing_score': 60, 'speaking_score': 65, 'recommended_course_id': courses['IELTS-AC'].id, 'state': 'graded'})
    test_line_model.create({'test_id': pt1.id, 'partner_id': students[15].id, 'listening_score': 70, 'reading_score': 75, 'writing_score': 65, 'speaking_score': 70, 'recommended_course_id': courses['IELTS-AC'].id, 'state': 'graded'})
    test_line_model.create({'test_id': pt1.id, 'partner_id': students[16].id, 'listening_score': 80, 'reading_score': 80, 'writing_score': 75, 'speaking_score': 80, 'recommended_course_id': courses['IELTS-AC'].id, 'state': 'graded'})
    test_line_model.create({'test_id': pt1.id, 'partner_id': students[17].id, 'listening_score': 55, 'reading_score': 60, 'writing_score': 50, 'speaking_score': 55, 'recommended_course_id': courses['IELTS-FD'].id, 'state': 'graded'})
    
    print("✔ Đã tạo Lịch kiểm tra đầu vào và Bảng điểm thi xếp lớp mẫu.")

    # 2.11. Tạo Phiếu báo vắng & Dạy thay
    leave_model = env['vus.teacher.leave']
    
    sess = env['vus.class.session'].search([('class_id', '=', classes_dict['IELTS-FD-A'].id)], limit=1)
    if sess:
        leave_rec = leave_model.create({
            'teacher_id': sess.teacher_id.id,
            'leave_date': sess.date,
            'class_id': sess.class_id.id,
            'reason': 'Nghỉ ốm đột xuất',
            'state': 'draft'
        })
        leave_rec.action_submit()
        leave_rec.action_confirm()
        
        if leave_rec.affected_line_ids:
            affected_line = leave_rec.affected_line_ids[0]
            sub_teacher = env['res.partner'].search([('is_teacher', '=', True), ('id', '!=', sess.teacher_id.id)], limit=1)
            if sub_teacher:
                affected_line.write({'substitute_teacher_id': sub_teacher.id})
                affected_line.button_confirm_substitute()
                leave_rec.action_resolve()
        print("✔ Đã tạo và xử lý thành công 1 yêu cầu Báo vắng & Phân giảng viên dạy thay.")

    # 2.12. Tạo Odoo Activity mẫu cho Giảng viên ngày hôm nay
    env['vus.class.session']._cron_notify_today_classes()
    print("✔ Đã tạo Odoo Activity nhắc nhở đứng lớp ngày hôm nay cho giáo viên.")

    # 2.13. Tạo các đợt Email Marketing mẫu liên kết với các Chiến dịch VUS
    mailing_model = env['mailing.mailing']
    mailing_model.create({
        'subject': 'Đón Hè Rực Rỡ cùng Tiếng Anh IELTS VUS - Nhận ưu đãi 20%',
        'vus_campaign_id': campaigns[0].id,
        'state': 'done',
        'sent': 1200,
        'opened': 480,
        'clicked': 120,
        'bounced': 12,
        'failed': 0,
        'reply_to_mode': 'update',
        'mailing_type': 'mail'
    })
    mailing_model.create({
        'subject': 'Tặng Balo xinh xắn & Học bổng 2 Triệu cho bé yêu học tiếng Anh',
        'vus_campaign_id': campaigns[1].id,
        'state': 'done',
        'sent': 1500,
        'opened': 600,
        'clicked': 180,
        'bounced': 15,
        'failed': 0,
        'reply_to_mode': 'update',
        'mailing_type': 'mail'
    })
    print("✔ Đã khởi tạo dữ liệu mẫu Email Marketing.")

    # Lưu lại toàn bộ dữ liệu mẫu vừa tạo
    cr.commit()
    print("\n>>> TOÀN BỘ CƠ SỞ DỮ LIỆU ĐÃ ĐƯỢC RESET VÀ NẠP LẠI THÀNH CÔNG! <<<")

    print("\n=========================================")
    print("3. KẾT XUẤT CSDL RA FILE CSV (EXPORT DATA)")
    print("=========================================")

    # Hàm export model ra file CSV
    def export_to_csv(model_name, fields_list, file_name):
        export_dir = r"C:\Users\HUYNH KIM TUYEN\.gemini\antigravity-ide\brain\9d124192-e176-472b-92f2-9dee61557ff3\scratch\export_data"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            
        file_path = os.path.join(export_dir, file_name)
        records = env[model_name].search([])
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write Header
            writer.writerow(fields_list)
            # Write Data Rows
            for rec in records:
                row = []
                for field in fields_list:
                    val = getattr(rec, field)
                    # Định dạng các quan hệ Many2one / selection / dates
                    if hasattr(val, '_name'): # Quan hệ
                        val = val.display_name or ''
                    elif isinstance(val, list) or hasattr(val, 'ids'): # M2m / O2m
                        val = ', '.join(val.mapped('display_name'))
                    elif isinstance(val, datetime.date) or isinstance(val, datetime.datetime):
                        val = val.strftime('%Y-%m-%d %H:%M:%S') if isinstance(val, datetime.datetime) else val.strftime('%Y-%m-%d')
                    row.append(val)
                writer.writerow(row)
        print(f"✔ Đã kết xuất {model_name} ra tệp: {file_path}")

    # Xuất các tệp CSV quan trọng
    export_to_csv('vus.academic.term', ['name', 'start_date', 'end_date', 'registration_deadline', 'state'], 'terms.csv')
    export_to_csv('vus.time.slot', ['days_group', 'shift', 'start_time', 'end_time', 'name'], 'time_slots.csv')
    export_to_csv('vus.course', ['course_name', 'code', 'base_price', 'level', 'duration_weeks', 'state'], 'courses.csv')
    
    # Chỉ xuất các giảng viên ra teachers.csv
    teachers_records = env['res.partner'].search([('is_teacher', '=', True)])
    teachers_file = r"C:\Users\HUYNH KIM TUYEN\.gemini\antigravity-ide\brain\9d124192-e176-472b-92f2-9dee61557ff3\scratch\export_data\teachers.csv"
    with open(teachers_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'email', 'phone', 'is_teacher'])
        for t in teachers_records:
            writer.writerow([t.name, t.email or '', t.phone or '', t.is_teacher])
    print(f"✔ Đã kết xuất res.partner (teachers) ra tệp: {teachers_file}")

    # Chỉ xuất các học viên ra students.csv
    students_records = env['res.partner'].search([('is_student', '=', True)])
    students_file = r"C:\Users\HUYNH KIM TUYEN\.gemini\antigravity-ide\brain\9d124192-e176-472b-92f2-9dee61557ff3\scratch\export_data\students.csv"
    with open(students_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'student_code', 'email', 'phone', 'is_student', 'student_status'])
        for s in students_records:
            writer.writerow([s.name, s.student_code or '', s.email or '', s.phone or '', s.is_student, s.student_status])
    print(f"✔ Đã kết xuất res.partner (students) ra tệp: {students_file}")

    export_to_csv('vus.marketing.campaign', ['name', 'code', 'budget', 'actual_cost', 'lead_count', 'cost_per_lead', 'conversion_count', 'conversion_rate', 'total_revenue', 'roi', 'state'], 'campaigns.csv')
    export_to_csv('crm.lead', ['name', 'partner_id', 'vus_campaign_id', 'lead_source'], 'leads.csv')
    export_to_csv('vus.class', ['class_name', 'class_code', 'course_id', 'term_id', 'time_slot_id', 'teacher_id', 'classroom', 'max_students', 'payment_deadline', 'closing_date', 'state'], 'classes.csv')
    export_to_csv('vus.enrollment', ['name', 'student_id', 'course_id', 'class_id', 'amount', 'state'], 'enrollments.csv')

    print("\n>>> KẾT XUẤT TẤT CẢ FILE CSV DỮ LIỆU MẪU THÀNH CÔNG! <<<")
    print("Các tệp dữ liệu đã sẵn sàng trong thư mục custom_addons/scratch/export_data/")
    print("=========================================")
