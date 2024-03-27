"""Common methods"""
import json
import logging

import werkzeug.wrappers

_logger = logging.getLogger(__name__)


# try:
# import simplejson as json
# from simplejson.errors import JSONDecodeError
# except ModuleNotFoundError as identifier:
# _logger.error(identifier)
# else:
# import json


def valid_response(data, status=200, typ='OK', message='Successful'):
    """Valid Response
    This will be return when the http request was successfully processed."""
    data_format = {
        "error_code": typ,
        "error_message": str(message),
        "data": []
    }

    if data:
        data_format['data'] = data
        # data = {"count": len(data), "data": data}

    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(data_format, indent=4, sort_keys=True, default=str),
    )


def invalid_response(typ, message=None, status=401):
    """Invalid Response
    This will be the return value whenever the server runs into an error
    either from the client or the server."""
    # return json.dumps({})
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(
            {
                "error_code": typ,
                "error_message": str(message)
                if str(message)
                else "wrong arguments (missing validation)",
            }
        ),
    )


def extract_arguments(payloads, offset=0, limit=0, order=''):
    fields, filter, payload = [], [], {}
    if payloads:
        if payloads.get("offset"):
            offset = int(payloads["offset"])
        if payloads.get("items_per_page"):
            limit = int(payloads.get("items_per_page"))
        if payloads.get("order"):
            order = payloads.get("order")
    return [filter, offset, limit, order]
