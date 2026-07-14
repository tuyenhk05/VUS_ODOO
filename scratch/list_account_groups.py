# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

config_file = r"C:\Program Files\Odoo 17.0.20260615\server\odoo.conf"
odoo.tools.config.parse_config(['-c', config_file])

db_name = 'Vus_odoo'
registry = odoo.registry(db_name)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Tìm kiếm toàn bộ các nhóm quyền thuộc module account
    groups = env['res.groups'].search([
        ('implied_ids', '!=', False)
    ])
    
    print("\n--- TOÀN BỘ CÁC NHÓM QUYỀN ACCOUNT ---")
    for g in env['res.groups'].search([]):
        xml_ids = g.get_external_id()
        xml_id = xml_ids[g.id] if g.id in xml_ids else ''
        if 'account' in xml_id:
            print(f"Group Name: {g.name} | XML ID: {xml_id}")
