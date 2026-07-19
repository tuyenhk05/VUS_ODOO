# -*- coding: utf-8 -*-
from odoo import models, fields, api

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


    def action_book_placement_test(self):
        self.ensure_one()
        # 1. Đảm bảo Lead được liên kết với partner học viên tiềm năng
        if not self.partner_id:
            partner_vals = {
                'name': self.partner_name or self.contact_name or self.name,
                'email': self.email_from,
                'phone': self.phone,
                'is_student': False,
                'student_status': 'potential'
            }
            partner = self.env['res.partner'].create(partner_vals)
            self.partner_id = partner.id
            
        # 2. Mở cửa sổ popup tạo dòng đăng ký thi xếp lớp vus.placement.test.line
        return {
            'name': 'Đăng ký Buổi kiểm tra xếp lớp VUS',
            'type': 'ir.actions.act_window',
            'res_model': 'vus.placement.test.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
            }
        }
