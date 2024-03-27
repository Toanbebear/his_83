# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Thống kê Shealth All In one',
    'sequence': 1,
    'category': 'Tools',
    'summary': """
        Các biểu đồ phân tích thống kê cho shealth_all_in_one""",

    'description': """
        Các biểu đồ phân tích thống kê cho shealth_all_in_one
    """,
    'version': '12.0.2.0.1',
    'depends': ['web_dynamic_dashboard', 'shealth_all_in_one'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_datas.xml',
    ],
    # 'qweb': [
    #     'static/src/xml/web_dashboard.xml',
    # ],
    'images': ['images/main_screenshot.png'],
    'application': True,
    'auto_install': False,
}