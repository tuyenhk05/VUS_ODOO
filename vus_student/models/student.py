# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_student = fields.Boolean(
        string='Là học viên VUS',
        default=False,
        help="Đánh dấu đối tác này là học viên VUS"
    )
    is_teacher = fields.Boolean(
        string='Là giảng viên VUS',
        default=False,
        help="Đánh dấu đối tác này là giảng viên VUS"
    )
    student_code = fields.Char(
        string='Mã học viên',
        help="Nhập mã định danh học viên VUS"
    )
    dob = fields.Date(
        string='Ngày sinh',
        help="Ngày sinh của học viên"
    )
    student_status = fields.Selection([
        ('potential', 'Khách hàng tiềm năng'),
        ('waiting', 'Chờ xếp lớp'),
        ('studying', 'Đang học'),
        ('reserved', 'Bảo lưu'),
        ('completed', 'Đã hoàn thành')
    ], string='Trạng thái học viên', default='potential', help="Trạng thái hiện tại của học viên VUS")
