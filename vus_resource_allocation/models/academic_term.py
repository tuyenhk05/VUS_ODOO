# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VusAcademicTerm(models.Model):
    _name = 'vus.academic.term'
    _description = 'Kỳ học tại VUS'
    _order = 'start_date desc'

    name = fields.Char(string='Tên kỳ học', required=True)
    start_date = fields.Date(string='Ngày bắt đầu', required=True)
    end_date = fields.Date(string='Ngày kết thúc', required=True)
    active = fields.Boolean(string='Đang hoạt động', default=True)

    registration_deadline = fields.Date(string='Hạn đăng ký lịch rảnh')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('registration', 'Đang đăng ký lịch'),
        ('active', 'Đang diễn ra'),
        ('completed', 'Đã kết thúc')
    ], string='Trạng thái', default='draft', required=True)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError('Ngày bắt đầu không được lớn hơn ngày kết thúc!')

    def action_start_registration(self):
        self.write({'state': 'registration'})
        # Gửi email thông báo cho toàn bộ giảng viên đang hoạt động
        teachers = self.env['res.partner'].search([('is_teacher', '=', True), ('email', '!=', False)])
        if teachers:
            mail_values = []
            deadline_str = self.registration_deadline.strftime('%d/%m/%Y') if self.registration_deadline else 'chưa xác định'
            body = f"""
                <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333333;">
                    <p>Kính chào Quý Thầy/Cô,</p>
                    <p>Hệ thống VUS Đào tạo đã mở cổng tiếp nhận đăng ký lịch dạy rảnh cho <strong>Kỳ học: {self.name}</strong>.</p>
                    <p>Thời gian đăng ký bắt đầu từ hôm nay và hạn chót đăng ký là: <strong style="color: #d9534f;">{deadline_str}</strong>.</p>
                    <p>Vui lòng đăng nhập vào tài khoản cá nhân trên hệ thống VUS Odoo và thực hiện tạo phiếu <strong>Đăng ký lịch dạy</strong> trước thời hạn trên.</p>
                    <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 20px 0;"/>
                    <p style="font-size: 12px; color: #777777;">Trân trọng,<br/>Phòng Giáo vụ - Hệ thống Anh văn Hội Việt Mỹ VUS</p>
                </div>
            """
            for teacher in teachers:
                mail_values.append({
                    'subject': f"[VUS] Thông báo Đăng ký lịch dạy rảnh - {self.name}",
                    'email_to': teacher.email,
                    'body_html': body,
                })
            mail_records = self.env['mail.mail'].create(mail_values)
            mail_records.send()

    def action_activate(self):
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_set_draft(self):
        self.write({'state': 'draft'})
