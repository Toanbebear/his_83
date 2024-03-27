{
    "name": "QR CODE BỆNH NHÂN",
    "summary": "Mã QR code bệnh nhân",
    "version": "12.0.0.1",
    "website": "",
    'sequence': 1,
	"description": """""",
    "depends": ['shealth_all_in_one'],
    "author": "Toàn bebear",
    "installable": True,
    'application': True,
    'auto_install': False,
    "data": [
        'data/report_papeformat.xml',
        'views/report_qr_code_patient.xml',
        'views/sh_medical_patient_inherit_view.xml',
    ],
    'qweb': [

    ]

}
