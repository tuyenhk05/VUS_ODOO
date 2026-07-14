# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class VusEnrollment(models.Model):
    _name = 'vus.enrollment'
    _description = 'Phiếu ghi danh học viên VUS'
    _order = 'id desc'

    name = fields.Char(
        string='Mã phiếu ghi danh',
        required=True,
        readonly=True,
        copy=False,
        default='New'
    )

    @api.depends('name', 'student_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.student_id.name:
                record.display_name = record.student_id.name
            else:
                record.display_name = record.name or 'New'
    student_id = fields.Many2one(
        'res.partner',
        string='Học viên',
        domain="[('is_student', '=', True)]",
        required=True
    )
    course_id = fields.Many2one(
        'vus.course',
        string='Khóa học đăng ký',
        required=True
    )
    class_id = fields.Many2one(
        'vus.class',
        string='Lớp học đăng ký',
        domain="[('course_id', '=', course_id)]"
    )
    enrollment_date = fields.Date(
        string='Ngày ghi danh',
        default=fields.Date.today,
        required=True
    )
    amount = fields.Float(
        string='Số tiền phải nộp',
        compute='_compute_amount',
        store=True,
        default=0.0
    )
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Chờ thanh toán'),
        ('paid', 'Đã thanh toán')
    ], string='Trạng thái', compute='_compute_state', store=True, default='draft')

    @api.depends('invoice_id.payment_state', 'invoice_id.state')
    def _compute_state(self):
        for record in self:
            if record.invoice_id:
                if record.invoice_id.payment_state in ['paid', 'in_payment']:
                    record.state = 'paid'
                elif record.invoice_id.state == 'posted':
                    record.state = 'confirmed'
                else:
                    record.state = 'draft'
            else:
                if not record.state:
                    record.state = 'draft'
            
            # Logic: Tạo hồ sơ học viên (Đánh dấu chính thức) khi đã thanh toán
            if record.state == 'paid' and record.student_id:
                record.student_id.write({
                    'is_student': True,
                    'comment': f"Học viên chính thức từ phiếu ghi danh {record.name}"
                })

    invoice_id = fields.Many2one(
        'account.move',
        string='Hóa đơn liên kết',
        readonly=True,
        copy=False
    )

    @api.depends('course_id')
    def _compute_amount(self):
        for record in self:
            record.amount = record.course_id.base_price if record.course_id else 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                seq = self.env['ir.sequence'].next_by_code('vus.enrollment')
                if seq:
                    vals['name'] = seq
                else:
                    # Tự sinh mã định danh nếu chưa tạo sequence XML
                    year = fields.Date.context_today(self).strftime('%Y')
                    last_enrollment = self.env['vus.enrollment'].search([], order='id desc', limit=1)
                    next_id = (last_enrollment.id + 1) if last_enrollment else 1
                    vals['name'] = f"VUS/ENR/{year}/{next_id:05d}"
        return super(VusEnrollment, self).create(vals_list)

    @api.constrains('class_id', 'state')
    def _check_class_capacity(self):
        for record in self:
            if record.class_id and record.state in ['confirmed', 'paid']:
                # Đếm số học viên thực tế khác phiếu này
                current_count = len(record.class_id.enrollment_ids.filtered(lambda e: e.id != record.id and e.state in ['confirmed', 'paid']))
                if current_count >= record.class_id.max_students:
                    raise ValidationError(f"Lớp {record.class_id.class_name} đã đạt giới hạn sĩ số tối đa ({record.class_id.max_students} học viên)!")

    @api.constrains('class_id')
    def _check_class_registration_deadline(self):
        # Bỏ qua nếu chạy bằng quyền superuser (migration, script nạp dữ liệu mẫu)
        if self.env.su:
            return
        for record in self:
            if record.class_id:
                completed_sheets = self.env['vus.attendance.sheet'].search_count([
                    ('class_id', '=', record.class_id.id),
                    ('state', '=', 'done')
                ])
                if completed_sheets > 3:
                    raise ValidationError(
                        f"Không thể ghi danh vào lớp '{record.class_id.class_name}' "
                        f"vì lớp đã học quá 3 buổi (đã học xong {completed_sheets} buổi)!"
                    )

    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise UserError("Phiếu ghi danh này đã được xác nhận hoặc xử lý rồi!")
            if not record.student_id:
                raise UserError("Vui lòng chọn học viên!")
            if not record.course_id:
                raise UserError("Vui lòng chọn khóa học!")
            if not record.class_id:
                raise UserError("Vui lòng chọn lớp học trước khi xác nhận ghi danh và thanh toán!")

            # 1. Tìm Nhật ký bán hàng (Sales Journal)
            journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
            if not journal:
                raise UserError("Hệ thống chưa cấu hình Nhật ký bán hàng (Sales Journal)!")

            # 2. Tìm tài khoản doanh thu (Income Account) cho dòng hóa đơn
            account = journal.default_account_id
            if not account:
                account = self.env['account.account'].search([
                    ('account_type', '=', 'income'),
                    ('deprecated', '=', False)
                ], limit=1)
            if not account:
                raise UserError("Hệ thống chưa cấu hình tài khoản doanh thu (Income Account)!")

            # 3. Tạo hóa đơn (account.move)
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': record.student_id.id,
                'journal_id': journal.id,
                'invoice_date': fields.Date.context_today(record),
                'invoice_line_ids': [
                    (0, 0, {
                        'name': f"Học phí khóa học: {record.course_id.course_name} ({record.course_id.code})",
                        'price_unit': record.amount,
                        'quantity': 1.0,
                        'account_id': account.id,
                    })
                ],
            }
            invoice = self.env['account.move'].create(invoice_vals)
            # Tự động xác nhận/vào sổ hóa đơn để đưa nó về trạng thái 'posted'
            invoice.action_post()

            # 4. Ghi nhận hóa đơn và chuyển trạng thái phiếu ghi danh sang 'confirmed'
            record.write({
                'invoice_id': invoice.id,
                'state': 'confirmed'
            })
        
        # Nếu xác nhận đơn lẻ, tự động chuyển hướng trực tiếp đến hóa đơn liên kết để giáo vụ xử lý thanh toán nhanh
        if len(self) == 1:
            return self.action_view_invoice()
        return True

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'name': 'Hóa đơn học phí',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
        }

class VusClassInherit(models.Model):
    _inherit = 'vus.class'

    enrollment_ids = fields.One2many('vus.enrollment', 'class_id', string='Danh sách ghi danh')
    current_student_count = fields.Integer(
        string='Số học viên hiện tại',
        compute='_compute_student_count',
        store=True
    )
    available_seats = fields.Integer(
        string='Chỗ trống',
        compute='_compute_available_seats',
        store=True
    )

    @api.depends('enrollment_ids')
    def _compute_student_count(self):
        for rec in self:
            rec.current_student_count = len(rec.enrollment_ids)

    @api.depends('max_students', 'current_student_count')
    def _compute_available_seats(self):
        for rec in self:
            rec.available_seats = rec.max_students - rec.current_student_count
            # Tự động chuyển trạng thái nếu đầy
            if rec.available_seats <= 0 and rec.state == 'opened':
                rec.state = 'full'
