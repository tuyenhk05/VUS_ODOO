# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VusClass(models.Model):
    _name = 'vus.class'
    _description = 'Lớp học tại VUS'
    _rec_name = 'class_name'
    _order = 'start_date desc'

    class_name = fields.Char(string='Tên lớp', required=True)
    class_code = fields.Char(string='Mã lớp', required=True, copy=False)
    
    course_id = fields.Many2one('vus.course', string='Khóa học', required=True)
    course_level = fields.Selection(related='course_id.level', string='Trình độ', store=True)
    
    teacher_id = fields.Many2one(
        'res.partner',
        string='Giảng viên',
        domain=[('is_teacher', '=', True)],
        help='Chỉ chọn những người đã được đánh dấu là Giảng viên'
    )
    teacher_name = fields.Char(related='teacher_id.name', string='Tên giảng viên', store=True)
    
    schedule = fields.Char(string='Lịch học', help='VD: 18:30 - 20:30 Thứ 3,5,7')
    start_date = fields.Date(string='Ngày khai giảng', required=True)
    end_date = fields.Date(string='Ngày kết thúc')
    classroom = fields.Char(string='Phòng học')
    
    max_students = fields.Integer(string='Sĩ số tối đa', default=20, required=True)
    state = fields.Selection([
        ('draft', 'Chờ mở'),
        ('opened', 'Đang mở'),
        ('full', 'Đã đầy'),
        ('closed', 'Đã kết thúc')
    ], string='Trạng thái', default='draft', required=True)


    def action_open_class(self):
        self.state = 'opened'

    def action_close_class(self):
        self.state = 'closed'

    def action_duplicate_class(self):
        for rec in self:
            rec.copy({
                'class_name': rec.class_name + ' (Copy)',
                'class_code': rec.class_code + '_COPY',
                'state': 'draft',
            })

    @api.constrains('max_students')
    def _check_max_students(self):
        for rec in self:
            if rec.max_students < 0:
                raise ValidationError('Sĩ số tối đa không thể âm!')

    @api.constrains('class_code')
    def _check_unique_class_code(self):
        for rec in self:
            existing = self.search([('class_code', '=', rec.class_code), ('id', '!=', rec.id)])
            if existing:
                raise ValidationError(f'Mã lớp "{rec.class_code}" đã tồn tại!')

class VusCourseInherit(models.Model):
    _inherit = 'vus.course'

    class_ids = fields.One2many('vus.class', 'course_id', string='Các lớp học')
    class_count = fields.Integer(string='Số lớp', compute='_compute_class_count', store=True)

    @api.depends('class_ids')
    def _compute_class_count(self):
        for rec in self:
            rec.class_count = len(rec.class_ids)
