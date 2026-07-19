# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VusClass(models.Model):
    _name = 'vus.class'
    _description = 'Lớp học tại VUS'
    _inherit = ['mail.thread']
    _rec_name = 'class_name'
    _order = 'start_date desc'

    class_name = fields.Char(string='Tên lớp', required=True)
    class_code = fields.Char(string='Mã lớp', required=True, readonly=True, copy=False, default='New')
    
    course_id = fields.Many2one('vus.course', string='Khóa học', required=True)
    course_level = fields.Selection(related='course_id.level', string='Trình độ', store=True)
    
    teacher_id = fields.Many2one(
        'res.partner',
        string='Giảng viên',
        domain=[('is_teacher', '=', True)],
        help='Chỉ chọn những người đã được đánh dấu là Giảng viên'
    )
    teacher_name = fields.Char(related='teacher_id.name', string='Tên giảng viên', store=True)
    
    schedule = fields.Char(string='Lịch học', help='VD: 18:30 - 20:30 Thứ 3,5,7')
    start_date = fields.Date(string='Ngày khai giảng', required=True)
    end_date = fields.Date(string='Ngày kết thúc')
    classroom = fields.Char(string='Phòng học')
    
    max_students = fields.Integer(string='Sĩ số tối đa', default=20, required=True)
    payment_deadline = fields.Date(string='Hạn đóng học phí')
    state = fields.Selection([
        ('draft', 'Chờ mở'),
        ('opened', 'Đang mở'),
        ('full', 'Đã đầy'),
        ('closed', 'Đã kết thúc'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', required=True)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('class_code', 'New') == 'New':
                course_id = vals.get('course_id')
                if course_id:
                    course = self.env['vus.course'].browse(course_id)
                    course_code = course.code or 'CLASS'
                else:
                    course_code = 'CLASS'
                year = fields.Date.today().strftime('%y')
                last_class = self.search([('class_code', 'like', f"{course_code}-{year}-%")], order='id desc', limit=1)
                if last_class and last_class.class_code:
                    try:
                        last_seq = int(last_class.class_code.split('-')[-1])
                        next_seq = last_seq + 1
                    except:
                        next_seq = 1
                else:
                    next_seq = 1
                vals['class_code'] = f"{course_code}-{year}-{next_seq:03d}"
        return super(VusClass, self).create(vals_list)

    def action_open_class(self):
        self.state = 'opened'

    def action_close_class(self):
        self.state = 'closed'

    def action_cancel_class(self):
        self.state = 'cancelled'

    def action_set_draft(self):
        self.state = 'draft'

    def action_remove_unpaid_students(self):
        self.ensure_one()
        unpaid_enrollments = self.env['vus.enrollment'].search([
            ('class_id', '=', self.id),
            ('state', 'in', ['draft', 'confirmed'])
        ])
        if not unpaid_enrollments:
            raise ValidationError("Không có học viên chưa đóng học phí nào trong lớp này!")
        
        # Gỡ bỏ lớp học khỏi các phiếu ghi danh chưa thanh toán
        unpaid_enrollments.write({'class_id': False})
        
        # Nếu lớp ở trạng thái 'full', tự động cập nhật lại trạng thái dựa trên số học viên hiện tại
        if self.state == 'full':
            self.state = 'opened'
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': f"Đã hủy xếp lớp cho {len(unpaid_enrollments)} học viên chưa hoàn thành học phí.",
                'type': 'success',
                'sticky': False,
            }
        }

    def action_duplicate_class(self):
        for rec in self:
            rec.copy({
                'class_name': rec.class_name + ' (Copy)',
                'class_code': rec.class_code + '_COPY',
                'state': 'draft',
            })

    def action_view_students(self):
        self.ensure_one()
        return {
            'name': 'Học viên trong lớp',
            'type': 'ir.actions.act_window',
            'res_model': 'vus.enrollment',
            'view_mode': 'tree,form',
            'domain': [('class_id', '=', self.id)],
            'context': {'default_class_id': self.id},
            'target': 'current',
        }

    @api.constrains('max_students')
    def _check_max_students(self):
        for rec in self:
            if rec.max_students < 0:
                raise ValidationError('Sĩ số tối đa không thể âm!')

    @api.constrains('class_code')
    def _check_unique_class_code(self):
        for rec in self:
            existing = self.search([('class_code', '=', rec.class_code), ('id', '!=', rec.id)])
            if existing:
                raise ValidationError(f'Mã lớp "{rec.class_code}" đã tồn tại!')

class VusCourseInherit(models.Model):
    _inherit = 'vus.course'

    class_ids = fields.One2many('vus.class', 'course_id', string='Các lớp học')
    class_count = fields.Integer(string='Số lớp', compute='_compute_class_count', store=True)

    @api.depends('class_ids')
    def _compute_class_count(self):
        for rec in self:
            rec.class_count = len(rec.class_ids)
