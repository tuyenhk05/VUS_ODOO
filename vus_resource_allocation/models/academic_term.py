# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from markupsafe import Markup

class VusAcademicTerm(models.Model):
    _name = 'vus.academic.term'
    _description = 'Kỳ học tại VUS'
    _inherit = ['mail.thread']
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
        # 1. Gửi email thông báo cho toàn bộ giảng viên đang hoạt động
        teachers = self.env['res.partner'].search([('is_teacher', '=', True), ('email', '!=', False)])
        deadline_str = self.registration_deadline.strftime('%d/%m/%Y') if self.registration_deadline else 'chưa xác định'
        if teachers:
            mail_values = []
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

        # 2. Gửi Odoo Inbox Message cho toàn bộ Giảng viên
        teacher_group = self.env.ref('vus_student.group_vus_teacher', raise_if_not_found=False)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
        if teacher_group:
            teacher_users = teacher_group.users
            for user in teacher_users:
                reg = self.env['vus.teacher.registration'].search([
                    ('term_id', '=', self.id),
                    ('teacher_id', '=', user.partner_id.id)
                ], limit=1)
                if reg:
                    reg_link = f"{base_url}/web#id={reg.id}&model=vus.teacher.registration&view_type=form"
                else:
                    reg_link = f"{base_url}/web#model=vus.teacher.registration&view_type=list"
                
                t_subj = f"[VUS] Mở cổng đăng ký lịch dạy rảnh - Kỳ {self.name}"
                t_body = f"<p>📅 <b>THÔNG BÁO MỞ CỔNG ĐĂNG KÝ LỊCH DẠY RẢNH</b></p>" \
                         f"<p>Kính chào Thầy / Cô <b>{user.name}</b>,</p>" \
                         f"<p>Hệ thống VUS Đào tạo đã chính thức mở cổng tiếp nhận đăng ký lịch dạy rảnh cho <b>Kỳ học: {self.name}</b>.</p>" \
                         f"<ul>" \
                         f"  <li><b>Hạn chót đăng ký:</b> {deadline_str}</li>" \
                         f"</ul>" \
                         f"<p style=\"margin-top: 10px;\">" \
                         f"  <a href=\"{reg_link}\" target=\"_blank\" style=\"background-color: #0C2B5C; color: #FFFFFF; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block;\">" \
                         f"    👉 Click vào đây để điền Phiếu đăng ký lịch dạy" \
                         f"  </a>" \
                         f"</p>"
                msg = self.env['mail.message'].sudo().create({
                    'model': 'vus.academic.term',
                    'res_id': self.id,
                    'message_type': 'notification',
                    'subject': t_subj,
                    'body': Markup(t_body),
                    'partner_ids': [(6, 0, [user.partner_id.id])],
                })
                self.env['mail.notification'].sudo().create({
                    'mail_message_id': msg.id,
                    'res_partner_id': user.partner_id.id,
                    'notification_type': 'inbox',
                    'is_read': False,
                })
        
        # 3. Gửi Odoo Inbox Message cho toàn bộ Quản lý (Manager)
        manager_group = self.env.ref('vus_student.group_vus_manager', raise_if_not_found=False)
        if manager_group:
            manager_users = manager_group.users
            for user in manager_users:
                term_link = f"{base_url}/web#id={self.id}&model=vus.academic.term&view_type=form"
                m_subj = f"[VUS] Theo dõi cổng đăng ký lịch dạy rảnh - Kỳ {self.name}"
                m_body = f"<p>📊 <b>QUẢN LÝ CỔNG ĐĂNG KÝ LỊCH DẠY RẢNH</b></p>" \
                         f"<p>Kính gửi Quản lý Đào tạo,</p>" \
                         f"<p>Cổng đăng ký lịch dạy rảnh cho <b>Kỳ học: {self.name}</b> đã chính thức được mở.</p>" \
                         f"<ul>" \
                         f"  <li><b>Hạn chót đăng ký của giáo viên:</b> {deadline_str}</li>" \
                         f"</ul>" \
                         f"<p style=\"margin-top: 10px;\">" \
                         f"  <a href=\"{term_link}\" target=\"_blank\" style=\"background-color: #0C2B5C; color: #FFFFFF; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block;\">" \
                         f"    👉 Click vào đây để mở theo dõi Kỳ học {self.name}" \
                         f"  </a>" \
                         f"</p>"
                msg = self.env['mail.message'].sudo().create({
                    'model': 'vus.academic.term',
                    'res_id': self.id,
                    'message_type': 'notification',
                    'subject': m_subj,
                    'body': Markup(m_body),
                    'partner_ids': [(6, 0, [user.partner_id.id])],
                })
                self.env['mail.notification'].sudo().create({
                    'mail_message_id': msg.id,
                    'res_partner_id': user.partner_id.id,
                    'notification_type': 'inbox',
                    'is_read': False,
                })

    @api.model
    def _cron_notify_registration_deadline(self):
        import datetime
        today = fields.Date.today()
        two_days_later = today + datetime.timedelta(days=2)
        
        # Tìm các kỳ học đang ở trạng thái 'registration' và cách hạn đăng ký <= 2 ngày
        terms = self.search([
            ('state', '=', 'registration'),
            ('registration_deadline', '>=', today),
            ('registration_deadline', '<=', two_days_later)
        ])
        
        teacher_group = self.env.ref('vus_student.group_vus_teacher', raise_if_not_found=False)
        manager_group = self.env.ref('vus_student.group_vus_manager', raise_if_not_found=False)
        
        if not terms:
            return
            
        for term in terms:
            deadline_str = term.registration_deadline.strftime('%d/%m/%Y')
            
            # Cảnh báo cho Giảng viên chưa đăng ký ca rảnh trong kỳ này
            if teacher_group:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
                for user in teacher_group.users:
                    reg = self.env['vus.teacher.registration'].search([
                        ('term_id', '=', term.id),
                        ('teacher_id', '=', user.partner_id.id)
                    ], limit=1)
                    if reg and reg.state != 'draft':
                        continue
                        
                    if reg:
                        reg_link = f"{base_url}/web#id={reg.id}&model=vus.teacher.registration&view_type=form"
                    else:
                        reg_link = f"{base_url}/web#model=vus.teacher.registration&view_type=list"
                        
                    summary = f"[VUS] GẤP: Hạn đăng ký ca dạy rảnh sắp hết - Kỳ {term.name}"
                    existing_msg = self.env['mail.message'].search([
                        ('model', '=', 'vus.academic.term'),
                        ('res_id', '=', term.id),
                        ('partner_ids', 'in', [user.partner_id.id]),
                        ('subject', '=', summary)
                    ], limit=1)
                    if not existing_msg:
                        t_body = f"<p>⏰ <b>CẢNH BÁO HẠN ĐĂNG KÝ LỊCH DẠY RẢNH SẮP HẾT</b></p>" \
                                 f"<p>Kính chào Thầy / Cô <b>{user.name}</b>,</p>" \
                                 f"<p>Hệ thống xin nhắc nhở lịch đăng ký ca dạy rảnh cho <b>Kỳ học: {term.name}</b> sắp hết hạn:</p>" \
                                 f"<ul>" \
                                 f"  <li><b>Hạn chót:</b> {deadline_str}</li>" \
                                 f"</ul>" \
                                 f"<p style=\"margin-top: 10px;\">" \
                                 f"  <a href=\"{reg_link}\" target=\"_blank\" style=\"background-color: #0C2B5C; color: #FFFFFF; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block;\">" \
                                 f"    👉 Click vào đây để hoàn thành Phiếu đăng ký" \
                                 f"  </a>" \
                                 f"</p>"
                        msg = self.env['mail.message'].sudo().create({
                            'model': 'vus.academic.term',
                            'res_id': term.id,
                            'message_type': 'notification',
                            'subject': summary,
                            'body': Markup(t_body),
                            'partner_ids': [(6, 0, [user.partner_id.id])],
                        })
                        self.env['mail.notification'].sudo().create({
                            'mail_message_id': msg.id,
                            'res_partner_id': user.partner_id.id,
                            'notification_type': 'inbox',
                            'is_read': False,
                        })
                        
            # Nhắc nhở cho Managers để đôn đốc
            if manager_group:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
                for user in manager_group.users:
                    summary = f"[VUS] Đôn đốc hạn đăng ký lịch dạy rảnh - Kỳ {term.name}"
                    existing_msg = self.env['mail.message'].search([
                        ('model', '=', 'vus.academic.term'),
                        ('res_id', '=', term.id),
                        ('partner_ids', 'in', [user.partner_id.id]),
                        ('subject', '=', summary)
                    ], limit=1)
                    if not existing_msg:
                        term_link = f"{base_url}/web#id={term.id}&model=vus.academic.term&view_type=form"
                        m_body = f"<p>📌 <b>ĐÔN ĐỐC HẠN ĐĂNG KÝ LỊCH DẠY RẢNH</b></p>" \
                                 f"<p>Kính gửi Quản lý Đào tạo,</p>" \
                                 f"<p>Thời hạn đăng ký lịch dạy rảnh cho <b>Kỳ học: {term.name}</b> sẽ đóng vào ngày <b>{deadline_str}</b>.</p>" \
                                 f"<p style=\"margin-top: 10px;\">" \
                                 f"  <a href=\"{term_link}\" target=\"_blank\" style=\"background-color: #0C2B5C; color: #FFFFFF; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block;\">" \
                                 f"    👉 Click vào đây để đôn đốc giảng viên chưa đăng ký" \
                                 f"  </a>" \
                                 f"</p>"
                        msg = self.env['mail.message'].sudo().create({
                            'model': 'vus.academic.term',
                            'res_id': term.id,
                            'message_type': 'notification',
                            'subject': summary,
                            'body': Markup(m_body),
                            'partner_ids': [(6, 0, [user.partner_id.id])],
                        })
                        self.env['mail.notification'].sudo().create({
                            'mail_message_id': msg.id,
                            'res_partner_id': user.partner_id.id,
                            'notification_type': 'inbox',
                            'is_read': False,
                        })

    def action_activate(self):
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_set_draft(self):
        self.write({'state': 'draft'})
