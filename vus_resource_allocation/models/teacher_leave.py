# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VusTeacherLeave(models.Model):
    _name = 'vus.teacher.leave'
    _description = 'Báo vắng giảng viên'
    _order = 'leave_date desc'

    name = fields.Char(string='Mã báo vắng', compute='_compute_name', store=True)
    
    teacher_id = fields.Many2one(
        'res.partner', 
        string='Giảng viên', 
        domain=[('is_teacher', '=', True)], 
        required=True,
        default=lambda self: self.env.user.partner_id if self.env.user.has_group('vus_student.group_vus_teacher') else False
    )
    
    leave_date = fields.Date(string='Ngày vắng', required=True, default=fields.Date.today)
    
    class_id = fields.Many2one(
        'vus.class', 
        string='Lớp học vắng', 
        required=True
    )
    
    reason = fields.Text(string='Lý do vắng')
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Chờ duyệt'),
        ('confirmed', 'Đã xác nhận'),
        ('resolved', 'Đã xử lý xong')
    ], string='Trạng thái', default='draft', required=True)

    affected_line_ids = fields.One2many(
        'vus.teacher.leave.line', 
        'leave_id', 
        string='Buổi học bị ảnh hưởng'
    )

    # Các trường kiểm tra quyền và hỗ trợ domain lọc lớp học động
    is_teacher_user = fields.Boolean(compute='_compute_is_teacher_user')
    eligible_class_ids = fields.Many2many('vus.class', compute='_compute_eligible_class_ids')

    @api.depends('teacher_id')
    def _compute_is_teacher_user(self):
        is_teacher = self.env.user.has_group('vus_student.group_vus_teacher')
        for rec in self:
            rec.is_teacher_user = is_teacher

    @api.depends('leave_date', 'teacher_id')
    def _compute_eligible_class_ids(self):
        for rec in self:
            if rec.leave_date and rec.teacher_id:
                # Tìm các buổi học chi tiết trong ngày vắng của giảng viên này
                sessions = self.env['vus.class.session'].search([
                    ('teacher_id', '=', rec.teacher_id.id),
                    ('date', '=', rec.leave_date),
                    ('class_id.state', '=', 'opened')
                ])
                rec.eligible_class_ids = sessions.mapped('class_id')
            else:
                rec.eligible_class_ids = self.env['vus.class'].search([('state', '=', 'opened')])

    @api.constrains('teacher_id')
    def _check_teacher_id(self):
        for rec in self:
            if self.env.user.has_group('vus_student.group_vus_teacher') and rec.teacher_id != self.env.user.partner_id:
                raise ValidationError("Bạn chỉ có quyền báo vắng cho chính bản thân mình!")

    @api.depends('teacher_id', 'leave_date', 'class_id')
    def _compute_name(self):
        for rec in self:
            date_str = rec.leave_date.strftime('%d/%m/%Y') if rec.leave_date else ''
            teacher_name = rec.teacher_id.name if rec.teacher_id else 'Mới'
            class_name = rec.class_id.class_name if rec.class_id else ''
            rec.name = f"Báo vắng - {teacher_name} ({date_str}){f' - Lớp {class_name}' if class_name else ''}"

    def action_submit(self):
        for rec in self:
            if not rec.class_id:
                raise ValidationError("Vui lòng chọn lớp học bạn sẽ vắng!")
            rec.state = 'submitted'

    def action_confirm(self):
        for rec in self:
            if not rec.leave_date or not rec.teacher_id or not rec.class_id:
                raise ValidationError("Vui lòng chọn giảng viên, ngày báo vắng và lớp học!")
            
            # Tìm buổi học chi tiết tương ứng trong lịch của giáo viên
            session = self.env['vus.class.session'].search([
                ('class_id', '=', rec.class_id.id),
                ('teacher_id', '=', rec.teacher_id.id),
                ('date', '=', rec.leave_date)
            ], limit=1)

            if not session:
                raise ValidationError(
                    f"Không tìm thấy buổi học nào của giảng viên {rec.teacher_id.name} "
                    f"phụ trách lớp {rec.class_id.class_name} vào ngày {rec.leave_date.strftime('%d/%m/%Y')}!"
                )
            
            # Xóa dòng ảnh hưởng cũ
            rec.affected_line_ids.unlink()

            # Tạo dòng ảnh hưởng mới liên kết trực tiếp với session đó
            self.env['vus.teacher.leave.line'].create({
                'leave_id': rec.id,
                'class_id': rec.class_id.id,
                'date': rec.leave_date,
                'session_id': session.id,
                'state': 'pending'
            })
            
            rec.state = 'confirmed'

    def action_resolve(self):
        for rec in self:
            if any(line.state == 'pending' for line in rec.affected_line_ids):
                raise ValidationError("Vui lòng xử lý giải quyết dạy thay / dạy bù cho lớp học bị ảnh hưởng trước khi hoàn tất!")
            rec.state = 'resolved'

    def action_set_draft(self):
        for rec in self:
            rec.state = 'draft'


class VusTeacherLeaveLine(models.Model):
    _name = 'vus.teacher.leave.line'
    _description = 'Chi tiết lớp bị ảnh hưởng do giảng viên vắng'

    leave_id = fields.Many2one('vus.teacher.leave', ondelete='cascade', string='Phiếu báo vắng')
    class_id = fields.Many2one('vus.class', string='Lớp học', required=True)
    date = fields.Date(string='Ngày vắng', required=True)
    session_id = fields.Many2one('vus.class.session', string='Buổi học bị ảnh hưởng')
    
    state = fields.Selection([
        ('pending', 'Chờ xử lý'),
        ('substituted', 'Dạy thay'),
        ('rescheduled', 'Dạy bù')
    ], string='Trạng thái', default='pending', required=True)

    # 1. Thông tin dạy thay
    substitute_teacher_id = fields.Many2one(
        'res.partner', 
        string='Giáo viên dạy thay',
        domain=[('is_teacher', '=', True)]
    )

    # 2. Thông tin dạy bù
    makeup_date = fields.Date(string='Ngày dạy bù')
    makeup_time_slot_id = fields.Many2one('vus.time.slot', string='Ca dạy bù')

    # Danh sách giáo viên gợi ý rảnh ca này để dạy thay
    eligible_substitute_ids = fields.Many2many(
        'res.partner', 
        compute='_compute_eligible_substitutes', 
        string='Giáo viên rảnh phù hợp'
    )

    @api.depends('class_id', 'date')
    def _compute_eligible_substitutes(self):
        for rec in self:
            if rec.class_id and rec.class_id.time_slot_id:
                # Tìm các giáo viên đăng ký ca học này trong kỳ học của lớp
                term = rec.class_id.term_id
                time_slot = rec.class_id.time_slot_id
                
                domain = [('state', '=', 'approved')]
                if term:
                    domain.append(('term_id', '=', term.id))
                if time_slot:
                    domain.append(('time_slot_ids', 'in', time_slot.id))
                
                registrations = self.env['vus.teacher.registration'].search(domain)
                teachers = registrations.mapped('teacher_id')
                
                # Loại trừ chính giáo viên vắng
                rec.eligible_substitute_ids = teachers.filtered(lambda t: t.id != rec.leave_id.teacher_id.id)
            else:
                rec.eligible_substitute_ids = self.env['res.partner'].search([('is_teacher', '=', True)])

    def button_confirm_substitute(self):
        self.ensure_one()
        if not self.substitute_teacher_id:
            raise ValidationError("Vui lòng chọn giáo viên dạy thay trước khi xác nhận!")
        
        self.state = 'substituted'

        # Cập nhật giáo viên trực tiếp trên Buổi học chi tiết (Class Session) để hiển thị lịch Calendar chính xác
        if self.session_id:
            self.session_id.write({'teacher_id': self.substitute_teacher_id.id})

        # Tìm xem bảng điểm danh của ngày học hôm đó đã tồn tại chưa để tự động cập nhật
        sheet = self.env['vus.attendance.sheet'].search([
            ('class_id', '=', self.class_id.id),
            ('date', '=', self.date)
        ], limit=1)
        if sheet:
            sheet.write({'teacher_id': self.substitute_teacher_id.id})

    def button_confirm_makeup(self):
        self.ensure_one()
        if not self.makeup_date or not self.makeup_time_slot_id:
            raise ValidationError("Vui lòng chọn ngày dạy bù và ca dạy bù trước khi xác nhận!")
        
        if self.makeup_date <= self.date:
            raise ValidationError("Ngày dạy bù phải sau ngày báo vắng!")
            
        self.state = 'rescheduled'

        # Cập nhật ngày học trực tiếp trên Buổi học chi tiết để cập nhật lịch Calendar
        if self.session_id:
            self.session_id.write({
                'date': self.makeup_date
            })

        # Tạo tự động bảng điểm danh cho buổi học bù
        existing_sheets = self.env['vus.attendance.sheet'].search([
            ('class_id', '=', self.class_id.id)
        ])
        session_num = len(existing_sheets) + 1

        makeup_sheet = self.env['vus.attendance.sheet'].create({
            'class_id': self.class_id.id,
            'date': self.makeup_date,
            'session_number': session_num,
            'session': f"Học bù (Thay thế cho buổi ngày {self.date.strftime('%d/%m/%Y')})",
            'state': 'draft'
        })
        
        # Liên kết bảng điểm danh mới với session
        if self.session_id:
            self.session_id.write({'attendance_sheet_id': makeup_sheet.id})
            
        makeup_sheet.action_load_students()
