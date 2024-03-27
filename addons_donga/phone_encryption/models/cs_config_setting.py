from odoo import api, models, fields


class CaresoftConfigSetting(models.TransientModel):
    _inherit = "res.config.settings"

    encrypt_phone = fields.Boolean(string='Mã hóa số điện thoại', readonly=False,
                                help='Mã hóa 5 số điện thoại khi hiển thị cho người dùng',
                                config_parameter='phone_encryption.encrypt_phone')
