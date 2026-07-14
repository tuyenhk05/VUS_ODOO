# -*- coding: utf-8 -*-
from odoo import models, fields, api

class VusMarketingCampaign(models.Model):
    _name = 'vus.marketing.campaign'
    _description = 'Chiến dịch Marketing VUS'
    _order = 'start_date desc, name'

    name = fields.Char(string='Tên chiến dịch', required=True)
    code = fields.Char(string='Mã chiến dịch', required=True, copy=False)
    
    start_date = fields.Date(string='Ngày bắt đầu')
    end_date = fields.Date(string='Ngày kết thúc')
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    budget = fields.Monetary(string='Ngân sách dự kiến', currency_field='currency_id')
    actual_cost = fields.Monetary(string='Chi phí thực tế', currency_field='currency_id')
    
    target_leads = fields.Integer(string='Chỉ tiêu Lead', default=100)
    
    channel_ids = fields.Many2many('vus.marketing.channel', string='Kênh Marketing')
    audience_ids = fields.Many2many('vus.marketing.audience', string='Đối tượng hướng đến')
    
    lead_ids = fields.One2many('crm.lead', 'vus_campaign_id', string='Danh sách Lead')
    
    lead_count = fields.Integer(
        string='Số Lead thực tế', 
        compute='_compute_lead_count', 
        store=True
    )
    conversion_count = fields.Integer(
        string='Số học viên chuyển đổi', 
        compute='_compute_conversion_count', 
        store=True
    )
    conversion_rate = fields.Float(
        string='Tỷ lệ chuyển đổi (%)', 
        compute='_compute_conversion_rate', 
        store=True
    )

    # Các chỉ số hiệu suất hiệu quả Marketing vừa thêm
    cost_per_lead = fields.Monetary(
        string='Chi phí/Lead', 
        compute='_compute_cost_per_lead', 
        currency_field='currency_id',
        store=True
    )
    total_revenue = fields.Monetary(
        string='Doanh thu mang lại', 
        compute='_compute_total_revenue', 
        currency_field='currency_id',
        store=True
    )
    roi = fields.Float(
        string='Chỉ số ROI (%)', 
        compute='_compute_roi', 
        store=True
    )
    
    mailing_ids = fields.One2many(
        'mailing.mailing', 
        'vus_campaign_id', 
        string='Chiến dịch Email Marketing'
    )
    email_sent = fields.Integer(
        string='Tổng email gửi', 
        compute='_compute_email_stats', 
        store=True
    )
    email_opened = fields.Integer(
        string='Email đã mở', 
        compute='_compute_email_stats', 
        store=True
    )
    email_clicked = fields.Integer(
        string='Email đã nhấp link', 
        compute='_compute_email_stats', 
        store=True
    )
    email_open_rate = fields.Float(
        string='Tỷ lệ mở (%)', 
        compute='_compute_email_stats', 
        store=True
    )
    email_click_rate = fields.Float(
        string='Tỷ lệ nhấp (%)', 
        compute='_compute_email_stats', 
        store=True
    )

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('running', 'Đang chạy'),
        ('completed', 'Đã kết thúc'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', required=True)
    
    description = fields.Html(string='Mô tả chi tiết')

    @api.depends('lead_ids')
    def _compute_lead_count(self):
        for rec in self:
            rec.lead_count = len(rec.lead_ids)

    @api.depends('lead_ids.partner_id.is_student')
    def _compute_conversion_count(self):
        for rec in self:
            rec.conversion_count = len(rec.lead_ids.filtered(lambda l: l.partner_id and l.partner_id.is_student))

    @api.depends('lead_count', 'conversion_count')
    def _compute_conversion_rate(self):
        for rec in self:
            if rec.lead_count > 0:
                rec.conversion_rate = (rec.conversion_count / rec.lead_count) * 100.0
            else:
                rec.conversion_rate = 0.0

    @api.depends('actual_cost', 'lead_count')
    def _compute_cost_per_lead(self):
        for rec in self:
            if rec.lead_count > 0:
                rec.cost_per_lead = rec.actual_cost / rec.lead_count
            else:
                rec.cost_per_lead = 0.0

    @api.depends('lead_ids.partner_id', 'lead_ids.partner_id.is_student')
    def _compute_total_revenue(self):
        for rec in self:
            partners = rec.lead_ids.mapped('partner_id').filtered(lambda p: p.is_student)
            if partners:
                # Tìm các phiếu ghi danh đã thanh toán của học viên
                enrollments = self.env['vus.enrollment'].search([
                    ('student_id', 'in', partners.ids),
                    ('state', '=', 'paid')
                ])
                rec.total_revenue = sum(enrollments.mapped('amount'))
            else:
                rec.total_revenue = 0.0

    @api.depends('total_revenue', 'actual_cost')
    def _compute_roi(self):
        for rec in self:
            if rec.actual_cost > 0:
                rec.roi = ((rec.total_revenue - rec.actual_cost) / rec.actual_cost) * 100.0
            else:
                rec.roi = 0.0

    @api.depends('mailing_ids.sent', 'mailing_ids.opened', 'mailing_ids.clicked')
    def _compute_email_stats(self):
        for rec in self:
            mailings = rec.mailing_ids
            sent = sum(mailings.mapped('sent'))
            opened = sum(mailings.mapped('opened'))
            clicked = sum(mailings.mapped('clicked'))
            rec.email_sent = sent
            rec.email_opened = opened
            rec.email_clicked = clicked
            rec.email_open_rate = (opened / sent * 100) if sent > 0 else 0.0
            rec.email_click_rate = (clicked / sent * 100) if sent > 0 else 0.0

    def action_start(self):
        self.state = 'running'

    def action_complete(self):
        self.state = 'completed'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_create_targeted_email(self):
        self.ensure_one()
        if not self.audience_ids:
            from odoo.exceptions import UserError
            raise UserError("Vui lòng cấu hình ít nhất một Đối tượng hướng đến cho chiến dịch này!")
        
        partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        if not partner_model:
            from odoo.exceptions import UserError
            raise UserError("Hệ thống không tìm thấy mô hình res.partner!")
            
        mailing_vals = {
            'subject': f"[VUS] Thông tin chiến dịch: {self.name}",
            'vus_campaign_id': self.id,
            'mailing_model_id': partner_model.id,
            'mailing_domain': str([('marketing_audience_ids', 'in', self.audience_ids.ids)]),
            'reply_to_mode': 'update',
            'mailing_type': 'mail',
            'state': 'draft'
        }
        new_mailing = self.env['mailing.mailing'].create(mailing_vals)
        
        return {
            'name': 'Thiết kế Email Marketing',
            'type': 'ir.actions.act_window',
            'res_model': 'mailing.mailing',
            'view_mode': 'form',
            'res_id': new_mailing.id,
            'target': 'current',
        }

class VusMarketingChannel(models.Model):
    _name = 'vus.marketing.channel'
    _description = 'Kênh Marketing VUS'
    _rec_name = 'name'

    name = fields.Char(string='Tên kênh', required=True)
    code = fields.Char(string='Mã kênh')

class VusMarketingAudience(models.Model):
    _name = 'vus.marketing.audience'
    _description = 'Đối tượng mục tiêu VUS'
    _rec_name = 'name'

    name = fields.Char(string='Tên đối tượng', required=True)
    description = fields.Char(string='Mô tả')
