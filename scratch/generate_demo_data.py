# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

# Cấu hình đường dẫn file config
config_file = r"C:\Program Files\Odoo 17.0.20260615\server\odoo.conf"
odoo.tools.config.parse_config(['-c', config_file])

# Khởi tạo registry Odoo cho database Vus_odoo
db_name = 'Vus_odoo'
registry = odoo.registry(db_name)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Tạo Giảng viên (res.partner)
    teacher_model = env['res.partner']
    teachers = []
    teacher_data = [
        {'name': 'Mr. John Smith', 'is_teacher': True, 'email': 'john.smith@vus.edu.vn'},
        {'name': 'Ms. Maria Nguyen', 'is_teacher': True, 'email': 'maria.nguyen@vus.edu.vn'},
        {'name': 'Mr. David Lee', 'is_teacher': True, 'email': 'david.lee@vus.edu.vn'}
    ]
    for data in teacher_data:
        existing = teacher_model.search([('name', '=', data['name'])], limit=1)
        if not existing:
            t = teacher_model.create(data)
            teachers.append(t)
            print(f"Tạo giảng viên: {t.name}")
        else:
            teachers.append(existing)
            print(f"Giảng viên đã tồn tại: {existing.name}")

    # 2. Tạo Khóa học (vus.course)
    course_model = env['vus.course']
    courses = []
    course_data = [
        {'course_name': 'IELTS Foundation', 'code': 'IELTS-FD', 'level': 'elementary', 'base_price': 4500000.0, 'state': 'confirmed'},
        {'course_name': 'IELTS Intensive', 'code': 'IELTS-IT', 'level': 'upper', 'base_price': 8000000.0, 'state': 'confirmed'},
        {'course_name': 'Super Minds 1', 'code': 'SM-1', 'level': 'starter', 'base_price': 3200000.0, 'state': 'confirmed'},
        {'course_name': 'Super Minds 2', 'code': 'SM-2', 'level': 'beginner', 'base_price': 3500000.0, 'state': 'confirmed'}
    ]
    for data in course_data:
        existing = course_model.search([('code', '=', data['code'])], limit=1)
        if not existing:
            c = course_model.create(data)
            courses.append(c)
            print(f"Tạo khóa học: {c.course_name}")
        else:
            courses.append(existing)
            print(f"Khóa học đã tồn tại: {existing.course_name}")

    # 3. Tạo Lớp học (vus.class)
    class_model = env['vus.class']
    classes = []
    import datetime
    start_date = datetime.date.today() + datetime.timedelta(days=7)
    class_data = [
        {'class_name': 'IELTS Foundation Class A', 'class_code': 'IELTS-FD-A', 'course_id': courses[0].id, 'teacher_id': teachers[0].id, 'schedule': '18:30 - 20:30 Thứ 2,4,6', 'start_date': start_date, 'max_students': 15, 'state': 'opened'},
        {'class_name': 'IELTS Intensive Class A', 'class_code': 'IELTS-IT-A', 'course_id': courses[1].id, 'teacher_id': teachers[1].id, 'schedule': '18:30 - 20:30 Thứ 3,5,7', 'start_date': start_date, 'max_students': 10, 'state': 'opened'},
        {'class_name': 'Super Minds 1 Class A', 'class_code': 'SM-1-A', 'course_id': courses[2].id, 'teacher_id': teachers[2].id, 'schedule': '17:00 - 18:30 Thứ 2,4', 'start_date': start_date, 'max_students': 12, 'state': 'opened'}
    ]
    for data in class_data:
        existing = class_model.search([('class_code', '=', data['class_code'])], limit=1)
        if not existing:
            cl = class_model.create(data)
            classes.append(cl)
            print(f"Tạo lớp học: {cl.class_name}")
        else:
            classes.append(existing)
            print(f"Lớp học đã tồn tại: {existing.class_name}")

    # 4. Tạo Học viên/Học viên tiềm năng (res.partner)
    student_model = env['res.partner']
    students = []
    student_data = [
        {'name': 'Nguyen Van A', 'is_student': True, 'student_code': 'VUS2026001', 'dob': '2005-05-15', 'student_status': 'studying'},
        {'name': 'Tran Thi B', 'is_student': True, 'student_code': 'VUS2026002', 'dob': '2006-11-20', 'student_status': 'waiting'},
        {'name': 'Le Hoang C', 'is_student': False, 'student_status': 'potential'},
        {'name': 'Pham Minh D', 'is_student': False, 'student_status': 'potential'},
        {'name': 'Vu Thu E', 'is_student': False, 'student_status': 'potential'}
    ]
    for data in student_data:
        existing = student_model.search([('name', '=', data['name'])], limit=1)
        if not existing:
            s = student_model.create(data)
            students.append(s)
            print(f"Tạo học viên: {s.name}")
        else:
            students.append(existing)
            print(f"Học viên đã tồn tại: {existing.name}")

    # 5. Tạo Chiến dịch Marketing (vus.marketing.campaign)
    campaign_model = env['vus.marketing.campaign']
    campaigns = []
    campaign_data = [
        {'name': 'Chiến dịch Tuyển sinh Hè 2026', 'code': 'VUS-HE-2026', 'budget': 50000000.0, 'actual_cost': 45000000.0, 'target_leads': 100, 'state': 'running', 'description': '<p>Chiến dịch quảng bá các lớp tiếng Anh thiếu nhi và luyện thi IELTS cho dịp hè.</p>'},
        {'name': 'Chiến dịch Thu 2026', 'code': 'VUS-THU-2026', 'budget': 30000000.0, 'actual_cost': 0.0, 'target_leads': 50, 'state': 'draft', 'description': '<p>Chiến dịch chuẩn bị cho mùa khai giảng tháng 9.</p>'}
    ]
    for data in campaign_data:
        existing = campaign_model.search([('code', '=', data['code'])], limit=1)
        if not existing:
            camp = campaign_model.create(data)
            campaigns.append(camp)
            print(f"Tạo chiến dịch: {camp.name}")
        else:
            campaigns.append(existing)
            print(f"Chiến dịch đã tồn tại: {existing.name}")

    # Tạo Leads crm liên kết chiến dịch
    lead_model = env['crm.lead']
    lead_data = [
        {'name': 'Tư vấn IELTS - Nguyen Van A', 'partner_id': students[0].id, 'vus_campaign_id': campaigns[0].id, 'lead_source': 'facebook', 'follow_up_notes': 'Học viên muốn học IELTS để đi du học. Đã thi thử.'},
        {'name': 'Tư vấn Tiếng Anh trẻ em - Le Hoang C', 'partner_id': students[2].id, 'vus_campaign_id': campaigns[0].id, 'lead_source': 'web', 'follow_up_notes': 'Phụ huynh quan tâm khóa Super Minds.'},
        {'name': 'Tư vấn IELTS - Pham Minh D', 'partner_id': students[3].id, 'vus_campaign_id': campaigns[0].id, 'lead_source': 'referral', 'follow_up_notes': 'Bạn của Nguyen Van A giới thiệu.'}
    ]
    for data in lead_data:
        existing = lead_model.search([('name', '=', data['name'])], limit=1)
        if not existing:
            lead = lead_model.create(data)
            print(f"Tạo Lead CRM: {lead.name}")
        else:
            print(f"Lead CRM đã tồn tại: {existing.name}")

    # 6. Tạo Lịch thi đầu vào và kết quả (vus.placement.test)
    test_model = env['vus.placement.test']
    test_line_model = env['vus.placement.test.line']
    
    test_datetime = datetime.datetime.now() + datetime.timedelta(days=1)
    existing_test = test_model.search([('name', '=', 'Kiểm tra trình độ IELTS tháng 7')], limit=1)
    if not existing_test:
        test = test_model.create({
            'name': 'Kiểm tra trình độ IELTS tháng 7',
            'date': test_datetime,
            'teacher_id': teachers[0].id,
            'classroom': 'Room 102',
            'max_participants': 10,
            'state': 'confirmed'
        })
        print(f"Tạo lịch thi: {test.name}")
        
        # Thêm kết quả thi
        test_line_model.create({
            'test_id': test.id,
            'partner_id': students[2].id, # Le Hoang C
            'listening_score': 65,
            'reading_score': 70,
            'writing_score': 55,
            'speaking_score': 60,
            'recommended_course_id': courses[0].id, # IELTS Foundation
            'state': 'graded'
        })
        test_line_model.create({
            'test_id': test.id,
            'partner_id': students[3].id, # Pham Minh D
            'listening_score': 85,
            'reading_score': 80,
            'writing_score': 75,
            'speaking_score': 80,
            'recommended_course_id': courses[1].id, # IELTS Intensive
            'state': 'graded'
        })
        print("Tạo dòng điểm thi đầu vào cho Le Hoang C và Pham Minh D")
    else:
        print(f"Lịch thi đã tồn tại: {existing_test.name}")

    # 7. Tạo Chương trình Ưu đãi (vus.promotion)
    promo_model = env['vus.promotion']
    promo_data = [
        {'name': 'Ưu đãi Tuyển sinh Hè 10%', 'code': 'HE2026_10', 'type': 'percent', 'value': 10.0, 'start_date': '2026-06-01', 'end_date': '2026-08-31', 'max_uses': 50, 'active': True},
        {'name': 'Học bổng Tiên Phong 1 Triệu', 'code': 'SCHOLAR_1M', 'type': 'fixed', 'value': 1000000.0, 'start_date': '2026-06-01', 'end_date': '2026-12-31', 'max_uses': 10, 'active': True}
    ]
    for data in promo_data:
        existing = promo_model.search([('code', '=', data['code'])], limit=1)
        if not existing:
            p = promo_model.create(data)
            print(f"Tạo chương trình ưu đãi: {p.name}")
        else:
            print(f"Ưu đãi đã tồn tại: {existing.name}")

    cr.commit()
    print("DỮ LIỆU MẪU ĐÃ ĐƯỢC TẠO THÀNH CÔNG!")
