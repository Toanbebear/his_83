from odoo import models, fields


class Setting(models.TransientModel):
    _inherit = "res.config.settings"

    erp_url = fields.Char(string='User', readonly=False, config_parameter='api_erp.erp_url')
