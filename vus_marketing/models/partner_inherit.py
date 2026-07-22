# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    marketing_audience_ids = fields.Many2many(
        'vus.marketing.audience',
        string='Đối tượng hướng đến (Phân loại Marketing)',
        help='Phân loại đối tượng khách hàng / học viên để phục vụ chiến dịch Marketing'
    )
