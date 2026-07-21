# -*- coding: utf-8 -*-
import pytz
from datetime import datetime, time
from odoo import models, fields, api
from markupsafe import Markup

class VusClassSession(models.Model):
    _name = 'vus.class.session'
    _description = 'Buổi học chi tiết của lớp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date, session_number'

    class_id = fields.Many2one('vus.class', string='Lớp học', required=True, ondelete='cascade')
    date = fields.Date(string='Ngày học', required=True)
    time_slot_id = fields.Many2one('vus.time.slot', related='class_id.time_slot_id', string='Ca học', store=True)
    teacher_id = fields.Many2one('res.partner', string='Giảng viên', domain=[('is_teacher', '=', True)])
    session_number = fields.Integer(string='Buổi số', required=True)
    name = fields.Char(string='Tên buổi học', compute='_compute_name', store=True)
    
    attendance_sheet_id = fields.Many2one('vus.attendance.sheet', string='Bảng điểm danh liên kết')
    attendance_state = fields.Selection(related='attendance_sheet_id.state', string='Trạng thái điểm danh', store=True)
    session_count = fields.Integer(string='Số ca dạy', compute='_compute_session_count', store=True)

    @api.depends('class_id')
    def _compute_session_count(self):
        for rec in self:
            rec.session_count = 1

    # Các trường Datetime lưu giờ học chính xác phục vụ hiển thị trên lưới thời gian của Calendar
    start_datetime = fields.Datetime(string='Thời gian bắt đầu', compute='_compute_datetimes', store=True)
    end_datetime = fields.Datetime(string='Thời gian kết thúc', compute='_compute_datetimes', store=True)

    session_status = fields.Selection([
        ('regular', 'Lớp chính thức'),
        ('substituted', 'Dạy thay'),
        ('makeup', 'Dạy bù / Học bù'),
        ('leave', 'Giáo viên báo nghỉ')
    ], string='Trạng thái buổi học', compute='_compute_session_status', store=True, default='regular')

    @api.depends('teacher_id', 'class_id.teacher_id', 'date')
    def _compute_session_status(self):
        for rec in self:
            leave_line = self.env['vus.teacher.leave.line'].search([
                ('session_id', '=', rec.id)
            ], limit=1)
            
            if leave_line:
                if leave_line.state == 'pending':
                    rec.session_status = 'leave'
                elif leave_line.state == 'substituted':
                    rec.session_status = 'substituted'
                elif leave_line.state == 'rescheduled':
                    rec.session_status = 'makeup'
            else:
                if rec.teacher_id and rec.class_id.teacher_id and rec.teacher_id != rec.class_id.teacher_id:
                    rec.session_status = 'substituted'
                else:
                    rec.session_status = 'regular'

    def action_report_leave(self):
        self.ensure_one()
        return {
            'name': 'Báo vắng giảng viên',
            'type': 'ir.actions.act_window',
            'res_model': 'vus.teacher.leave',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_teacher_id': self.teacher_id.id,
                'default_leave_date': self.date,
                'default_class_id': self.class_id.id,
            }
        }

    @api.depends('class_id', 'session_number', 'date')
    def _compute_name(self):
        for rec in self:
            class_name = rec.class_id.class_name if rec.class_id else 'Mới'
            date_str = rec.date.strftime('%d/%m/%Y') if rec.date else ''
            rec.name = f"{class_name} - Buổi {rec.session_number} ({date_str})"

    @api.depends('date', 'time_slot_id.start_time', 'time_slot_id.end_time')
    def _compute_datetimes(self):
        # Lấy múi giờ của người dùng để tính toán chính xác giờ UTC lưu vào database
        tz_name = self.env.user.tz or 'Asia/Ho_Chi_Minh'
        local_tz = pytz.timezone(tz_name)
        
        for rec in self:
            if rec.date and rec.time_slot_id:
                slot = rec.time_slot_id
                
                # Ca học lưu thời gian dưới dạng float (ví dụ: 18.5 -> 18h30)
                start_hour = int(slot.start_time)
                start_minute = int(round((slot.start_time - start_hour) * 60))
                
                end_hour = int(slot.end_time)
                end_minute = int(round((slot.end_time - end_hour) * 60))
                
                # Tạo datetime naive theo giờ địa phương
                local_start = datetime.combine(rec.date, time(start_hour, start_minute))
                local_end = datetime.combine(rec.date, time(end_hour, end_minute))
                
                # Chuyển đổi sang múi giờ UTC và lưu trữ
                rec.start_datetime = local_tz.localize(local_start).astimezone(pytz.utc).replace(tzinfo=None)
                rec.end_datetime = local_tz.localize(local_end).astimezone(pytz.utc).replace(tzinfo=None)
            else:
                rec.start_datetime = False
                rec.end_datetime = False

    def action_open_attendance(self):
        self.ensure_one()
        # Sử dụng sudo() để bỏ qua ràng buộc phân quyền ghi nhận (write) trên vus.class.session
        # và cho phép nạp học viên (đối với giáo viên dạy thay / dạy bù không phải giáo viên chính)
        if not self.attendance_sheet_id:
            existing_sheet = self.env['vus.attendance.sheet'].sudo().search([
                ('class_id', '=', self.class_id.id),
                ('date', '=', self.date)
            ], limit=1)
            
            if existing_sheet:
                self.sudo().write({'attendance_sheet_id': existing_sheet.id})
            else:
                # Nếu chưa có, tạo bảng điểm danh nháp mới cho ngày này
                sheet = self.env['vus.attendance.sheet'].sudo().create({
                    'class_id': self.class_id.id,
                    'date': self.date,
                    'session_number': self.session_number,
                    'teacher_id': self.teacher_id.id,
                    'session': f"Buổi {self.session_number}",
                    'state': 'draft'
                })
                sheet.sudo().action_load_students()
                self.sudo().write({'attendance_sheet_id': sheet.id})

        return {
            'name': 'Điểm danh buổi học',
            'type': 'ir.actions.act_window',
            'res_model': 'vus.attendance.sheet',
            'view_mode': 'form',
            'res_id': self.attendance_sheet_id.id,
            'target': 'current',
        }

    @api.model
    def _cron_notify_today_classes(self):
        today = fields.Date.today()
        # Tìm các buổi học diễn ra trong ngày hôm nay của các lớp đang mở
        sessions = self.search([
            ('date', '=', today),
            ('class_id.state', '=', 'opened')
        ])
        
        for sess in sessions:
            if not sess.teacher_id:
                continue
            # Tìm user liên kết với giáo viên này
            user = self.env['res.users'].search([('partner_id', '=', sess.teacher_id.id)], limit=1)
            if not user:
                continue
                
            # Kiểm tra xem đã gửi thông báo hôm nay chưa để tránh gửi trùng lặp
            summary = f"[VUS] Lịch dạy hôm nay - Lớp {sess.class_id.class_name}"
            existing_msg = self.env['mail.message'].search([
                ('model', '=', 'vus.class.session'),
                ('res_id', '=', sess.id),
                ('partner_ids', 'in', [user.partner_id.id]),
                ('subject', '=', summary)
            ], limit=1)
            
            if not existing_msg:
                slot_name = sess.time_slot_id.name if sess.time_slot_id else ''
                date_str = sess.date.strftime('%d/%m/%Y') if sess.date else ''
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
                session_link = f"{base_url}/web#id={sess.id}&model=vus.class.session&view_type=form"
                note = f"<p>📚 <b>THÔNG BÁO LỊCH DẠY HÔM NAY</b></p>" \
                       f"<p>Kính chào Thầy / Cô <b>{user.name}</b>,</p>" \
                       f"<p>Hệ thống xin thông báo lịch giảng dạy của bạn trong ngày hôm nay như sau:</p>" \
                       f"<ul>" \
                       f"  <li><b>Lớp học:</b> {sess.class_id.class_name}</li>" \
                       f"  <li><b>Buổi học:</b> Buổi số {sess.session_number}</li>" \
                       f"  <li><b>Ca học:</b> {slot_name}</li>" \
                       f"  <li><b>Ngày học:</b> {date_str}</li>" \
                       f"</ul>" \
                       f"<p style=\"margin-top: 10px;\">" \
                       f"  <a href=\"{session_link}\" target=\"_blank\" style=\"background-color: #0C2B5C; color: #FFFFFF; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block;\">" \
                       f"    👉 Click vào đây để mở Buổi học &amp; Điểm danh" \
                       f"  </a>" \
                       f"</p>"
                msg = self.env['mail.message'].sudo().create({
                    'model': 'vus.class.session',
                    'res_id': sess.id,
                    'message_type': 'notification',
                    'subject': summary,
                    'body': Markup(note),
                    'partner_ids': [(6, 0, [user.partner_id.id])],
                })
                self.env['mail.notification'].sudo().create({
                    'mail_message_id': msg.id,
                    'res_partner_id': user.partner_id.id,
                    'notification_type': 'inbox',
                    'is_read': False,
                })
