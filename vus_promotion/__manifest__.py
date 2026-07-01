# -*- coding: utf-8 -*-
{
    'name': 'VUS Scholarship & Promotion Management',
    'version': '17.0.1.0.0',
    'summary': 'Quản lý học bổng, ưu đãi và khuyến mãi VUS',
    'category': 'Sales',
    'author': 'Nhóm đồ án VUS',
    'depends': ['vus_enrollment'],
    'data': [
        'security/ir.model.access.csv',
        'views/promotion_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
