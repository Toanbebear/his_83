# -*- coding: utf-8 -*-

from odoo import fields, api, models, _

class CountryDistrict(models.Model):
    _name = "res.country.district"
    _description = 'District of country'

    name = fields.Char('Name', required=True)
    state_id = fields.Many2one('res.country.state', 'Thành phố', required=True)
    active = fields.Boolean('Active', default=True)
    ward_ids = fields.One2many('res.country.ward', 'district_id', string='Ward')
    cs_id = fields.Integer()

class CountryState(models.Model):
    _inherit = "res.country.state"

    district_ids = fields.One2many('res.country.district', 'state_id', string='Districts')
