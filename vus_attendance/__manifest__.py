# -*- coding: utf-8 -*-
{
    'name': 'VUS Attendance Management',
    'version': '17.0.1.0.0',
    'summary': 'Quản lý điểm danh VUS',
    'description': """
        Module quản lý việc điểm danh học viên trong các lớp học tại VUS.
    """,
    'category': 'Education',
    'author': 'Nhóm đồ án VUS',
    'website': 'https://vus.edu.vn',
    'license': 'LGPL-3',
    'depends': ['base', 'vus_class', 'vus_student', 'vus_enrollment'],
    'data': [
        'security/vus_attendance_security.xml',
        'security/ir.model.access.csv',
        'views/attendance_view.xml',
        'views/attendance_menu.xml',
        'views/enrollment_inheritance_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
