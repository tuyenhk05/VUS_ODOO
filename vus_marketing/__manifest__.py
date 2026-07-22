# -*- coding: utf-8 -*-
{
    'name': 'VUS Marketing Campaign Management',
    'version': '17.0.1.0.0',
    'summary': 'Quản lý chiến dịch Marketing tùy chỉnh của VUS',
    'category': 'Marketing',
    'author': 'Nhóm đồ án VUS',
    'depends': ['crm', 'vus_student', 'vus_placement_test', 'mass_mailing'],
    'data': [
        'security/ir.model.access.csv',
        'data/marketing_data.xml',
        'views/marketing_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
