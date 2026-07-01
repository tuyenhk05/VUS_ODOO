# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VusPromotion(models.Model):
    _name = 'vus.promotion'
    _description = 'Chương trình Ưu đãi & Học bổng VUS'
    _order = 'end_date desc, name'

    name = fields.Char(string='Tên ưu đãi/Học bổng', required=True)
    code = fields.Char(string='Mã ưu đãi', required=True, copy=False)
    
    type = fields.Selection([
        ('percent', 'Phần trăm (%)'),
        ('fixed', 'Số tiền cố định (VND)')
    ], string='Loại ưu đãi', default='percent', required=True)
    
    value = fields.Float(string='Giá trị giảm', required=True, default=0.0)
    
    start_date = fields.Date(string='Ngày bắt đầu')
    end_date = fields.Date(string='Ngày kết thúc')
    
    max_uses = fields.Integer(string='Lượt dùng tối đa', default=0, help='0 nghĩa là không giới hạn số lượt sử dụng')
    use_count = fields.Integer(string='Lượt dùng thực tế', compute='_compute_use_count')
    
    active = fields.Boolean(string='Đang hoạt động', default=True)
    description = fields.Text(string='Mô tả chi tiết')
    
    enrollment_ids = fields.One2many('vus.enrollment', 'promotion_id', string='Phiếu ghi danh sử dụng')

    @api.constrains('code')
    def _check_unique_code(self):
        for rec in self:
            existing = self.search([('code', '=', rec.code), ('id', '!=', rec.id)])
            if existing:
                raise ValidationError(f'Mã ưu đãi "{rec.code}" đã tồn tại!')

    @api.constrains('value', 'type')
    def _check_value(self):
        for rec in self:
            if rec.value < 0:
                raise ValidationError('Giá trị giảm không thể âm!')
            if rec.type == 'percent' and rec.value > 100:
                raise ValidationError('Phần trăm giảm tối đa là 100%!')

    def _compute_use_count(self):
        for rec in self:
            rec.use_count = self.env['vus.enrollment'].search_count([
                ('promotion_id', '=', rec.id),
                ('state', 'in', ['confirmed', 'paid'])
            ])
