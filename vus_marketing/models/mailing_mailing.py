# -*- coding: utf-8 -*-
from odoo import models, fields

class MailingMailing(models.Model):
    _inherit = 'mailing.mailing'

    vus_campaign_id = fields.Many2one(
        'vus.marketing.campaign',
        string='Chiến dịch VUS',
        help='Liên kết đợt Email Marketing này với Chiến dịch VUS tương ứng'
    )
