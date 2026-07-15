# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from markupsafe import Markup

class VusClassInherit(models.Model):
    _inherit = 'vus.class'

    term_id = fields.Many2one('vus.academic.term', string='Kỳ học')
    time_slot_id = fields.Many2one('vus.time.slot', string='Khung giờ / Ca học')
    
    eligible_teacher_ids = fields.Many2many(
        'res.partner', 
        compute='_compute_eligible_teacher_ids',
        string='Giáo viên khả dụng'
    )
    eligible_course_ids = fields.Many2many(
        'vus.course',
        compute='_compute_eligible_course_ids',
        string='Khóa học khả dụng'
    )

    session_ids = fields.One2many(
        'vus.class.session', 
        'class_id', 
        string='Danh sách buổi học'
    )
    closing_date = fields.Date(string='Hạn đóng lớp (Khóa lớp)')
    suggested_teacher_ids = fields.One2many(
        'vus.class.teacher.suggestion', 
        'class_id', 
        compute='_compute_suggested_teachers',
        string='Đề xuất giảng viên'
    )

    @api.depends('term_id')
    def _compute_eligible_course_ids(self):
        for rec in self:
            all_courses = self.env['vus.course'].search([('state', '=', 'confirmed')])
            if rec.term_id:
                eligible = []
                for course in all_courses:
                    class_count = self.env['vus.class'].search_count([
                        ('term_id', '=', rec.term_id.id),
                        ('course_id', '=', course.id),
                        ('state', '!=', 'cancelled')
                    ])
                    # Nếu đang chỉnh sửa chính lớp này, trừ đi 1 để tránh tự lọc chính mình
                    if rec.id and rec.course_id == course:
                        class_count -= 1
                    if class_count < course.max_classes:
                        eligible.append(course.id)
                rec.eligible_course_ids = [(6, 0, eligible)]
            else:
                rec.eligible_course_ids = all_courses

    @api.depends('term_id', 'time_slot_id')
    def _compute_eligible_teacher_ids(self):
        for rec in self:
            if rec.term_id and rec.time_slot_id:
                # Tìm các đăng ký dạy của giáo viên đã được duyệt chứa ca này trong kỳ
                registrations = self.env['vus.teacher.registration'].search([
                    ('term_id', '=', rec.term_id.id),
                    ('time_slot_ids', 'in', rec.time_slot_id.id),
                    ('state', '=', 'approved')
                ])
                teachers = registrations.mapped('teacher_id')
                valid_teachers = []
                for teacher in teachers:
                    class_count = self.env['vus.class'].search_count([
                        ('term_id', '=', rec.term_id.id),
                        ('teacher_id', '=', teacher.id),
                        ('state', '!=', 'cancelled')
                    ])
                    # Nếu đang chỉnh sửa chính lớp này, trừ đi 1 để tránh tự lọc chính mình
                    if rec.id and rec.teacher_id == teacher:
                        class_count -= 1
                    if class_count < teacher.max_classes:
                        valid_teachers.append(teacher.id)
                rec.eligible_teacher_ids = [(6, 0, valid_teachers)]
            else:
                rec.eligible_teacher_ids = self.env['res.partner'].search([('is_teacher', '=', True)])

    @api.constrains('course_id', 'term_id')
    def _check_course_class_limit(self):
        for rec in self:
            if rec.course_id and rec.term_id:
                class_count = self.env['vus.class'].search_count([
                    ('term_id', '=', rec.term_id.id),
                    ('course_id', '=', rec.course_id.id),
                    ('id', '!=', rec.id),
                    ('state', '!=', 'cancelled')
                ])
                if class_count >= rec.course_id.max_classes:
                    raise ValidationError(
                        f"Khóa học '{rec.course_id.course_name}' đã đạt giới hạn số lớp tối đa trong {rec.term_id.name} "
                        f"({rec.course_id.max_classes} lớp)!"
                    )

    @api.constrains('teacher_id', 'term_id')
    def _check_teacher_class_limit(self):
        for rec in self:
            if rec.teacher_id and rec.term_id:
                class_count = self.env['vus.class'].search_count([
                    ('term_id', '=', rec.term_id.id),
                    ('teacher_id', '=', rec.teacher_id.id),
                    ('id', '!=', rec.id),
                    ('state', '!=', 'cancelled')
                ])
                if class_count >= rec.teacher_id.max_classes:
                    raise ValidationError(
                        f"Giảng viên '{rec.teacher_id.name}' đã vượt quá số lớp dạy tối đa trong {rec.term_id.name} "
                        f"({rec.teacher_id.max_classes} lớp)!"
                    )

    @api.constrains('teacher_id', 'term_id', 'time_slot_id')
    def _check_teacher_availability(self):
        for rec in self:
            if rec.teacher_id and rec.term_id and rec.time_slot_id:
                if rec.teacher_id not in rec.eligible_teacher_ids:
                    raise ValidationError(
                        f"Giảng viên {rec.teacher_id.name} chưa đăng ký hoặc chưa được duyệt "
                        f"cho ca học {rec.time_slot_id.name} trong {rec.term_id.name}!"
                    )

    def action_open_class(self):
        # Kế thừa mở lớp: tự động sinh lịch học chi tiết các buổi học
        super(VusClassInherit, self).action_open_class()
        for rec in self:
            if not rec.closing_date and rec.payment_deadline:
                rec.closing_date = rec.payment_deadline
            if rec.term_id and rec.time_slot_id:
                rec.action_generate_sessions()

    def action_generate_sessions(self):
        for rec in self:
            if not rec.start_date or not rec.time_slot_id:
                continue
            
            # Xóa các buổi học chi tiết cũ
            rec.session_ids.unlink()

            # Lấy danh sách thứ tự ngày học trong tuần (0=Mon, ..., 6=Sun)
            days_map = {
                'mwf': [0, 2, 4],
                'tts': [1, 3, 5],
                'ss': [5, 6]
            }
            active_days = days_map.get(rec.time_slot_id.days_group, [])
            
            # Tính toán tổng số buổi dựa trên số tuần và số ca/tuần của khóa học
            sessions_per_week = len(active_days)
            duration_weeks = rec.course_id.duration_weeks or 12
            total_sessions = duration_weeks * sessions_per_week

            # Sinh lịch học chi tiết các buổi
            generated_sessions = []
            current_date = rec.start_date
            session_count = 0
            
            while session_count < total_sessions:
                if current_date.weekday() in active_days:
                    session_count += 1
                    generated_sessions.append({
                        'class_id': rec.id,
                        'date': current_date,
                        'session_number': session_count,
                        'teacher_id': rec.teacher_id.id if rec.teacher_id else False,
                    })
                current_date += datetime.timedelta(days=1)
            
            if generated_sessions:
                self.env['vus.class.session'].create(generated_sessions)

    @api.model
    def _cron_notify_payment_deadline(self):
        today = fields.Date.today()
        three_days_later = today + datetime.timedelta(days=3)
        
        # Tìm các lớp học đang mở có hạn đóng học phí cận hạn (trong vòng 3 ngày tới)
        classes = self.search([
            ('payment_deadline', '>=', today),
            ('payment_deadline', '<=', three_days_later),
            ('state', 'in', ['opened', 'full'])
        ])
        
        staff_group = self.env.ref('vus_student.group_vus_staff', raise_if_not_found=False)
        if not staff_group:
            return
            
        staff_users = staff_group.users
        for rec in classes:
            # Kiểm tra xem lớp này có học viên chưa đóng phí không
            unpaid_count = self.env['vus.enrollment'].search_count([
                ('class_id', '=', rec.id),
                ('state', 'in', ['draft', 'confirmed'])
            ])
            if unpaid_count == 0:
                continue
                
            deadline_str = rec.payment_deadline.strftime('%d/%m/%Y')
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            class_link = f"{base_url}/web#id={rec.id}&model=vus.class&view_type=form"
            summary = f"[VUS] Hạn đóng học phí cận kề - Lớp {rec.class_name}"
            note = f"<p>Kính gửi Bộ phận Giáo vụ/Staff,</p>" \
                   f"<p>Hệ thống xin thông báo lớp học <strong>{rec.class_name}</strong> đang có hạn đóng học phí cận kề:</p>" \
                   f"<ul>" \
                   f"  <li><strong>Hạn đóng phí:</strong> {deadline_str}</li>" \
                   f"  <li><strong>Số học viên chưa đóng phí:</strong> {unpaid_count} học viên</li>" \
                   f"</ul>" \
                   f"<p>Vui lòng click vào <a href=\"{class_link}\" target=\"_blank\"><strong>đây</strong></a> để xem chi tiết danh sách học viên lớp học và đôn đốc hoàn thành học phí.</p>"
            
            for user in staff_users:
                # Kiểm tra trùng lặp
                existing_msg = self.env['mail.message'].search([
                    ('model', '=', 'vus.class'),
                    ('res_id', '=', rec.id),
                    ('partner_ids', 'in', [user.partner_id.id]),
                    ('subject', '=', summary)
                ], limit=1)
                if not existing_msg:
                    rec.message_notify(
                        body=Markup(note),
                        subject=summary,
                        partner_ids=[user.partner_id.id]
                    )

    @api.depends('term_id', 'time_slot_id', 'eligible_teacher_ids')
    def _compute_suggested_teachers(self):
        self.env['vus.class.teacher.suggestion'].sudo().search([('class_id', 'in', self.ids)]).unlink()
        for rec in self:
            suggestions = []
            if rec.term_id and rec.time_slot_id and rec.eligible_teacher_ids:
                for teacher in rec.eligible_teacher_ids:
                    class_count = self.env['vus.class'].search_count([
                        ('term_id', '=', rec.term_id.id),
                        ('teacher_id', '=', teacher.id),
                        ('state', '!=', 'cancelled')
                    ])
                    suggestions.append((0, 0, {
                        'teacher_id': teacher.id,
                        'active_class_count': class_count,
                        'max_classes': teacher.max_classes
                    }))
            rec.suggested_teacher_ids = suggestions

    def action_assign_optimal_teacher(self):
        self.ensure_one()
        if not self.term_id or not self.time_slot_id:
            raise ValidationError("Vui lòng chọn Kỳ học và Ca học trước khi xếp giáo viên!")
        
        eligible_teachers = self.eligible_teacher_ids
        if not eligible_teachers:
            raise ValidationError("Không tìm thấy giáo viên nào có ca rảnh tương ứng trong kỳ học này!")
        
        best_teacher = False
        min_classes = 999999
        
        for teacher in eligible_teachers:
            class_count = self.env['vus.class'].search_count([
                ('term_id', '=', self.term_id.id),
                ('teacher_id', '=', teacher.id),
                ('state', '!=', 'cancelled')
            ])
            if class_count >= teacher.max_classes:
                continue
                
            if class_count < min_classes:
                min_classes = class_count
                best_teacher = teacher
                
        if not best_teacher:
            raise ValidationError("Tất cả giáo viên phù hợp đều đã đạt giới hạn số lớp dạy tối đa trong kỳ này!")
            
        self.write({'teacher_id': best_teacher.id})
        if self.session_ids:
            self.session_ids.write({'teacher_id': best_teacher.id})
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Xếp lớp thành công',
                'message': f"Đã xếp Giảng viên {best_teacher.name} cho lớp (đang dạy {min_classes} lớp trong kỳ này).",
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_attendance_sheets(self):
        self.ensure_one()
        return {
            'name': 'Bảng điểm danh lớp học',
            'type': 'ir.actions.act_window',
            'res_model': 'vus.attendance.sheet',
            'view_mode': 'tree,form',
            'domain': [('class_id', '=', self.id)],
            'context': {'default_class_id': self.id},
            'target': 'current',
        }


class VusClassTeacherSuggestion(models.TransientModel):
    _name = 'vus.class.teacher.suggestion'
    _description = 'Đề xuất giảng viên cho lớp học'
    
    class_id = fields.Many2one('vus.class', string='Lớp học')
    teacher_id = fields.Many2one('res.partner', string='Giảng viên')
    active_class_count = fields.Integer(string='Số lớp đang dạy trong kỳ')
    max_classes = fields.Integer(string='Giới hạn số lớp')
    
    def action_select_teacher(self):
        self.ensure_one()
        self.class_id.write({'teacher_id': self.teacher_id.id})
        if self.class_id.session_ids:
            self.class_id.session_ids.write({'teacher_id': self.teacher_id.id})
