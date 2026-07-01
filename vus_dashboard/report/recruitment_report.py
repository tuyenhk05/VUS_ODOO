# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

class VusRecruitmentReport(models.Model):
    _name = 'vus.recruitment.report'
    _description = 'Báo cáo Tuyển sinh & Marketing VUS'
    _auto = False
    _order = 'date desc'

    date = fields.Date(string='Ngày ghi nhận', readonly=True)
    campaign_id = fields.Many2one('vus.marketing.campaign', string='Chiến dịch Marketing', readonly=True)
    course_id = fields.Many2one('vus.course', string='Khóa học', readonly=True)
    lead_id = fields.Many2one('crm.lead', string='Lead CRM', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Khách hàng/Học viên', readonly=True)
    test_line_id = fields.Many2one('vus.placement.test.line', string='Kết quả thi', readonly=True)
    enrollment_id = fields.Many2one('vus.enrollment', string='Phiếu ghi danh', readonly=True)
    
    lead_count = fields.Integer(string='Số lượng Lead', readonly=True)
    test_count = fields.Integer(string='Lượt thi đầu vào', readonly=True)
    enrollment_count = fields.Integer(string='Lượt ghi danh', readonly=True)
    
    revenue = fields.Float(string='Doanh thu tuyển sinh', readonly=True)
    total_score = fields.Float(string='Điểm kiểm tra đầu vào', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW vus_recruitment_report AS (
                SELECT 
                    l.id * 1000 + 1 AS id,
                    l.create_date::date AS date,
                    l.vus_campaign_id AS campaign_id,
                    NULL::integer AS course_id,
                    l.id AS lead_id,
                    l.partner_id AS partner_id,
                    NULL::integer AS test_line_id,
                    NULL::integer AS enrollment_id,
                    1 AS lead_count,
                    0 AS test_count,
                    0 AS enrollment_count,
                    0.0 AS revenue,
                    0.0 AS total_score
                FROM crm_lead l

                UNION ALL

                SELECT 
                    pt.id * 1000 + 2 AS id,
                    pt.create_date::date AS date,
                    (SELECT vus_campaign_id FROM crm_lead WHERE partner_id = pt.partner_id LIMIT 1) AS campaign_id,
                    pt.recommended_course_id AS course_id,
                    (SELECT id FROM crm_lead WHERE partner_id = pt.partner_id LIMIT 1) AS lead_id,
                    pt.partner_id AS partner_id,
                    pt.id AS test_line_id,
                    NULL::integer AS enrollment_id,
                    0 AS lead_count,
                    1 AS test_count,
                    0 AS enrollment_count,
                    0.0 AS revenue,
                    pt.total_score AS total_score
                FROM vus_placement_test_line pt

                UNION ALL

                SELECT 
                    e.id * 1000 + 3 AS id,
                    e.enrollment_date AS date,
                    (SELECT vus_campaign_id FROM crm_lead WHERE partner_id = e.student_id LIMIT 1) AS campaign_id,
                    e.course_id AS course_id,
                    (SELECT id FROM crm_lead WHERE partner_id = e.student_id LIMIT 1) AS lead_id,
                    e.student_id AS partner_id,
                    NULL::integer AS test_line_id,
                    e.id AS enrollment_id,
                    0 AS lead_count,
                    0 AS test_count,
                    1 AS enrollment_count,
                    e.amount AS revenue,
                    0.0 AS total_score
                FROM vus_enrollment e
            )
        """)
