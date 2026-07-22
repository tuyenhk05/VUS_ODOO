# -*- coding: utf-8 -*-
{
    'name': 'VUS Student Management',
    'version': '17.0.1.0.0',
    'summary': 'Quản lý thông tin học viên VUS',
    'description': """
        Module kế thừa res.partner để quản lý học viên VUS.
        Hỗ trợ thêm các trường thông tin học viên và logic hiển thị trên form.
    """,
    'category': 'Sales/Members',
    'author': 'Senior Odoo Developer',
    'website': 'https://vus.edu.vn',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
    ],
    'data': [
        'security/vus_security.xml',
        'data/ir_sequence_data.xml',
        'data/student_demo_data.xml',
        'views/student_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
