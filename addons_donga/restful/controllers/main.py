"""Part of odoo. See LICENSE file for full copyright and licensing details."""

import datetime
import functools
import json
import logging

from odoo.addons.restful.common import (
    invalid_response,
    valid_response
)

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        # access_token = request.httprequest.headers.get("access_token")
        authorization = request.httprequest.headers.get("Authorization")
        if not authorization:
            return invalid_response(
                "authorization", "missing authorization in request header", 401
            )
        # Unicode-objects must be encoded before hashing
        # result = hashlib.md5('test:123@'.encode())
        # result = result.hexdigest()
        # 9a9af5b8174facde56cdb07e803c9f40
        result = '9a9af5b8174facde56cdb07e803c9f40'
        if result != authorization:
            return invalid_response(
                "authorization", "authorization seems to have expired or invalid", 401
            )

        # request.session.uid = 1
        # request.uid = 1
        return func(self, *args, **kwargs)

    return wrap


_routes = ["/api/<model>", "/api/<model>/<id>", "/api/<model>/<id>/<action>"]


class APIController(http.Controller):
    """."""

    def __init__(self):
        self._model = "ir.model"

    def _convert_string_to_date(self, string):
        return datetime.datetime(int(string[0:4]), int(string[4:6]), int(string[6:8]), int(string[8:10]),
                                 int(string[10:12]), int(string[12:14]))

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["GET"], csrf=False)
    def get(self, model=None, id=None, booking_id=None, phone=None, date_from=None, date_to=None, **payload):

        # call api GET http://baseurl/api/partner/{id}
        if model == "partner":
            module = 'res.partner'
            domain = []
            if id:
                domain.append(('id', '=', int(id)))
                data = request.env[module].sudo().search(domain, limit=1)
            else:
                data = request.env[module].sudo().search(domain)
            list_banner = []
            for item in data:
                list_banner.append({
                    "id": item.id,
                    "name": item.name,
                    "display_name": item.display_name,
                })
            data = list_banner
        elif model == "get-booking":
            module = 'crm.lead'
            domain = [('type', '=', 'opportunity')]
            if booking_id:
                domain.append(('name', '=', booking_id))
                data = request.env[module].sudo().search(domain, limit=1)
            else:
                if phone:
                    domain.append(('partner_address_phone', '=', phone))
                if date_from:
                    domain.append(('booking_date', '>=', self._convert_string_to_date(date_from)))
                if date_to:
                    domain.append(('booking_date', '<=', self._convert_string_to_date(date_to)))
                data = request.env[module].sudo().search(domain)
            list_booking = []
            for item in data:
                list_service = []
                for service in item.sale_order_line_id:
                    list_service.append({
                        'service_code': service.product_id.default_code,
                        'service_name': service.product_id.name,
                    })
                birth_date = ''
                if item.birth_date:
                    date = item.birth_date
                    birth_date = date.strftime("%Y") + date.strftime("%m") + date.strftime("%d") + '000000'
                list_booking.append({
                    'booking_id': item.name,
                    'name': item.partner_id.name,
                    'birthdate': birth_date,
                    'gender': item.gender,
                    'phone': item.partner_address_phone,
                    'address': item.partner_id.street if not item.partner_id.street2 else item.partner_id.street + ',' + item.partner_id.street2,
                    'services': list_service,
                    'source': item.source_id.name,
                })
            data = list_booking
        else:
            return invalid_response(
                "Error",
                "The route %s is not found." % model,
                404,
            )
        return valid_response(data)

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["POST"], csrf=False)
    def post(self, model=None, id=None, **payload):
        """Create a new record.
        Basic sage:
        import requests

        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'charset': 'utf-8',
            'access-token': 'access_token'
        }
        data = {
            'name': 'Babatope Ajepe',
            'country_id': 105,
            'child_ids': [
                {
                    'name': 'Contact',
                    'type': 'contact'
                },
                {
                    'name': 'Invoice',
                   'type': 'invoice'
                }
            ],
            'category_id': [{'id': 9}, {'id': 10}]
        }
        req = requests.post('%s/api/res.partner/' %
                            base_url, headers=headers, data=data)

        """
        ioc_name = model
        # model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        if 'customer-payment' == model:
            for item in payload:
                data = json.loads(str(item))
                _logger.warning(data)

                # error = False

                if 'booking_id' not in data or not data['booking_id']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'booking_id',
                    )

                if 'invoice_code' not in data or not data['invoice_code']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'invoice_code',
                    )

                if 'patient_code' not in data or not data['patient_code']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'patient_code',
                    )

                if 'type' not in data or not data['type']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'type',
                    )
                if 'service_datas' not in data:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'service_datas',
                    )

                if 'amount_due' not in data or not data['amount_due']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'amount_due',
                    )

                if 'amount_paid' not in data or not data['amount_due']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'amount_paid',
                    )

                booking_id = data['booking_id']
                patient_code = data['patient_code']
                amount_due = data['amount_due']
                amount_paid = data['amount_paid']
                payment_type = data['type']
                invoice_code = data['invoice_code']
                service_datas = data['service_datas']

                booking_id = request.env['crm.lead'].sudo().search(
                    [('type', '=', 'opportunity'), ('name', '=', booking_id)], limit=1)
                if invoice_code:
                    data = {
                        'booking_id': booking_id.name,
                        'invoice_code': invoice_code,
                        'patient_code': patient_code,
                        'amount_paid': amount_paid,
                        'amount_due': amount_due,
                        'service_datas': service_datas,
                        # 'type': payment_type
                    }

                    # Trường hợp 1 tạm ứng
                    if 1 == payment_type:
                        payment = request.env['account.payment'].sudo().create({
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'partner_form': '1',
                            'payment_method_id': '1',
                            'journal_id': '1',
                            'crm_id': booking_id.id,
                            'partner_id': booking_id.partner_id.id,
                            'brand_id': booking_id.brand_sci.id if booking_id.brand_sci else False,
                            'team_id': booking_id.team_id.id if booking_id.team_id else False,
                            'department_id': booking_id.department_id.id if booking_id.department_id else False,
                            'amount': amount_paid,
                        })
                        sale_order_line_ids = []
                        for service_data in service_datas:
                            product = request.env['product.product'].sudo().search(
                                [('code', '=', service_data['service_code'])], limit=1)
                            sale_order_line = request.env['sale.order.line'].sudo().create({
                                'price_unit': int(service_data['service_price']),
                                'discount': int(service_data['service_discount']) / int(
                                    service_data['service_price']) * 100 if service_data['service_discount'] else 0,
                                'product_uom_qty': int(service_data['service_quantity']),
                                'name': '',
                                'product_id': product.id,
                                'product_uom': product.uom_id.id,
                            })
                            sale_order_line_ids.append(sale_order_line.id)
                        payment.sale_order_line_ids = [(6, 0, sale_order_line_ids)]
                        return valid_response(data, message='Cập nhật tạm ứng thành công')
                    # Trường hợp 2 hóa đơn
                    elif 2 == payment_type:
                        payment = request.env['account.payment'].sudo().create({
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'partner_form': '1',
                            'payment_method_id': '1',
                            'journal_id': '1',
                            'crm_id': booking_id.id,
                            'partner_id': booking_id.partner_id.id,
                            'brand_id': booking_id.brand_sci.id if booking_id.brand_sci else False,
                            'team_id': booking_id.team_id.id if booking_id.team_id else False,
                            'department_id': booking_id.department_id.id if booking_id.department_id else False,
                            'amount': amount_paid,
                        })
                        # add service(s) to payment
                        sale_order_line_ids = []
                        for service_data in service_datas:
                            product = request.env['product.product'].sudo().search(
                                [('code', '=', service_data['service_code'])], limit=1)
                            sale_order_line = request.env['sale.order.line'].sudo().create({
                                'price_unit': int(service_data['service_price']),
                                'discount': int(service_data['service_discount']) / int(
                                    service_data['service_price']) * 100 if service_data['service_discount'] else 0,
                                'product_uom_qty': int(service_data['service_quantity']),
                                'name': '',
                                'product_id': product.id,
                                'product_uom': product.uom_id.id,
                            })
                            sale_order_line_ids.append(sale_order_line.id)
                        payment.sale_order_line_ids = [(6, 0, sale_order_line_ids)]
                        # add service(s) to booking
                        for service_data in service_datas:
                            product = request.env['product.product'].sudo().search(
                                [('code', '=', service_data['service_code'])], limit=1)
                            request.env['sale.order.line'].sudo().create({
                                'price_unit': int(service_data['service_price']),
                                'discount': int(service_data['service_discount']) / int(
                                    service_data['service_price']) * 100 if service_data['service_discount'] else 0,
                                'product_uom_qty': int(service_data['service_quantity']),
                                'name': '',
                                'product_id': product.id,
                                'product_uom': product.uom_id.id,
                                'crm_id': booking_id.id
                            })
                        return valid_response(data, message='Cập nhật hóa đơn thành công')
                    # Trường hợp 3 hoàn ứng
                    elif 3 == payment_type:
                        request.env['account.payment'].sudo().create({
                            'payment_type': 'outbound',
                            'partner_type': 'customer',
                            'partner_form': '1',
                            'payment_method_id': '1',
                            'journal_id': '1',
                            'crm_id': booking_id.id,
                            'partner_id': booking_id.partner_id.id,
                            'brand_id': booking_id.brand_sci.id if booking_id.brand_sci else False,
                            'team_id': booking_id.team_id.id if booking_id.team_id else False,
                            'department_id': booking_id.department_id.id if booking_id.department_id else False,
                            'amount': amount_paid,
                        })
                        return valid_response(data, message='Cập nhật hoàn ứng thành công')
                    else:
                        invalid_response(
                            "ERROR",
                            "Sai giá trị của tham số type %s." % payment_type,
                            200
                        )

        if 'update-customer-service' == model:
            for item in payload:
                data = json.loads(str(item))
                _logger.warning(data)
                # error = False

                if 'booking_id' not in data or not data['booking_id']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'booking_id',
                    )

                if 'patient_code' not in data or not data['patient_code']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'patient_code',
                    )

                if 'patient_name' not in data or not data['patient_name']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'patient_name',
                    )

                if 'patient_address' not in data or not data['patient_address']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'patient_address',
                    )

                if 'patient_birthdate' not in data or not data['patient_birthdate']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'patient_birthdate',
                    )

                if 'is_insurance' not in data or not data['is_insurance']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'is_insurance',
                    )

                if 'reception_date' not in data or not data['reception_date']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'reception_date',
                    )

                if 'out_date' not in data or not data['out_date']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'out_date',
                    )

                if 'amount_paid' not in data or not data['amount_paid']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'amount_paid',
                    )

                if 'amount_due' not in data or not data['amount_due']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'amount_due',
                    )

                if 'amount_discount' not in data or not data['amount_discount']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'amount_discount',
                    )

                if 'status' not in data or not data['status']:
                    return invalid_response(
                        "Missing",
                        "The parameter %s is missing." % 'status',
                    )

                booking_id = data['booking_id']
                patient_code = data['patient_code']
                patient_name = data['patient_name']
                patient_address = data['patient_address']
                patient_birthdate = data['patient_birthdate']
                is_insurance = data['is_insurance']
                reception_date = data['reception_date']
                out_date = data['out_date']
                amount_paid = data['amount_paid']
                amount_due = data['amount_due']
                amount_discount = data['amount_discount']
                status = data['status']

                if status in [1, 2, 3]:
                    data = {
                        'booking_id': booking_id,
                        'patient_code': patient_code,
                        'patient_name': patient_name,
                        'patient_address': patient_address,
                        'patient_birthdate': patient_birthdate,
                        'is_insurance': is_insurance,
                        'reception_date': reception_date,
                        'out_date': out_date,
                        'amount_paid': amount_paid,
                        'amount_due': amount_due,
                        'amount_discount': amount_discount,
                        'status': status,
                    }
                    crm_id = request.env['crm.lead'].sudo().search(
                        [('type', '=', 'opportunity'), ('name', '=', booking_id)], limit=1)
                    crm_id.write({
                        'is_insurance': is_insurance,
                        'reception_date': self._convert_string_to_date(reception_date),
                        'out_date': self._convert_string_to_date(out_date),
                        'amount_paid': amount_paid,
                        'amount_due': amount_due,
                        'amount_discount': amount_discount,
                        'status': status,
                    })

                    return valid_response(data, message='Cập nhật bệnh án thành công')
                else:
                    invalid_response(
                        "ERROR",
                        "Sai giá trị của tham số type %s." % status,
                        200
                    )

        if model == "get-booking":
            for item in payload:
                data = json.loads(str(item))
                _logger.warning(data)

                module = 'crm.lead'
                domain = [('type', '=', 'opportunity')]

                if 'booking_id' in data and data['booking_id']:
                    booking_id = data['booking_id']
                    domain.append(('name', '=', booking_id))
                    data = request.env[module].sudo().search(domain, limit=1)
                else:
                    if 'phone' in data and data['phone']:
                        domain.append(('partner_address_phone', '=', data['phone']))
                    if 'date_from' in data and data['date_from']:
                        domain.append(('booking_date', '>=', self._convert_string_to_date(data['date_from'])))
                    if 'date_to' in data and data['date_to']:
                        domain.append(('booking_date', '<=', self._convert_string_to_date(data['date_to'])))
                    data = request.env[module].sudo().search(domain)
                list_booking = []
                for item in data:
                    list_service = []
                    for service in item.sale_order_line_id:
                        list_service.append({
                            'service_code': service.product_id.default_code,
                            'service_name': service.product_id.name,
                        })
                    birth_date = ''
                    if item.birth_date:
                        date = item.birth_date
                        birth_date = date.strftime("%Y") + date.strftime("%m") + date.strftime("%d") + '000000'

                    if item.gender:
                        if item.gender == 'm':
                            gender = '1'
                        elif item.gender == 'f':
                            gender = '2'
                    address = ''
                    if item.partner_id.street:
                        address = item.partner_id.street
                        if item.partner_id.street2:
                            address = item.partner_id.street + ',' + item.partner_id.street2

                    list_booking.append({
                        'booking_id': item.name,
                        'name': item.partner_id.name,
                        'birthdate': birth_date,
                        'gender': gender,
                        'phone': item.partner_address_phone,
                        'address': address,
                        'services': list_service,
                        'source': item.source_id.name,
                    })
                data = list_booking
                return valid_response(data, message='Danh sách')
        return invalid_response(
            "Error",
            "The route %s is not found." % ioc_name,
            404,
        )

    # @validate_token
    @http.route(_routes, type="http", auth="none", methods=["PUT"], csrf=False)
    def put(self, model=None, id=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response(
                "invalid object id", "invalid literal %s for id with base " % id
            )
        _model = (
            request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        )
        if not _model:
            return invalid_response(
                "invalid object model",
                "The model %s is not available in the registry." % model,
                404,
            )
        try:
            request.env[_model.model].sudo().browse(_id).write(payload)
        except Exception as e:
            return invalid_response("exception", e.name)
        else:
            return valid_response(
                "update %s record with id %s successfully!" % (_model.model, _id)
            )

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["DELETE"], csrf=False)
    def delete(self, model=None, id=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response(
                "invalid object id", "invalid literal %s for id with base " % id
            )
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            if record:
                record.unlink()
            else:
                return invalid_response(
                    "missing_record",
                    "record object with id %s could not be found" % _id,
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e.name, 503)
        else:
            return valid_response("record %s has been successfully deleted" % record.id)

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["PATCH"], csrf=False)
    def patch(self, model=None, id=None, action=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response(
                "invalid object id", "invalid literal %s for id with base " % id
            )
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            _callable = action in [
                method for method in dir(record) if callable(getattr(record, method))
            ]
            if record and _callable:
                # action is a dynamic variable.
                getattr(record, action)()
            else:
                return invalid_response(
                    "missing_record",
                    "record object with id %s could not be found or %s object has no method %s"
                    % (_id, model, action),
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e, 503)
        else:
            return valid_response("record %s has been successfully patched" % record.id)
