# -*- coding: utf-8 -*-
from odoo import models, fields, api

class VusAttendanceSheetInherit(models.Model):
    _inherit = 'vus.attendance.sheet'

    # Override lại teacher_id thành computed field để tự động nhận dạng Giáo viên dạy thay
    teacher_id = fields.Many2one(
        'res.partner',
        string='Giảng viên',
        compute='_compute_teacher_id',
        store=True,
        readonly=False
    )

    @api.depends('class_id', 'date')
    def _compute_teacher_id(self):
        for rec in self:
            # Tìm giáo viên dạy thay đã được duyệt cho lớp này vào đúng ngày này
            sub_line = self.env['vus.teacher.leave.line'].search([
                ('class_id', '=', rec.class_id.id),
                ('date', '=', rec.date),
                ('state', '=', 'substituted')
            ], limit=1)
            if sub_line and sub_line.substitute_teacher_id:
                rec.teacher_id = sub_line.substitute_teacher_id
            else:
                rec.teacher_id = rec.class_id.teacher_id if rec.class_id else False


class VusAttendanceInherit(models.Model):
    _inherit = 'vus.attendance'

    # Override lại teacher_id để liên kết trực tiếp với Giảng viên trên Bảng điểm danh
    # Thay vì lấy mặc định giáo viên chính của lớp học
    teacher_id = fields.Many2one(
        'res.partner',
        related='sheet_id.teacher_id',
        string='Giảng viên',
        store=True
    )
