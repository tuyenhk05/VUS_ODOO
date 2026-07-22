# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class VusPlacementTest(models.Model):
    _name = 'vus.placement.test'
    _description = 'Buổi kiểm tra đầu vào VUS'
    _order = 'date desc, name'

    name = fields.Char(string='Tên buổi kiểm tra', required=True)
    date = fields.Datetime(string='Ngày giờ kiểm tra', required=True, default=fields.Datetime.now)
    
    teacher_id = fields.Many2one(
        'res.partner',
        string='Giảng viên chấm thi',
        domain=[('is_teacher', '=', True)],
        required=True
    )
    classroom = fields.Char(string='Phòng thi')
    max_participants = fields.Integer(string='Sĩ số tối đa', default=15, required=True)
    
    line_ids = fields.One2many('vus.placement.test.line', 'test_id', string='Danh sách thí sinh')
    
    participant_count = fields.Integer(
        string='Số lượng thí sinh',
        compute='_compute_participant_count',
        store=True
    )
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('completed', 'Đã hoàn thành')
    ], string='Trạng thái', default='draft', required=True)

    @api.depends('line_ids')
    def _compute_participant_count(self):
        for rec in self:
            rec.participant_count = len(rec.line_ids)

    @api.constrains('max_participants')
    def _check_max_participants(self):
        for rec in self:
            if rec.max_participants <= 0:
                raise ValidationError('Sĩ số tối đa phải lớn hơn 0!')

    def action_confirm(self):
        self.state = 'confirmed'

    def action_complete(self):
        for rec in self:
            for line in rec.line_ids:
                if line.state == 'registered':
                    line.state = 'attended'
            rec.state = 'completed'


class VusPlacementTestLine(models.Model):
    _name = 'vus.placement.test.line'
    _description = 'Kết quả thi đầu vào thí sinh'
    _rec_name = 'partner_id'

    test_id = fields.Many2one('vus.placement.test', string='Buổi kiểm tra', ondelete='cascade', required=True)
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Thí sinh (Ứng viên/Học viên)',
        domain=[('is_company', '=', False)],
        required=True
    )
    
    listening_score = fields.Float(string='Điểm Nghe', default=0.0)
    reading_score = fields.Float(string='Điểm Đọc', default=0.0)
    writing_score = fields.Float(string='Điểm Viết', default=0.0)
    speaking_score = fields.Float(string='Điểm Nói', default=0.0)
    
    total_score = fields.Float(
        string='Tổng điểm',
        compute='_compute_total_score',
        store=True
    )
    
    recommended_course_id = fields.Many2one('vus.course', string='Khóa học đề xuất')
    
    state = fields.Selection([
        ('registered', 'Đã đăng ký'),
        ('attended', 'Đã tham gia'),
        ('graded', 'Đã chấm điểm'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='registered', required=True)
    
    enrollment_id = fields.Many2one(
        'vus.enrollment',
        string='Phiếu ghi danh liên kết',
        readonly=True,
        copy=False
    )

    @api.depends('listening_score', 'reading_score', 'writing_score', 'speaking_score')
    def _compute_total_score(self):
        for rec in self:
            rec.total_score = rec.listening_score + rec.reading_score + rec.writing_score + rec.speaking_score

    @api.constrains('listening_score', 'reading_score', 'writing_score', 'speaking_score')
    def _check_scores(self):
        for rec in self:
            for score in [rec.listening_score, rec.reading_score, rec.writing_score, rec.speaking_score]:
                if score < 0 or score > 100:
                    raise ValidationError('Điểm số phải nằm trong khoảng từ 0 đến 100!')

    def action_confirm_grade(self):
        for rec in self:
            rec.state = 'graded'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_create_enrollment(self):
        self.ensure_one()
        if self.enrollment_id:
            raise UserError('Thí sinh này đã có phiếu ghi danh liên kết!')
        if not self.recommended_course_id:
            raise UserError('Vui lòng chọn khóa học đề xuất trước khi tạo phiếu ghi danh!')

        # Hãy chắc chắn rằng thí sinh được đánh dấu là học viên trước khi ghi danh
        self.partner_id.write({
            'is_student': True,
        })

        # Tạo phiếu ghi danh
        enrollment_vals = {
            'student_id': self.partner_id.id,
            'course_id': self.recommended_course_id.id,
            'enrollment_date': fields.Date.today(),
            'state': 'draft',
        }
        enrollment = self.env['vus.enrollment'].create(enrollment_vals)
        self.enrollment_id = enrollment.id

        # Mở phiếu ghi danh mới tạo
        return {
            'name': 'Phiếu ghi danh học viên',
            'type': 'ir.actions.act_window',
            'res_model': 'vus.enrollment',
            'view_mode': 'form',
            'res_id': enrollment.id,
            'target': 'current',
        }
