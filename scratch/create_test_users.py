# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

# Cấu hình đường dẫn file config của Odoo 17.0.20260615
config_file = r"C:\Program Files\Odoo 17.0.20260615\server\odoo.conf"
odoo.tools.config.parse_config(['-c', config_file])

# Database của dự án
db_name = 'Vus_odoo'
registry = odoo.registry(db_name)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Lấy thông tin các nhóm quyền
    group_manager = env.ref('vus_student.group_vus_manager')
    group_staff = env.ref('vus_student.group_vus_staff')
    group_teacher = env.ref('vus_student.group_vus_teacher')
    group_internal = env.ref('base.group_user')
    
    print("Đang khởi tạo các tài khoản phân quyền kiểm thử...")

    # 2. Tạo hoặc Cập nhật tài khoản Quản lý (Manager)
    group_sale_manager = env.ref('sales_team.group_sale_manager')
    group_account_manager = env.ref('account.group_account_manager')
    manager_group_ids = [group_internal.id, group_manager.id, group_sale_manager.id, group_account_manager.id]

    manager_login = 'manager@vus.edu.vn'
    user_manager = env['res.users'].search([('login', '=', manager_login)], limit=1)
    if not user_manager:
        user_manager = env['res.users'].create({
            'name': 'VUS Manager',
            'login': manager_login,
            'password': 'admin',
            'groups_id': [(6, 0, manager_group_ids)]
        })
        print(f"--> Đã tạo tài khoản Quản lý: {manager_login} / mật khẩu: admin")
    else:
        user_manager.write({
            'groups_id': [(6, 0, manager_group_ids)]
        })
        print(f"--> Đã cập nhật tài khoản Quản lý: {manager_login}")

    # 3. Tạo hoặc Cập nhật tài khoản Giáo vụ / Tuyển sinh (Staff)
    group_sale_salesman = env.ref('sales_team.group_sale_salesman_all_leads')
    group_account_invoice = env.ref('account.group_account_invoice')
    group_account_user = env.ref('account.group_account_user')
    staff_group_ids = [group_internal.id, group_staff.id, group_sale_salesman.id, group_account_invoice.id, group_account_user.id]

    staff_login = 'staff@vus.edu.vn'
    user_staff = env['res.users'].search([('login', '=', staff_login)], limit=1)
    if not user_staff:
        user_staff = env['res.users'].create({
            'name': 'VUS Staff',
            'login': staff_login,
            'password': 'admin',
            'groups_id': [(6, 0, staff_group_ids)]
        })
        print(f"--> Đã tạo tài khoản Giáo vụ/Tuyển sinh: {staff_login} / mật khẩu: admin")
    else:
        user_staff.write({
            'groups_id': [(6, 0, staff_group_ids)]
        })
        print(f"--> Đã cập nhật tài khoản Giáo vụ/Tuyển sinh: {staff_login}")

    # 4. Tạo hoặc Cập nhật tài khoản Giảng viên (Teacher)
    teacher_login = 'teacher@vus.edu.vn'
    user_teacher = env['res.users'].search([('login', '=', teacher_login)], limit=1)
    if not user_teacher:
        user_teacher = env['res.users'].create({
            'name': 'Mr. John Smith',
            'login': teacher_login,
            'password': 'admin',
            'groups_id': [(6, 0, [group_internal.id, group_teacher.id])]
        })
        print(f"--> Đã tạo tài khoản Giáo viên: {teacher_login} / mật khẩu: admin")
    else:
        user_teacher.write({
            'groups_id': [(6, 0, [group_internal.id, group_teacher.id])]
        })
        print(f"--> Đã cập nhật tài khoản Giáo viên: {teacher_login}")

    # 5. Liên kết tài khoản Giáo viên với các dữ liệu lớp học mẫu để chạy Record Rule
    # Thiết lập Partner của user_teacher thành Giảng viên đứng lớp
    user_teacher_partner = user_teacher.partner_id
    user_teacher_partner.write({
        'is_teacher': True,
        'name': 'Mr. John Smith',
        'email': 'john.smith@vus.edu.vn'
    })
    print(f"--> Đã thiết lập Partner liên kết ({user_teacher_partner.name}) làm Giảng viên chính thức.")

    # Tìm các partner trùng tên 'Mr. John Smith' khác để gộp
    old_partners = env['res.partner'].search([
        ('name', '=', 'Mr. John Smith'),
        ('id', '!=', user_teacher_partner.id)
    ])
    for old_p in old_partners:
        # Cập nhật các bảng liên quan sang cho partner của user
        env['vus.class'].search([('teacher_id', '=', old_p.id)]).write({'teacher_id': user_teacher_partner.id})
        env['vus.teacher.registration'].search([('teacher_id', '=', old_p.id)]).write({'teacher_id': user_teacher_partner.id})
        env['vus.teacher.leave'].search([('teacher_id', '=', old_p.id)]).write({'teacher_id': user_teacher_partner.id})
        env['vus.class.session'].search([('teacher_id', '=', old_p.id)]).write({'teacher_id': user_teacher_partner.id})
        env['vus.attendance.sheet'].search([('teacher_id', '=', old_p.id)]).write({'teacher_id': user_teacher_partner.id})
        env['vus.attendance'].search([('teacher_id', '=', old_p.id)]).write({'teacher_id': user_teacher_partner.id})
        
        # Cập nhật các bảng khác như Placement Test nếu có
        if 'vus.placement.test' in env:
            env['vus.placement.test'].search([('teacher_id', '=', old_p.id)]).write({'teacher_id': user_teacher_partner.id})
        
        # Đổi tên và tắt cờ giảng viên để tránh trùng lặp
        old_p.write({
            'name': f"Mr. John Smith (Old - ID {old_p.id})",
            'is_teacher': False
        })
        print(f"--> Đã gộp dữ liệu và đổi tên partner trùng lặp: ID {old_p.id}")

    cr.commit()
    print("\nTẠO TÀI KHOẢN PHÂN QUYỀN HOÀN TẤT THÀNH CÔNG!")
