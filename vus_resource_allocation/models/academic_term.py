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
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if teacher_group:
            teacher_users = teacher_group.users
            for user in teacher_users:
                # Tìm xem giáo viên đã có phiếu đăng ký rảnh nào chưa
                reg = self.env['vus.teacher.registration'].search([
                    ('term_id', '=', self.id),
                    ('teacher_id', '=', user.partner_id.id)
                ], limit=1)
                if reg:
                    reg_link = f"{base_url}/web#id={reg.id}&model=vus.teacher.registration&view_type=form"
                else:
                    reg_link = f"{base_url}/web#model=vus.teacher.registration&view_type=list"
                
                self.message_notify(
                    body=Markup(f"<p>Kính chào Thầy/Cô <strong>{user.name}</strong>,</p>"
                         f"<p>Hệ thống VUS Đào tạo đã chính thức mở cổng tiếp nhận đăng ký lịch dạy rảnh cho <strong>Kỳ học: {self.name}</strong>.</p>"
                         f"<ul>"
                         f"  <li><strong>Hạn chót đăng ký:</strong> {deadline_str}</li>"
                         f"</ul>"
                         f"<p>Vui lòng click vào <a href=\"{reg_link}\" target=\"_blank\"><strong>đây</strong></a> để điền và hoàn thành phiếu <strong>Đăng ký lịch dạy</strong> trước thời hạn trên.</p>"),
                    subject=f"[VUS] Mở cổng đăng ký lịch dạy rảnh - Kỳ {self.name}",
                    partner_ids=[user.partner_id.id]
                )
        
        # 3. Gửi Odoo Inbox Message cho toàn bộ Quản lý (Manager)
        manager_group = self.env.ref('vus_student.group_vus_manager', raise_if_not_found=False)
        if manager_group:
            manager_users = manager_group.users
            for user in manager_users:
                term_link = f"{base_url}/web#id={self.id}&model=vus.academic.term&view_type=form"
                self.message_notify(
                    body=Markup(f"<p>Kính gửi Quản lý Đào tạo,</p>"
                         f"<p>Cổng đăng ký lịch dạy rảnh cho <strong>Kỳ học: {self.name}</strong> đã chính thức được mở.</p>"
                         f"<ul>"
                         f"  <li><strong>Hạn chót đăng ký của giáo viên:</strong> {deadline_str}</li>"
                         f"</ul>"
                         f"<p>Vui lòng click vào <a href=\"{term_link}\" target=\"_blank\"><strong>đây</strong></a> để theo dõi tiến độ đăng ký của các giảng viên phục vụ công tác xếp lớp.</p>"),
                    subject=f"[VUS] Theo dõi cổng đăng ký lịch dạy rảnh - Kỳ {self.name}",
                    partner_ids=[user.partner_id.id]
                )

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
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                for user in teacher_group.users:
                    # Kiểm tra xem giáo viên này đã có phiếu đăng ký rảnh nào trong kỳ này chưa
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
                        term.message_notify(
                            body=Markup(f"<p>Kính chào Thầy/Cô <strong>{user.name}</strong>,</p>"
                                 f"<p>Hệ thống xin nhắc nhở lịch đăng ký ca dạy rảnh cho <strong>Kỳ học: {term.name}</strong> sắp hết hạn:</p>"
                                 f"<ul>"
                                 f"  <li><strong>Hạn chót:</strong> {deadline_str}</li>"
                                 f"</ul>"
                                 f"<p>Hiện tại hệ thống chưa ghi nhận phiếu đăng ký của bạn. Vui lòng click vào <a href=\"{reg_link}\" target=\"_blank\"><strong>đây</strong></a> để hoàn thành ngay để không ảnh hưởng đến việc xếp lịch dạy.</p>"),
                            subject=summary,
                            partner_ids=[user.partner_id.id]
                        )
                        
            # Nhắc nhở cho Managers để đôn đốc
            if manager_group:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
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
                        term.message_notify(
                            body=Markup(f"<p>Kính gửi Quản lý Đào tạo,</p>"
                                 f"<p>Thời hạn đăng ký lịch dạy rảnh cho <strong>Kỳ học: {term.name}</strong> sẽ đóng vào ngày <strong>{deadline_str}</strong>.</p>"
                                 f"<p>Vui lòng click vào <a href=\"{term_link}\" target=\"_blank\"><strong>đây</strong></a> để kiểm tra và đôn đốc các giảng viên chưa hoàn thành đăng ký.</p>"),
                            subject=summary,
                            partner_ids=[user.partner_id.id]
                        )

    def action_activate(self):
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_set_draft(self):
        self.write({'state': 'draft'})
