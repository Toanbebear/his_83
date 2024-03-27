{
    "name": "API ERP",
    "version": "1.0.0",
    "category": "API ERP",
    "author": "",
    "website": "",
    "summary": "API ERP",
    "support": "",
    "description": """API ERP""",
    "depends":[
        'shealth_all_in_one'
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_param.xml",

        'views/setting_views.xml',
        'views/inherit_sh_medical_surgery.xml',
        'views/inherit_sh_medical_lab_test.xml',
        'views/inherit_sh_medical_patient.xml',
        'views/inherit_sh_medical_prescription.xml',
    ],
    "images": [],
    "license": "",
    "installable": True,
    'application': True,
    "auto_install": False,
}
