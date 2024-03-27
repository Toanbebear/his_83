from odoo import fields, models

from io import BytesIO
from odoo.http import request
import qrcode
import base64

def qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    temp = BytesIO()
    img.save(temp, format="PNG")
    qr_code_id = base64.b64encode(temp.getvalue())
    return qr_code_id

class ShMedicalEvaluationQRCode(models.Model):
    _inherit = 'sh.medical.evaluation'

    qr_code_id = fields.Binary(string="QR Code", compute='_generate_qr_code_id')

    def _generate_qr_code_id(self):
        for item in self:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            base_url += '/web#id=%d&action=400&view_type=form&model=%s' % (item.id, item._name)
            item.qr_code_id = qr_code(base_url)
