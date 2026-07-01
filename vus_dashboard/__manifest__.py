# -*- coding: utf-8 -*-
{
    'name': 'VUS Recruitment & Marketing Dashboard',
    'version': '17.0.1.0.0',
    'summary': 'Báo cáo thống kê và phân tích KPI tuyển sinh VUS',
    'category': 'Reporting',
    'author': 'Nhóm đồ án VUS',
    'depends': ['vus_enrollment', 'vus_placement_test', 'vus_marketing'],
    'data': [
        'security/ir.model.access.csv',
        'report/recruitment_report_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
