# -*- coding: utf-8 -*-
from odoo import models, fields

class VusCourse(models.Model):
    _name = 'vus.course'
    _description = 'Khóa học VUS'

    name = fields.Char(
        string='Tên khóa học',
        required=True
    )
    code = fields.Char(
        string='Mã khóa học',
        required=True
    )
    tuition_fee = fields.Float(
        string='Học phí gốc',
        default=0.0
    )
