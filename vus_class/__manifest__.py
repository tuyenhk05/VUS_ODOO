# -*- coding: utf-8 -*-
{
    'name': 'VUS Class Management',
    'version': '17.0.1.0.0',
    'summary': 'Quản lý lớp học VUS',
    'description': """
        Module quản lý các lớp học, giảng viên và sĩ số tại VUS.
    """,
    'category': 'Education',
    'author': 'Nhóm đồ án VUS',
    'website': 'https://vus.edu.vn',
    'license': 'LGPL-3',
    'depends': ['base', 'vus_course', 'vus_student'],
    'data': [
        'security/vus_class_security.xml',
        'security/ir.model.access.csv',
        'views/class_view.xml',
        'views/class_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
