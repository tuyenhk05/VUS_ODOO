# -*- coding: utf-8 -*-
from odoo import models, fields, api

class VusTimeSlot(models.Model):
    _name = 'vus.time.slot'
    _description = 'Khung giờ / Ca học VUS'
    _order = 'days_group, start_time'

    name = fields.Char(string='Tên khung giờ', compute='_compute_name', store=True)
    days_group = fields.Selection([
        ('mwf', 'Thứ 2 - Thứ 4 - Thứ 6'),
        ('tts', 'Thứ 3 - Thứ 5 - Thứ 7'),
        ('ss', 'Thứ 7 - Chủ Nhật')
    ], string='Nhóm ngày', required=True)

    shift = fields.Selection([
        ('ca1', 'Ca 1 (17:30 - 19:00)'),
        ('ca2', 'Ca 2 (19:15 - 20:45)'),
        ('ca3', 'Ca 3 (Thứ 7/CN: 08:00 - 09:30)'),
        ('ca4', 'Ca 4 (Thứ 7/CN: 09:45 - 11:15)')
    ], string='Ca học', required=True)

    start_time = fields.Float(string='Giờ bắt đầu', help='VD: 17.5 = 17:30')
    end_time = fields.Float(string='Giờ kết thúc', help='VD: 19.0 = 19:00')

    @api.depends('days_group', 'shift')
    def _compute_name(self):
        for rec in self:
            days_dict = dict(self._fields['days_group'].selection)
            shift_dict = dict(self._fields['shift'].selection)
            days_str = days_dict.get(rec.days_group, '')
            shift_str = shift_dict.get(rec.shift, '')
            rec.name = f"{days_str} | {shift_str}"
