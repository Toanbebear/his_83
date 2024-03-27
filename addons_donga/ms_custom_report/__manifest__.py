# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MS custom report',
    'author': 'Nomed',
    'version': '1.0',
    'category': 'Report',
    'sequence': 75,
    'summary': 'Customized report that could not be generated from ms template',
    'description': "",
    'website': 'http://project.scisoftware.xyz/',
    'images': [
    ],
    'depends': ['ms_templates',
    ],
    'data': [
        'data/template_attachment.xml',
        # 'inventory/monthly_inventory.xml',
        'crm/crm_monthly.xml',
        # 'course_report/course_report.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
