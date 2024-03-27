import datetime
import logging
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

from odoo import http
from odoo.addons.api_erp.common import (
    get_url_base,
    validate_token
)
from odoo.http import request
import json
_logger = logging.getLogger(__name__)

class PatientController(http.Controller):

    @validate_token
    @http.route("/api/create-patient", methods=["POST"], type="json", auth="none", csrf=False)
    def create_patient(self, **post):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= Đồng bộ tai khoan ==================')
        domain = [('phone', '=', body['phone'])]
        record = request.env['sh.medical.patient'].sudo().search(domain)
        gender_mapping = {
            'male': 'Male',
            'female': 'Female',
        }
        gender_value = gender_mapping.get(body.get('gender', '').lower(), None)
        state_id_record = request.env['res.country.state'].sudo().search([('code', '=', body['state_id']), ('country_id', '=', 241)])
        district_id_record = request.env['res.country.district'].sudo().search([('cs_id', '=', body['district_id'])])
        ward_id_record = request.env['res.country.ward'].sudo().search([('cs_id', '=', body['ward_id'])])
        value = {
            'dob':  body['year_of_birth'],
            'sex': gender_value,
            'name': body['name'],
            'phone': body['phone'],
            'function': body['career'] if body['career'] else 'Tự do',
            'ethnic_group': 1,
            'street': body['street'] if body['street'] else 'TP Hồ Chí Minh',
            'state_id': state_id_record.id if state_id_record else 702,
            'district_id': district_id_record.id if district_id_record else '',
            'ward_id': ward_id_record.id if ward_id_record else '',
            'weight': body['weight'] if body['weight'] else 0,
            'height': body['height'] if body['height'] else 0,
        }
        if record:
            record.sudo().write(value)
            # print('Đã có', record)
            # reception_create = request.env['sh.reception'].sudo().create({
            #     'patient':  record.id,
            #     'reception_date':' 2022-11-19 10:38:10',
            #     'advisory': 1,
            #     'service_room': 18,
            #     'reason_id':1,
            # })
            # print(reception_create)
            return json.dumps({
                'stage': 1,
                'message': 'SUA THANH CONG',
                'data': {'id': record.id}
            })
        else:
            account_storage_erp = request.env['sh.medical.patient'].sudo().create(value)
            if account_storage_erp:
                return json.dumps({
                    'stage': 1,
                    'message': 'TAO THANH CONG',
                     'data': {'id': account_storage_erp.id}
                })
            else:
                return json.dumps({
                'stage': 0,
                'message': 'TAO KHONG THANH CONG',
                'data': {'id': 0}
                })

