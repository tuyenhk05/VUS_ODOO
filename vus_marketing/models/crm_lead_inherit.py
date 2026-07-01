# -*- coding: utf-8 -*-
from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    vus_campaign_id = fields.Many2one(
        'vus.marketing.campaign', 
        string='Chiến dịch VUS',
        help='Chọn chiến dịch Marketing VUS tùy chỉnh cho Lead này'
    )
    lead_source = fields.Selection([
        ('web', 'Website VUS'),
        ('facebook', 'Facebook Fanpage'),
        ('referral', 'Học viên giới thiệu'),
        ('direct', 'Trực tiếp tại trung tâm'),
        ('event', 'Sự kiện / Hội thảo'),
        ('other', 'Nguồn khác')
    ], string='Nguồn khách hàng', default='web')
    
    follow_up_notes = fields.Text(string='Ghi chú chăm sóc')
