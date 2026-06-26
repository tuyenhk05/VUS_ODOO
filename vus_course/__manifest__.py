# -*- coding: utf-8 -*-
{
    'name': 'VUS Course Management',
    'version': '17.0.1.0.0',
    'summary': 'Quản lý khóa học VUS',
    'description': """
        Module quản lý các khóa học tại VUS.
    """,
    'category': 'Education',
    'author': 'Nhóm đồ án VUS',
    'website': 'https://vus.edu.vn',
    'license': 'LGPL-3',
    'depends': ['base', 'vus_student'],
    'data': [
        'security/ir.model.access.csv',
        'views/course_view.xml',
        'views/course_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
