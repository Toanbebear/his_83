# -*- encoding: utf-8 -*-


{
    "name": "Report Pdf Print",
    "version": "1.0",
    "depends": ["web"],
    "author": "Daniel Yang",
    'website': 'http://www.odoo.com',
    "category": "web",
    "description": """
    Print PDF report directly from Print.js.
    Notice: Only works with pdf reports.
    """,
    "data": [
        'views/assets.xml',
    ],
    "init_xml": [],
    'update_xml': [],
    'demo_xml': [],
    "qweb": [
    ],
    
    'installable': True,
    'active': False,
}