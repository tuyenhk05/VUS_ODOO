# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VusCourse(models.Model):
    _name = 'vus.course'
    _description = 'Khóa học tại VUS'
    _rec_name = 'course_name'
    _order = 'level, course_name'

    course_name = fields.Char(string='Tên khóa học', required=True, translate=True)
    code = fields.Char(string='Mã khóa học', required=True, copy=False)
    
    level = fields.Selection([
        ('starter', 'Starter - Mới bắt đầu'),
        ('beginner', 'Beginner - Sơ cấp'),
        ('elementary', 'Elementary - Sơ trung cấp'),
        ('intermediate', 'Intermediate - Trung cấp'),
        ('upper', 'Upper Intermediate - Trung cao cấp'),
        ('advanced', 'Advanced - Cao cấp'),
    ], string='Trình độ', required=True)
    
    base_price = fields.Monetary(string='Học phí gốc', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    
    duration_weeks = fields.Integer(string='Số tuần đào tạo', default=12)
    sessions_per_week = fields.Integer(string='Buổi/tuần', default=2)
    hours_per_session = fields.Float(string='Giờ/buổi', default=2.0)
    
    description = fields.Html(string='Mô tả chương trình')

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đang áp dụng'),
        ('closed', 'Ngưng áp dụng')
    ], string='Trạng thái', default='draft', required=True)

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_close(self):
        for rec in self:
            rec.state = 'closed'

    def action_set_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_view_classes(self):
        self.ensure_one()
        return {
            'name': 'Danh sách lớp học',
            'type': 'ir.actions.act_window',
            'res_model': 'vus.class',
            'view_mode': 'tree,form',
            'domain': [('course_id', '=', self.id)],
            'context': {'default_course_id': self.id},
            'target': 'current',
        }

    @api.constrains('code')
    def _check_unique_code(self):
        for rec in self:
            existing = self.search([('code', '=', rec.code), ('id', '!=', rec.id)])
            if existing:
                raise ValidationError(f'Mã khóa học "{rec.code}" đã tồn tại!')
