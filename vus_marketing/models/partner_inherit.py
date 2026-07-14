# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    marketing_audience_ids = fields.Many2many(
        'vus.marketing.audience',
        string='Phân loại đối tượng',
        help='Phân loại đối tượng để gửi Email Marketing hướng mục tiêu'
    )
