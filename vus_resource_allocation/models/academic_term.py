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

        # 2. Tạo Odoo Activities cho toàn bộ Giảng viên
        teacher_group = self.env.ref('vus_student.group_vus_teacher', raise_if_not_found=False)
        todo_activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if teacher_group and todo_activity_type:
            teacher_users = teacher_group.users
            for user in teacher_users:
                self.env['mail.activity'].create({
                    'activity_type_id': todo_activity_type.id,
                    'summary': f"Đăng ký ca rảnh {self.name}",
                    'note': f"Hệ thống đã mở đăng ký lịch dạy rảnh cho {self.name}. Vui lòng nộp đăng ký trước hạn chót: {deadline_str}",
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model']._get('vus.academic.term').id,
                    'user_id': user.id,
                    'date_deadline': self.registration_deadline,
                })
        
        # 3. Tạo Odoo Activities cho toàn bộ Quản lý (Manager)
        manager_group = self.env.ref('vus_student.group_vus_manager', raise_if_not_found=False)
        if manager_group and todo_activity_type:
            manager_users = manager_group.users
            for user in manager_users:
                self.env['mail.activity'].create({
                    'activity_type_id': todo_activity_type.id,
                    'summary': f"Theo dõi đăng ký {self.name}",
                    'note': f"Cổng đăng ký ca dạy rảnh của {self.name} đã mở. Hạn chót: {deadline_str}.",
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model']._get('vus.academic.term').id,
                    'user_id': user.id,
                    'date_deadline': self.registration_deadline,
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
        
        todo_activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        teacher_group = self.env.ref('vus_student.group_vus_teacher', raise_if_not_found=False)
        manager_group = self.env.ref('vus_student.group_vus_manager', raise_if_not_found=False)
        
        if not terms or not todo_activity_type:
            return
            
        for term in terms:
            deadline_str = term.registration_deadline.strftime('%d/%m/%Y')
            
            # Cảnh báo cho Giảng viên chưa đăng ký ca rảnh trong kỳ này
            if teacher_group:
                for user in teacher_group.users:
                    # Kiểm tra xem giáo viên này đã có phiếu đăng ký rảnh nào trong kỳ này chưa
                    reg_exists = self.env['vus.teacher.registration'].search_count([
                        ('term_id', '=', term.id),
                        ('teacher_id', '=', user.partner_id.id)
                    ])
                    if reg_exists > 0:
                        continue
                        
                    summary = f"GẤP: Hạn đăng ký ca rảnh {term.name}"
                    existing = self.env['mail.activity'].search([
                        ('res_model', '=', 'vus.academic.term'),
                        ('res_id', '=', term.id),
                        ('user_id', '=', user.id),
                        ('summary', '=', summary)
                    ], limit=1)
                    if not existing:
                        self.env['mail.activity'].create({
                            'activity_type_id': todo_activity_type.id,
                            'summary': summary,
                            'note': f"Sắp hết hạn đăng ký lịch dạy rảnh cho {term.name} (Hạn chót: {deadline_str}). Vui lòng hoàn thành ngay!",
                            'res_id': term.id,
                            'res_model_id': self.env['ir.model']._get('vus.academic.term').id,
                            'user_id': user.id,
                            'date_deadline': term.registration_deadline,
                        })
                        
            # Nhắc nhở cho Managers để đôn đốc
            if manager_group:
                for user in manager_group.users:
                    summary = f"Cảnh báo: Hạn đăng ký {term.name}"
                    existing = self.env['mail.activity'].search([
                        ('res_model', '=', 'vus.academic.term'),
                        ('res_id', '=', term.id),
                        ('user_id', '=', user.id),
                        ('summary', '=', summary)
                    ], limit=1)
                    if not existing:
                        self.env['mail.activity'].create({
                            'activity_type_id': todo_activity_type.id,
                            'summary': summary,
                            'note': f"Cổng đăng ký lịch dạy của {term.name} sẽ đóng vào ngày {deadline_str}. Hãy kiểm tra đôn đốc giảng viên!",
                            'res_id': term.id,
                            'res_model_id': self.env['ir.model']._get('vus.academic.term').id,
                            'user_id': user.id,
                            'date_deadline': term.registration_deadline,
                        })

    def action_activate(self):
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_set_draft(self):
        self.write({'state': 'draft'})
