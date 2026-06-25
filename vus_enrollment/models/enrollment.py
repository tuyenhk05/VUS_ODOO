# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

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
    amount = fields.Float(
        string='Số tiền phải nộp',
        compute='_compute_amount',
        store=True,
        default=0.0
    )
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã đóng tiền')
    ], string='Trạng thái', default='draft', readonly=True, copy=False)

    invoice_id = fields.Many2one(
        'account.move',
        string='Hóa đơn liên kết',
        readonly=True,
        copy=False
    )

    @api.depends('course_id')
    def _compute_amount(self):
        for record in self:
            record.amount = record.course_id.tuition_fee if record.course_id else 0.0

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

    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise UserError("Phiếu ghi danh này đã được xác nhận hoặc xử lý rồi!")
            if not record.student_id:
                raise UserError("Vui lòng chọn học viên!")
            if not record.course_id:
                raise UserError("Vui lòng chọn khóa học!")

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
                        'name': f"Học phí khóa học: {record.course_id.name} ({record.course_id.code})",
                        'price_unit': record.amount,
                        'quantity': 1.0,
                        'account_id': account.id,
                    })
                ],
            }
            invoice = self.env['account.move'].create(invoice_vals)

            # 4. Ghi nhận hóa đơn và chuyển trạng thái phiếu ghi danh sang 'confirmed'
            record.write({
                'invoice_id': invoice.id,
                'state': 'confirmed'
            })
        return True
