# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VusEnrollment(models.Model):
    _inherit = 'vus.enrollment'

    promotion_id = fields.Many2one(
        'vus.promotion', 
        string='Chương trình ưu đãi/Học bổng',
        domain="[('active', '=', True)]"
    )
    discount_amount = fields.Float(
        string='Số tiền được giảm',
        compute='_compute_discount_amount',
        store=True,
        default=0.0
    )

    @api.depends('course_id', 'promotion_id')
    def _compute_discount_amount(self):
        for record in self:
            discount = 0.0
            if record.course_id and record.promotion_id:
                promo = record.promotion_id
                base_price = record.course_id.base_price
                if promo.type == 'percent':
                    discount = base_price * (promo.value / 100.0)
                elif promo.type == 'fixed':
                    discount = promo.value
                
                # Cắt giảm tối đa bằng học phí gốc
                if discount > base_price:
                    discount = base_price
            record.discount_amount = discount

    @api.depends('course_id', 'discount_amount')
    def _compute_amount(self):
        for record in self:
            base_price = record.course_id.base_price if record.course_id else 0.0
            # Khấu trừ số tiền giảm giá
            record.amount = max(0.0, base_price - record.discount_amount)

    @api.constrains('promotion_id')
    def _check_promotion_validity(self):
        for record in self:
            if record.promotion_id:
                promo = record.promotion_id
                today = fields.Date.today()
                
                # 1. Kiểm tra thời hạn hiệu lực
                if promo.start_date and today < promo.start_date:
                    raise ValidationError(f"Mã ưu đãi '{promo.code}' chưa có hiệu lực (Bắt đầu từ {promo.start_date})!")
                if promo.end_date and today > promo.end_date:
                    raise ValidationError(f"Mã ưu đãi '{promo.code}' đã hết hạn sử dụng (Hết hạn ngày {promo.end_date})!")
                
                # 2. Kiểm tra số lượt sử dụng tối đa
                if promo.max_uses > 0:
                    other_uses = self.env['vus.enrollment'].search_count([
                        ('promotion_id', '=', promo.id),
                        ('id', '!=', record.id),
                        ('state', 'in', ['confirmed', 'paid'])
                    ])
                    if other_uses >= promo.max_uses:
                        raise ValidationError(f"Mã ưu đãi '{promo.code}' đã đạt giới hạn lượt sử dụng tối đa ({promo.max_uses} lượt)!")
