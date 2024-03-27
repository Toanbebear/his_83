# -*- coding: utf-8 -*-
###############################################################################
#
#    Công ty công nghệ OdooTech
#    Copyright (C) 2019.
#
###############################################################################


{
    'name': 'Odoo Tech Base',
    'description': 'Base module',
    'summary': 'Base module in Odoo Tech Base',
    'category': 'base',
    "sequence": 2,
    'version': '1.0.0',
    'author': 'odt',
    'website': 'http://odoootech.vn',
    'depends': ['base', 'web'],
    'data': [
        'views/asset_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
