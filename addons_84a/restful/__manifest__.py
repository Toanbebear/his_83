{
    "name": "RESTFUL API",
    "version": "1.0.0",
    "category": "API",
    'sequence': 2,
    "author": "SCI Dev",
    "website": "https://scigroup.com.vn",
    "summary": "RESTFUL API",
    "support": "contact@scigroup.com.vn",
    "description": """ RESTFUL API For Odoo
====================
With use of this module user can enable REST API in any Odoo applications/modules

""",
    "depends": ["web"],
    "data": [
        "data/ir_config_param.xml",
        "views/ir_model.xml",
        "views/res_users.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["static/description/main_screenshot.png"],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    'application': True,
}
