# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VusTeacherRegistration(models.Model):
    _name = 'vus.teacher.registration'
    _description = 'Đăng ký lịch dạy của giáo viên'
    _rec_name = 'teacher_id'

    term_id = fields.Many2one('vus.academic.term', string='Kỳ học', required=True)
    
    teacher_id = fields.Many2one(
        'res.partner', 
        string='Giảng viên', 
        domain=[('is_teacher', '=', True)], 
        required=True,
        default=lambda self: self.env.user.partner_id if self.env.user.has_group('vus_student.group_vus_teacher') else False
    )
    
    time_slot_ids = fields.Many2many('vus.time.slot', string='Khung giờ rảnh đăng ký')
    
    min_sessions = fields.Integer(string='Số ca tối thiểu/tháng', default=12, required=True)
    selected_sessions = fields.Integer(string='Số ca đã đăng ký', compute='_compute_selected_sessions', store=True)
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Chờ duyệt'),
        ('approved', 'Đã duyệt')
    ], string='Trạng thái', default='draft', required=True)

    # Trường kiểm tra user hiện tại có phải là giáo viên để điều khiển giao diện
    is_teacher_user = fields.Boolean(compute='_compute_is_teacher_user')

    @api.depends('teacher_id')
    def _compute_is_teacher_user(self):
        is_teacher = self.env.user.has_group('vus_student.group_vus_teacher')
        for rec in self:
            rec.is_teacher_user = is_teacher

    @api.constrains('teacher_id')
    def _check_teacher_id(self):
        for rec in self:
            if self.env.user.has_group('vus_student.group_vus_teacher') and rec.teacher_id != self.env.user.partner_id:
                raise ValidationError("Bạn chỉ có quyền đăng ký lịch dạy cho chính mình!")

    @api.constrains('term_id', 'time_slot_ids')
    def _check_registration_period(self):
        # Nếu chạy bằng quyền superuser (cron, migration, demo script), bỏ qua ràng buộc
        if self.env.su:
            return
        for rec in self:
            term = rec.term_id
            if term:
                # Nếu không phải là Giáo vụ / Quản lý, kiểm tra thời hạn và trạng thái kỳ học
                is_staff_or_manager = self.env.user.has_group('vus_student.group_vus_staff') or self.env.user.has_group('vus_student.group_vus_manager')
                if not is_staff_or_manager:
                    if term.state != 'registration':
                        raise ValidationError(
                            f"Kỳ học {term.name} hiện tại đang ở trạng thái '{dict(term._fields['state'].selection).get(term.state)}', "
                            f"không cho phép giáo viên tạo hoặc sửa phiếu đăng ký lịch rảnh!"
                        )
                    if term.registration_deadline and fields.Date.today() > term.registration_deadline:
                        raise ValidationError(
                            f"Đã quá hạn đăng ký lịch rảnh dạy cho kỳ học {term.name} "
                            f"(Hạn chót là ngày {term.registration_deadline.strftime('%d/%m/%Y')})!"
                        )

    @api.depends('time_slot_ids')
    def _compute_selected_sessions(self):
        for rec in self:
            sessions = 0
            for slot in rec.time_slot_ids:
                if slot.days_group in ['mwf', 'tts']:
                    # Ca T2-4-6 hoặc T3-5-7 có 3 buổi/tuần * 4 tuần = 12 ca/tháng
                    sessions += 3 * 4
                elif slot.days_group == 'ss':
                    # Ca T7-CN có 2 buổi/tuần * 4 tuần = 8 ca/tháng
                    sessions += 2 * 4
            rec.selected_sessions = sessions

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def action_approve(self):
        for rec in self:
            rec._check_min_sessions()
            rec.state = 'approved'

    def action_set_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.constrains('time_slot_ids', 'min_sessions', 'state')
    def _check_min_sessions(self):
        for rec in self:
            if rec.state == 'approved' and rec.selected_sessions < rec.min_sessions:
                raise ValidationError(
                    f"Giảng viên {rec.teacher_id.name} chỉ mới đăng ký {rec.selected_sessions} ca/tháng, "
                    f"chưa đạt số ca tối thiểu trong hợp đồng là {rec.min_sessions} ca/tháng!"
                )
