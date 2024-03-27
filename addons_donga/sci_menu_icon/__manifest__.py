# -*- coding: utf-8 -*-
# Copyright 2016, 2019 Openworx
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).



{
    "name": "SCI MENU ICON",
    "summary": "App for view icon on menu",
    "version": "12.0.0.1",
    "website": "http://scigroup.com.vn/",
    'sequence': 1,
	"description": """
		App for view icon on menu
    """,
    "author": "dungntp",
    "installable": True,
    "data": [
        'views/assets.xml',
		'views/ir_ui_menu_views.xml',
		# 'views/res_config_settings_view.xml',
    ],
    'qweb': [
        "static/src/xml/menu.xml",
    ]

}
