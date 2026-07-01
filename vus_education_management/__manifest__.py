{
    'name': 'VUS Education Management (Bundle)',
    'version': '1.0',
    'category': 'Education',
    'summary': 'Module tổng hợp quản lý đào tạo tại VUS',
    'description': """
        Module này đóng vai trò là module tổng hợp, tự động cài đặt các thành phần quản lý của VUS.
        Cấu trúc dự án hiện đã được module hóa hoàn toàn.
    """,
    'author': 'Nhóm đồ án VUS',
    'depends': [
        'base', 
        'crm', 
        'contacts', 
        'mail',
        'vus_student',
        'vus_course',
        'vus_class',
        'vus_attendance',
        'vus_enrollment',
        'vus_marketing',
        'vus_placement_test',
        'vus_promotion',
        'vus_dashboard',
    ],
    'data': [],
    'installable': True,
    'application': True,
}