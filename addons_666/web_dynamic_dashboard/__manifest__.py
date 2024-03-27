# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Web Dynamic Dashboard',
    'category': 'Tools',
    'summary': """
        Odoo Web Dynamic Dashboard""",

    'description': """
        Odoo Web Dynamic Dashboard
    """,
    'license': 'OPL-1',
    'price': 70.00,
    'currency': 'EUR',
    'author': 'Odoo BI',
    'version': '12.0.2.0.1',
    'support': 'odoobusinessintelligence@gmail.com',
    'depends': ['web', 'account', 'sale', 'purchase', 'stock'],
    'data': [
        'views/web_dashboard_templates.xml',
        'views/views.xml',
        'security/ir.model.access.csv',
        'views/dashboard_datas.xml',
    ],
    'qweb': [
        'static/src/xml/web_dashboard.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'application': True,
    'auto_install': False,
    'live_test_url': 'http://139.162.40.148:8069'
}