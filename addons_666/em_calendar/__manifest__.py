# -*- coding: utf-8 -*-
# Copyright 2016, 2019 Openworx
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).



{
    "name": "Lịch làm việc",
    "summary": "Đặt lịch làm việc cho cán bộ nhân viên, bsi",
    "version": "12.0.0.1",
    "website": "http://666.kangnam.com.vn/",
    'sequence': 1,
	"description": """
		lịch làm việc của cán bộ nhân viên
    """,
    "depends": ['hr', 'base'],
    "author": "Toàn bebear",
    "installable": True,
    'application': True,
    'auto_install': False,
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/em_schedule_views.xml',
        'views/training_schedule_views.xml',
        'wizard/bao_cao_nhan_luc/human_report_view.xml',
        'wizard/bao_cao_danh_sach_nhan_su/personnel_report.xml',
        'wizard/bao_cao_cham_cong/timekeeping_report_view.xml',
    ],
    'qweb': [

    ]

}
