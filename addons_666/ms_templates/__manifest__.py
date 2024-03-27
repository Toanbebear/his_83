# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MS templates',
    'author': 'Nomed',
    'version': '1.0',
    'category': 'Templates',
    'sequence': 75,
    'summary': 'Create report from excel or words templates',
    'description': "",
    'website': 'http://project.scisoftware.xyz/',
    'images': [
    ],
    'depends': ['mail'
    ],
    'data': [
        'security/excel_templates_security.xml',
        'security/ir.model.access.csv',
        'views/temp_creation_view.xml',
        'data/template_iframe.xml',
        'views/temp_wizard_view.xml',
    ],
    'demo': [
    ],
    "external_dependencies": {
        "python": ['openpyxl',],
        "bin": [],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
