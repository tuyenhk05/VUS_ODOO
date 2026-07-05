# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VusAttendance(models.Model):
    _name = 'vus.attendance'
    _description = 'Điểm danh học viên'
    _rec_name = 'student_id'
    _order = 'date desc'

    class_id = fields.Many2one(
        'vus.class', 
        string='Lớp học', 
        required=True
    )
    sheet_id = fields.Many2one(
        'vus.attendance.sheet', 
        string='Bảng điểm danh', 
        ondelete='cascade'
    )
    enrollment_id = fields.Many2one(
        'vus.enrollment', 
        string='Học viên', 
        domain="[('class_id', '=', class_id), ('state', 'in', ['confirmed', 'paid'])]",
        required=True
    )
    student_id = fields.Many2one(
        'res.partner',
        related='enrollment_id.student_id',
        string='Học viên',
        store=True
    )
    student_name = fields.Char(
        related='student_id.name',
        string='Tên học viên',
        store=True
    )
    class_name = fields.Char(
        related='class_id.class_name',
        string='Tên lớp',
        store=True
    )
    
    date = fields.Date(
        string='Ngày học',
        required=True,
        default=fields.Date.today
    )
    session = fields.Char(
        string='Buổi học',
        help='VD: Buổi 1 - Ngày 01/06/2025'
    )
    
    status = fields.Selection([
        ('present', 'Có mặt'),
        ('absent', 'Vắng'),
        ('late', 'Đi trễ'),
        ('permission', 'Xin phép'),
    ], string='Trạng thái', required=True, default='present')
    
    note = fields.Text(string='Ghi chú')
    
    teacher_id = fields.Many2one(
        'res.partner',
        related='class_id.teacher_id',
        string='Giảng viên',
        store=True
    )

    state = fields.Selection([
        ('draft', 'Mới'),
        ('done', 'Đã xác nhận'),
    ], string='Trạng thái', default='draft', required=True)

    def action_confirm(self):
        for rec in self:
            rec.state = 'done'

    @api.depends('enrollment_id', 'class_id', 'date')
    def _compute_display_name(self):
        for record in self:
            date_str = record.date.strftime('%d/%m/%Y') if record.date else ''
            student_name = record.enrollment_id.student_id.name if record.enrollment_id else 'Mới'
            class_name = record.class_id.class_name if record.class_id else 'Chưa chọn lớp'
            record.display_name = f"{student_name} - {class_name} ({date_str})"

    @api.constrains('date')
    def _check_date(self):
        for rec in self:
            if rec.date > fields.Date.today():
                raise ValidationError('Không thể điểm danh cho ngày trong tương lai!')
    
    @api.model
    def create(self, vals):
        if 'date' in vals and 'session' not in vals:
            vals['session'] = f"Buổi học ngày {fields.Date.from_string(vals['date']).strftime('%d/%m/%Y')}"
        return super(VusAttendance, self).create(vals)

class VusEnrollmentInherit(models.Model):
    _inherit = 'vus.enrollment'

    attendance_ids = fields.One2many(
        'vus.attendance',
        'enrollment_id',
        string='Điểm danh'
    )


class VusAttendanceSheet(models.Model):
    _name = 'vus.attendance.sheet'
    _description = 'Bảng điểm danh lớp học VUS'
    _order = 'date desc, id desc'

    name = fields.Char(string='Tên bảng điểm danh', compute='_compute_name', store=True)
    class_id = fields.Many2one('vus.class', string='Lớp học', required=True)
    date = fields.Date(string='Ngày học', required=True, default=fields.Date.today)
    session = fields.Char(string='Buổi học', help='VD: Buổi 1, Buổi 2...')
    teacher_id = fields.Many2one('res.partner', related='class_id.teacher_id', string='Giảng viên', store=True, readonly=True)
    
    # Các trường theo dõi tiến độ buổi học
    total_sessions = fields.Integer(string='Tổng số buổi', compute='_compute_total_sessions', store=True)
    session_number = fields.Integer(string='Buổi học số', default=1, required=True)
    session_progress = fields.Char(string='Tiến độ buổi học', compute='_compute_session_progress', store=True)
    
    line_ids = fields.One2many('vus.attendance', 'sheet_id', string='Chi tiết điểm danh')
    
    state = fields.Selection([
        ('draft', 'Mới'),
        ('done', 'Đã điểm danh')
    ], string='Trạng thái', default='draft', required=True)

    @api.depends('class_id')
    def _compute_total_sessions(self):
        for rec in self:
            if rec.class_id and rec.class_id.course_id:
                rec.total_sessions = rec.class_id.course_id.duration_weeks * rec.class_id.course_id.sessions_per_week
            else:
                rec.total_sessions = 0

    @api.depends('session_number', 'total_sessions')
    def _compute_session_progress(self):
        for rec in self:
            rec.session_progress = f"Buổi {rec.session_number} / {rec.total_sessions}"

    @api.onchange('class_id')
    def _onchange_class_id(self):
        if self.class_id:
            existing_sheets = self.env['vus.attendance.sheet'].search([
                ('class_id', '=', self.class_id.id),
                ('id', '!=', self._origin.id if self._origin else False)
            ])
            self.session_number = len(existing_sheets) + 1

    @api.depends('class_id', 'date', 'session_progress')
    def _compute_name(self):
        for rec in self:
            date_str = rec.date.strftime('%d/%m/%Y') if rec.date else ''
            class_name = rec.class_id.class_name if rec.class_id else 'Mới'
            progress_str = rec.session_progress or ''
            rec.name = f"Điểm danh {class_name} - {progress_str} ({date_str})"

    def action_load_students(self):
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError('Chỉ có thể tải lại học viên ở trạng thái Mới!')
            
        self.line_ids.unlink()
        
        enrollments = self.env['vus.enrollment'].search([
            ('class_id', '=', self.class_id.id),
            ('state', 'in', ['confirmed', 'paid'])
        ])
        
        if not enrollments:
            raise ValidationError(f"Không tìm thấy học viên nào đang đăng ký trong lớp {self.class_id.class_name}!")
            
        attendance_vals = []
        for enr in enrollments:
            attendance_vals.append({
                'sheet_id': self.id,
                'class_id': self.class_id.id,
                'enrollment_id': enr.id,
                'date': self.date,
                'session': self.session_progress,
                'status': 'present',
                'state': 'draft'
            })
            
        if attendance_vals:
            self.env['vus.attendance'].create(attendance_vals)
        return True

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError('Vui lòng tải danh sách học viên trước khi xác nhận!')
            rec.line_ids.write({'state': 'done'})
            rec.state = 'done'


class VusClassInherit(models.Model):
    _inherit = 'vus.class'

    attendance_sheet_ids = fields.One2many('vus.attendance.sheet', 'class_id', string='Các buổi điểm danh')
    total_sessions = fields.Integer(string='Tổng số buổi học', compute='_compute_sessions_progress', store=True)
    completed_sessions = fields.Integer(string='Số buổi đã học', compute='_compute_sessions_progress', store=True)
    sessions_progress = fields.Char(string='Tiến độ lớp học', compute='_compute_sessions_progress', store=True)

    @api.depends('course_id', 'attendance_sheet_ids.state')
    def _compute_sessions_progress(self):
        for rec in self:
            total = 0
            if rec.course_id:
                total = rec.course_id.duration_weeks * rec.course_id.sessions_per_week
            completed = len(rec.attendance_sheet_ids.filtered(lambda s: s.state == 'done'))
            rec.total_sessions = total
            rec.completed_sessions = completed
            rec.sessions_progress = f"{completed} / {total}"
