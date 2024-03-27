# -*- coding: utf-8 -*-

from odoo import fields, api, models, _


class CountryWard(models.Model):
    _name = "res.country.ward"
    _description = "Country ward"

    name = fields.Char('Name', required=True)
    district_id = fields.Many2one('res.country.district', 'District', required=True)
    active = fields.Boolean('Active', default=True)
    cs_id = fields.Integer()

