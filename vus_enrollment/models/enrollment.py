# -*- coding: utf-8 -*-
import re
from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

def parse_schedule_days(sched_str):
    """
    Extract set of day-of-week indices (0=Mon, 1=Tue, ..., 6=Sun) from a schedule text string.
    Safely strips out times (e.g. 18:00) and shift names (e.g. Ca 1) to avoid false matches.
    """
    if not sched_str:
        return set()
    s_lower = str(sched_str).lower()
    
    # Clean out times like 18:00, 19.30, 18h00, 8:00-9:30
    clean_text = re.sub(r'\d{1,2}\s*[:.h]\s*\d{2}', ' ', s_lower)
    # Clean out shift numbers like ca 1, ca 2
    clean_text = re.sub(r'\bca\s*\d+\b', ' ', clean_text)
    
    dows = set()
    if 'thứ 2' in clean_text or 't2' in clean_text or 'mon' in clean_text:
        dows.add(0)
    if 'thứ 3' in clean_text or 't3' in clean_text or 'tue' in clean_text:
        dows.add(1)
    if 'thứ 4' in clean_text or 't4' in clean_text or 'wed' in clean_text:
        dows.add(2)
    if 'thứ 5' in clean_text or 't5' in clean_text or 'thu' in clean_text:
        dows.add(3)
    if 'thứ 6' in clean_text or 't6' in clean_text or 'fri' in clean_text:
        dows.add(4)
    if 'thứ 7' in clean_text or 't7' in clean_text or 'sat' in clean_text:
        dows.add(5)
    if 'chủ nhật' in clean_text or 'cn' in clean_text or 'thứ 8' in clean_text or 't8' in clean_text or 'sun' in clean_text:
        dows.add(6)
        
    return dows

def parse_schedule_time_range(sched_str):
    """
    Extract start and end minutes from midnight from a schedule text string.
    Returns (start_minutes, end_minutes). If no valid time pair found, returns (0, 1440).
    """
    if not sched_str:
        return (0, 1440)
    
    times = re.findall(r'(\d{1,2})[\s:.h]+(\d{2})', str(sched_str))
    if len(times) >= 2:
        h1, m1 = int(times[0][0]), int(times[0][1])
        h2, m2 = int(times[1][0]), int(times[1][1])
        start_min = h1 * 60 + m1
        end_min = h2 * 60 + m2
        if 0 <= start_min < end_min <= 1440:
            return (start_min, end_min)
            
    return (0, 1440)

def check_classes_overlap(cls1, cls2):
    """
    Check if two vus.class records overlap in schedule.
    Returns (is_conflict, reason_string)
    """
    if not cls1 or not cls2 or cls1.id == cls2.id:
        return False, ''

    # 1. Date Range Overlap Check
    start1 = cls1.start_date
    end1 = cls1.end_date or (start1 + timedelta(days=90)) if start1 else False
    start2 = cls2.start_date
    end2 = cls2.end_date or (start2 + timedelta(days=90)) if start2 else False

    if start1 and start2 and end1 and end2:
        if start1 > end2 or end1 < start2:
            return False, '' # Classes run during different date periods

    # 2. Days of Week Check
    days1 = set()
    if hasattr(cls1, 'time_slot_id') and cls1.time_slot_id and hasattr(cls1.time_slot_id, 'days_group') and cls1.time_slot_id.days_group:
        dg = cls1.time_slot_id.days_group
        if dg == 'mwf': days1 = {0, 2, 4}
        elif dg == 'tts': days1 = {1, 3, 5}
        elif dg == 'ss': days1 = {5, 6}

    if not days1:
        s1 = cls1.schedule or ''
        days1 = parse_schedule_days(s1)

    days2 = set()
    if hasattr(cls2, 'time_slot_id') and cls2.time_slot_id and hasattr(cls2.time_slot_id, 'days_group') and cls2.time_slot_id.days_group:
        dg = cls2.time_slot_id.days_group
        if dg == 'mwf': days2 = {0, 2, 4}
        elif dg == 'tts': days2 = {1, 3, 5}
        elif dg == 'ss': days2 = {5, 6}

    if not days2:
        s2 = cls2.schedule or ''
        days2 = parse_schedule_days(s2)

    # If either class does not have days specified (schedule unassigned), no schedule conflict
    if not days1 or not days2:
        return False, ''

    common_days = days1 & days2
    if not common_days:
        return False, '' # No common day of week!

    # 3. Time Slot Range Check
    s1_text = cls1.schedule or (cls1.time_slot_id.name if hasattr(cls1, 'time_slot_id') and cls1.time_slot_id else '')
    s2_text = cls2.schedule or (cls2.time_slot_id.name if hasattr(cls2, 'time_slot_id') and cls2.time_slot_id else '')

    has_t1 = bool(s1_text and re.search(r'\d{1,2}[\s:.h]+\d{2}', str(s1_text)))
    has_t2 = bool(s2_text and re.search(r'\d{1,2}[\s:.h]+\d{2}', str(s2_text)))

    if has_t1 and has_t2:
        t1_start, t1_end = parse_schedule_time_range(s1_text)
        t2_start, t2_end = parse_schedule_time_range(s2_text)
        is_time_overlap = max(t1_start, t2_start) < min(t1_end, t2_end)
        if is_time_overlap:
            return True, f"Bị trùng lịch học với lớp '{cls2.class_name}'"
        return False, ''

    return True, f"Bị trùng lịch học với lớp '{cls2.class_name}'"

class VusEnrollment(models.Model):
    _name = 'vus.enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
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
        domain="[('course_id', '=', course_id), ('state', '=', 'opened')]"
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
        ('paid', 'Đã thanh toán'),
        ('cancel', 'Đã hủy')
    ], string='Trạng thái', compute='_compute_state', store=True, default='draft')

    @api.depends('invoice_id.payment_state', 'invoice_id.state')
    def _compute_state(self):
        for record in self:
            if record.state == 'cancel':
                continue
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
    is_near_due = fields.Boolean(
        string='Gần/Quá hạn nộp học phí',
        compute='_compute_is_near_due',
        store=True,
        help='Hóa đơn ở trạng thái Chờ thanh toán và có hạn đóng <= 3 ngày hoặc đã quá hạn'
    )

    @api.depends('state', 'invoice_id.invoice_date_due', 'enrollment_date', 'class_id.start_date')
    def _compute_is_near_due(self):
        from datetime import timedelta
        today = fields.Date.today()
        for rec in self:
            if rec.state == 'confirmed':
                due = False
                if rec.invoice_id and rec.invoice_id.invoice_date_due:
                    due = rec.invoice_id.invoice_date_due
                elif rec.class_id and rec.class_id.start_date:
                    due = rec.class_id.start_date
                elif rec.enrollment_date:
                    due = rec.enrollment_date + timedelta(days=7)
                
                if due and (due - today).days <= 3:
                    rec.is_near_due = True
                else:
                    rec.is_near_due = False
            else:
                rec.is_near_due = False

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
                # 1. Kiểm tra hạn đóng/khóa lớp học (closing_date)
                if record.class_id.closing_date and fields.Date.today() > record.class_id.closing_date:
                    raise ValidationError(
                        f"Không thể ghi danh vào lớp '{record.class_id.class_name}' "
                        f"vì lớp đã đóng/khóa ghi danh (Hạn đóng lớp là ngày {record.class_id.closing_date.strftime('%d/%m/%Y')})!"
                    )
                # 2. Kiểm tra số buổi đã học
                completed_sheets = self.env['vus.attendance.sheet'].search_count([
                    ('class_id', '=', record.class_id.id),
                    ('state', '=', 'done')
                ])
                if completed_sheets > 3:
                    raise ValidationError(
                        f"Không thể ghi danh vào lớp '{record.class_id.class_name}' "
                        f"vì lớp đã học quá 3 buổi (đã học xong {completed_sheets} buổi)!"
                    )

    @api.constrains('student_id', 'class_id', 'state')
    def _check_student_schedule_conflict(self):
        for record in self:
            if not record.student_id or not record.class_id or record.state not in ['draft', 'confirmed', 'paid']:
                continue

            target_class = record.class_id

            # Search existing non-cancelled enrollments for this student
            other_enrollments = self.search([
                ('id', '!=', record.id),
                ('student_id', '=', record.student_id.id),
                ('state', 'in', ['draft', 'confirmed', 'paid']),
                ('class_id', '!=', False)
            ])

            for other_enr in other_enrollments:
                other_class = other_enr.class_id
                if not other_class or other_class.id == target_class.id:
                    continue

                is_conflict, reason = check_classes_overlap(target_class, other_class)
                if is_conflict:
                    raise ValidationError(
                        f"⚠️ Không thể đăng ký lớp '{target_class.class_name}' ({target_class.schedule or ''}) "
                        f"vì bị TRÙNG LỊCH HỌC với lớp '{other_class.class_name}' ({other_class.schedule or ''}) "
                        f"mà học viên {record.student_id.name} đã đăng ký!"
                    )

    def action_confirm_bulk(self):
        """Action for managers to bulk confirm multiple selected draft enrollments."""
        draft_enrollments = self.filtered(lambda e: e.state == 'draft')
        if not draft_enrollments:
            raise UserError("Không có phiếu ghi danh nháp nào được chọn để duyệt!")
        
        count = 0
        for record in draft_enrollments:
            record.action_confirm()
            count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Duyệt phiếu ghi danh',
                'message': f'Đã xác nhận và tạo hóa đơn thành công cho {count} phiếu ghi danh!',
                'type': 'success',
                'sticky': False,
            }
        }

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

    new_enrollment_count = fields.Integer(
        string='Đăng ký mới cần duyệt',
        compute='_compute_enrollment_counts',
        help='Số phiếu ghi danh ở trạng thái Nháp từ Portal cần xác nhận'
    )
    near_due_payment_count = fields.Integer(
        string='Hóa đơn sắp/quá hạn',
        compute='_compute_enrollment_counts',
        help='Số phiếu ghi danh chờ đóng phí có hạn nộp <= 3 ngày hoặc quá hạn'
    )

    @api.depends('enrollment_ids', 'enrollment_ids.state', 'enrollment_ids.is_near_due')
    def _compute_enrollment_counts(self):
        for rec in self:
            rec.new_enrollment_count = len(rec.enrollment_ids.filtered(lambda e: e.state == 'draft'))
            rec.near_due_payment_count = len(rec.enrollment_ids.filtered(lambda e: e.is_near_due))

    @api.depends('enrollment_ids', 'enrollment_ids.state')
    def _compute_student_count(self):
        for rec in self:
            rec.current_student_count = len(rec.enrollment_ids.filtered(lambda e: e.state != 'cancel'))

    @api.depends('max_students', 'current_student_count')
    def _compute_available_seats(self):
        for rec in self:
            rec.available_seats = rec.max_students - rec.current_student_count
            if rec.available_seats <= 0 and rec.state == 'opened':
                rec.state = 'full'

    def action_view_new_enrollments(self):
        self.ensure_one()
        return {
            'name': f'Đăng ký mới cần duyệt - Lớp {self.class_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'vus.enrollment',
            'view_mode': 'tree,form',
            'domain': [('class_id', '=', self.id), ('state', '=', 'draft')],
            'context': {'default_class_id': self.id, 'default_state': 'draft'},
            'target': 'current',
        }

    def action_view_near_due_enrollments(self):
        self.ensure_one()
        return {
            'name': f'Hóa đơn gần/quá hạn - Lớp {self.class_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'vus.enrollment',
            'view_mode': 'tree,form',
            'domain': [('class_id', '=', self.id), ('is_near_due', '=', True)],
            'context': {'default_class_id': self.id},
            'target': 'current',
        }
