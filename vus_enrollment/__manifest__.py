# -*- coding: utf-8 -*-
{
    'name': 'VUS Enrollment & Accounting Integration',
    'version': '17.0.1.0.0',
    'summary': 'Quản lý ghi danh và liên kết hóa đơn tự động',
    'description': """
        Module hỗ trợ ghi danh khóa học tại VUS.
        Tự động sinh hóa đơn khách hàng (invoice) bên phân hệ Kế toán khi xác nhận.
    """,
    'category': 'Sales/Enrollment',
    'author': 'Senior Odoo Developer',
    'website': 'https://vus.edu.vn',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'vus_student',
        'vus_course',
        'vus_class',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/enrollment_view.xml',
        'views/enrollment_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
