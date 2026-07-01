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

    def action_start(self):
        self.state = 'running'

    def action_complete(self):
        self.state = 'completed'

    def action_cancel(self):
        self.state = 'cancelled'
