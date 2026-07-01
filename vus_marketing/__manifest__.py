# -*- coding: utf-8 -*-
{
    'name': 'VUS Marketing Campaign Management',
    'version': '17.0.1.0.0',
    'summary': 'Quản lý chiến dịch Marketing tùy chỉnh của VUS',
    'category': 'Marketing',
    'author': 'Nhóm đồ án VUS',
    'depends': ['crm', 'vus_student'],
    'data': [
        'security/ir.model.access.csv',
        'views/marketing_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
