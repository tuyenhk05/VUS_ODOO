# -*- coding: utf-8 -*-
{
    'name': 'VUS Student Portal',
    'version': '17.0.1.0.0',
    'summary': 'Trang web tích hợp dành cho Học viên VUS',
    'description': """
        Phân hệ cung cấp Cổng thông tin (Portal) dạng Single Page Application (SPA) dành cho học viên VUS.
        Học viên có thể tra cứu thông tin cá nhân, điểm danh, công nợ hóa đơn, đăng ký tư vấn và đăng ký lớp học trực tuyến.
    """,
    'category': 'Website',
    'author': 'Senior Odoo Developer',
    'website': 'https://vus.edu.vn',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'crm',
        'vus_student',
        'vus_course',
        'vus_class',
        'vus_enrollment',
        'vus_attendance',
    ],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
