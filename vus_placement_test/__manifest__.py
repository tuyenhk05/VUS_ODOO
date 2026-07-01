# -*- coding: utf-8 -*-
{
    'name': 'VUS Placement Test Management',
    'version': '17.0.1.0.0',
    'summary': 'Quản lý lịch thi và kết quả kiểm tra đầu vào VUS',
    'category': 'Sales',
    'author': 'Nhóm đồ án VUS',
    'depends': ['vus_student', 'vus_course', 'crm', 'vus_enrollment'],
    'data': [
        'security/ir.model.access.csv',
        'views/placement_test_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
