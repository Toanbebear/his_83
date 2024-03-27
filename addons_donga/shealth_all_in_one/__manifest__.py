##############################################################################
#    Copyright (C) 2018 shealth (<http://scigroup.com.vn/>). All Rights Reserved
#    shealth, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, shealth.in, openerpestore.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

{
    'name': 'SCI Health All In One',
    'version': '3.0.4',
    'sequence': 0,
    'author': "SCI Apps - Dungntp",
    'category': 'Generic Modules/Medical',
    'summary': 'Complete set of powerful features from shealth & shealth Extra Addons',
    'depends': ['account','base', 'purchase_stock','l10n_vn', 'product', 'hr', 'web','product_expiry','backend_theme_v12',
                'sci_menu_icon','ms_templates','ees_tree_no_open','odt_base', 'muk_web_client_refresh',
                'web_listview_range_select','stock_picking_show_return','stock_inventory_import','web_form_dynamic_button','field_image_preview'],
    'support': '',
    'description': """

About SCI Health
---------------

shealth is a multi-user, highly scalable, centralized Electronic Medical Record (EMR) and Hospital Information System for Odoo.

Manage your patients with their important details including family info, prescriptions, appointments, diseases, insurances, lifestyle,mental & social status, lab test details, invoices and surgical histories.

Administer all your doctors with their complete details, weekly consultancy schedule, prescriptions, inpatient admissions and many more.

Allow your doctors and patients to login inside your SCI Health system to manage their appointments. SCI Health is tightly integrated with Odoo’s calendar control so you will be always updated for your upcoming schedules.

""",
    "website": "http://scigroup.com.vn/",
    "data": [
        'views/shealth.xml',
        'security/sh_security.xml',

        'sequence/sh_sequence.xml',
        'sh_navigation.xml',

        'sh_branch/views/sh_branch_view.xml',
        'sh_medical/views/res_partner_view.xml',
        'sh_medical/views/product_product_view.xml',
        'sh_medical/views/sh_medical_medicaments_view.xml',
        'sh_medical/views/sh_medical_pharmacy_view.xml',
        'sh_medical/views/sh_medical_healthcenters_view.xml',
        'sh_medical/views/sh_medical_pathology_view.xml',
        'sh_medical/views/sh_medical_pathology_icd9_view.xml',
        'sh_medical/views/sh_medical_inpatient_view.xml',
        'sh_medical/views/sh_medical_view.xml',
        'sh_medical/views/account_invoice_view.xml',
        # 'sh_medical/views/sh_medical_insurance_view.xml',
        'sh_medical/views/sh_medical_ethnic_groups_view.xml',
        'sh_medical/views/sh_medical_genetics_view.xml',

        'sh_medical/data/sh_medical_team_role.xml',

        'sh_medical/views/inherit_sh_medical_physician_view.xml',

        'sh_branch/data/sh_branch.xml',
        'sh_medical/data/sh_medical_health_center.xml',
        'sh_medical/data/sh_physician_specialities.xml',
        # 'sh_medical/data/sh_physician_degrees.xml',
        # 'sh_medical/data/sh_insurance_types.xml',
        'sh_medical/data/sh_ethnic_groups.xml',
        # 'sh_medical/data/sh_who_medicaments.xml',
        'sh_medical/views/sh_medical_service_view.xml',

        'sh_medical/views/sh_medical_prescription_view.xml',
        'sh_medical/wizard/sh_prescription_cancel_view.xml',

        # 'sh_medical/data/sh_dose_units.xml',
        # 'sh_medical/data/sh_drug_administration_routes.xml',
        # 'sh_medical/data/sh_drug_form.xml',
        # 'sh_medical/data/sh_dose_frequencies.xml',
        # 'sh_medical/data/sh_genetic_risks.xml',
        'sh_medical/data/sh_report_paperformat.xml',
        'sh_medical/reports/report_patient_label.xml',
        'sh_medical/reports/report_patient_medicines.xml',
        'sh_medical/reports/report_appointment_receipt.xml',
        'sh_medical/reports/report_patient_prescriptions.xml',
        'sh_medical/reports/report_temp_service.xml',
        'sh_medical/views/sh_medical_report.xml',

        'sh_evaluation/views/sh_medical_evaluation_view.xml',
        # 'sh_socioeconomics/views/sh_medical_socioeconomics_view.xml',
        # 'sh_socioeconomics/data/sh_occupations.xml',
        # 'sh_gyneco/views/sh_medical_gyneco_view.xml',
        'sh_lifestyle/views/sh_medical_lifestyle_view.xml',
        'sh_lifestyle/data/sh_recreational_drugs.xml',
        'sh_lab/data/sh_lab_test_units.xml',
        # 'sh_lab/data/sh_lab_test_types.xml',
        'sh_lab/views/report_patient_labtest.xml',
        'sh_lab/views/sh_medical_lab_report.xml',
        'sh_lab/views/sh_medical_lab_view.xml',

        # 'sh_pediatrics/views/res_partner_view.xml',
        # 'sh_pediatrics/views/sh_medical_pediatrics_newborn_view.xml',
        # 'sh_pediatrics/views/sh_medical_pediatrics_pcs_view.xml',
        # 'sh_pediatrics/views/sh_medical_pediatrics_growth_chart_view.xml',
        # 'sh_pediatrics/data/sh_medical_wfa_boys_p.xml',
        # 'sh_pediatrics/data/sh_medical_wfa_boys_z.xml',
        # 'sh_pediatrics/data/sh_medical_wfa_girls_p.xml',
        # 'sh_pediatrics/data/sh_medical_wfa_girls_z.xml',
        # 'sh_pediatrics/data/sh_medical_lhfa_boys_p.xml',
        # 'sh_pediatrics/data/sh_medical_lhfa_boys_z.xml',
        # 'sh_pediatrics/data/sh_medical_lhfa_girls_p.xml',
        # 'sh_pediatrics/data/sh_medical_lhfa_girls_z.xml',
        # 'sh_pediatrics/data/sh_medical_bmi_boys_p.xml',
        # 'sh_pediatrics/data/sh_medical_bmi_boys_z.xml',
        # 'sh_pediatrics/data/sh_medical_bmi_girls_p.xml',
        # 'sh_pediatrics/data/sh_medical_bmi_girls_z.xml',

        # 'sh_icd10pcs/views/sh_icd10pcs_view.xml',
        'sh_surgery/views/sh_medical_healthcenters_view.xml',
        'sh_surgery/views/sh_medical_surgery_view.xml',
        'sh_surgery/views/sh_medical_specialty_view.xml',
        'sh_surgery/views/sh_medical_service_view.xml',
        'sh_surgery/data/sh_medical_health_center_ot.xml',

        'sh_medical/views/sh_medical_medicaments_view.xml',

        # 'sh_ophthalmology/views/sh_medical_ophthalmology_view.xml',
        # 'sh_ophthalmology/views/sh_medical_ophthalmology_report.xml',
        # 'sh_ophthalmology/views/sh_medical_report.xml',

        "sh_nursing/views/sh_medical_nursing_view.xml",
        "sh_nursing/views/sh_medical_instruction_view.xml",
        "sh_nursing/views/sh_medical_rounding_report.xml",
        "sh_nursing/views/sh_medical_report.xml",
        "sh_nursing/views/sh_medical_patient_rounding_view.xml",

        # "sh_imaging/data/sh_imaging_test_types.xml",
        "sh_imaging/views/sh_medical_imaging_view.xml",
        "sh_imaging/views/report_patient_imaging.xml",
        "sh_imaging/views/sh_medical_imaging_report.xml",

        "sh_evaluation_history/views/sh_medical_evaluation_report.xml",
        "sh_evaluation_history/views/sh_medical_report.xml",

        # 'sh_medical_certificate/views/sh_medical_certificate_view.xml',
        # 'sh_medical_certificate/views/report_medical_certificate.xml',
        # 'sh_medical_certificate/views/sh_medical_report.xml',

        'sh_walkins/wizard/walkin_labtest_result.xml',
        'sh_walkins/views/sh_medical_register_for_walkin_view.xml',
        'sh_walkins/views/report_walkin_patient_labtest.xml',
        'sh_walkins/views/sh_medical_walkin_lab_report.xml',
        'sh_walkins/views/report_walkin_patient_imaging.xml',
        'sh_walkins/views/sh_medical_walkin_img_report.xml',
        'sh_walkins/views/report_walkin_patient_services.xml',
        'sh_walkins/views/sh_medical_walkin_services_report.xml',

        'sh_patient_call_log/views/sh_medical_patient_call_log_view.xml',

        'sh_patient_medical_history/views/sh_medical_patient_view.xml',

        'sh_medical/data/sh_medical_services.xml',

        'sh_reception/views/sh_reception_view.xml',
        'sh_reception/views/report_receptiont_patient.xml',

        'sh_payment/views/sh_payment_view.xml',
        'sh_payment/views/inherit_report_payment_receipt_templates.xml',

        # Cải tiến
        'sh_reception/views/sh_reason_view.xml',
        'sh_payment/views/inherit_institution_view.xml',

        # cập nhật phiếu thu
        'sh_payment/wizard/tool_update_payment.xml',

        # Duyệt nợ
        'sh_debt/views/debt_reviews.xml',
        'sh_debt/views/walkin_debt_review.xml',

        #REPORT
        'sh_report/data/ir_config_param.xml',
        'sh_report/data/template_attachment.xml',
        'sh_report/wizard/dieutri_report.xml',
        'sh_report/wizard/surgery_report.xml',
        'sh_report/wizard/physician_report.xml',
        'sh_report/wizard/walkin_report.xml',
        'sh_report/wizard/inventory_report.xml',
        'sh_report/wizard/pathology_report.xml',
        'sh_report/wizard/duoc_report.xml',
        'sh_report/views/inherit_product_view.xml',
        
        # báo cáo doanh thu bệnh nhân
        'sh_report/data/report_revenue_patient.xml',
        'sh_report/wizard/report_revenue_patient.xml',

        # biên bản kiểm nhập thuốc - SonDC
        'sh_stock/views/report_drug_entry.xml',
        'sh_stock/wizard/quick_add_stock_scrap.xml',


        'security/sh_menu_rights.xml',
        'security/ir.model.access.csv',
        'security/ir.rule.xml',

        'sh_medical/data/sh_disease_categories.xml',
        # 'sh_medical/data/sh_diseases.xml',

        'sh_stock/data/template_attachment.xml',
        'sh_stock/views/report_sh_stock_view.xml',
        'sh_stock/views/sh_stock_view.xml',

        'sh_stock/wizard/action_return_stock_scrap.xml',

        'sh_stock/wizard/inherit_stock_transfer/inherit_overprocessed_transfer_view.xml',


        # 'sh_icd10pcs/data/sh_icd_10_pcs_2009_part1.xml',
        # 'sh_icd10pcs/data/sh_icd_10_pcs_2009_part2.xml',
        # 'sh_icd10pcs/data/sh_icd_10_pcs_2009_part3.xml',
    ],
    "images": ['images/main_screenshot.png'],
    "demo": [

    ],
    'test':[
    ],
    'css': [],
    'js': [

    ],
    'qweb': [

    ],
    'application': True,
    "active": False
}