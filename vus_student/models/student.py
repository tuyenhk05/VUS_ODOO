# -*- coding: utf-8 -*-
from odoo import models, fields, api

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
    max_classes = fields.Integer(
        string='Số lớp dạy tối đa/kỳ',
        default=3
    )
    student_code = fields.Char(
        string='Mã học viên',
        help="Nhập mã định danh học viên VUS"
    )
    dob = fields.Date(
        string='Ngày sinh',
        help="Ngày sinh của học viên"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_student') and not vals.get('student_code'):
                vals['student_code'] = self.env['ir.sequence'].next_by_code('res.partner.student.code') or 'New'
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        for partner in self:
            if partner.is_student and not partner.student_code:
                super(ResPartner, partner).write({
                    'student_code': self.env['ir.sequence'].next_by_code('res.partner.student.code') or 'New'
                })
        return res
