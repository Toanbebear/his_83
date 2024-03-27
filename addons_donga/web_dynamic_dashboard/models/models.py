# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import time
from odoo import models, fields, api

from odoo import http
import json
import logging
from werkzeug.exceptions import Forbidden

import werkzeug.urls

from odoo import http, tools, _
from odoo.http import request
from odoo.exceptions import ValidationError

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from random import choice
from string import ascii_uppercase

from datetime import datetime, timedelta
import re
import math


class View(models.Model):
    _inherit = 'ir.ui.view'
    type = fields.Selection(
        selection_add=[('ddashboard', 'DDashboard')]
    )


class ActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'
    view_mode = fields.Selection(
        selection_add=[('ddashboard', 'DDashboard')]
    )


class Dashboard(models.Model):
    _name = 'web.dashboard'

    name = fields.Char('Name', required=True, default="My Dashboard")
    parent_menu_id = fields.Many2one(
        'ir.ui.menu', 'Add Dashboard Under Menu', copy=False)
    menu_id = fields.Many2one('ir.ui.menu', 'Generated Menu', copy=False)
    block_ids = fields.One2many(
        'web.dashboard.block', 'dashboard_id', 'Blocks', copy=True)

    # TODO: Copy to 10
    dashboard_source = fields.Selection([('odoo', 'Odoo Dynamic Dashboard'), ('tableau', 'Tableau')],
                                        string='Dashboard Source', required=True, default='odoo')
    tableau_url = fields.Char('Tableau URL', required=False)

    # Iteration
    iteration_model_id = fields.Many2one('ir.model', 'Iteration Model')
    iteration_model = fields.Char(related='iteration_model_id.model', readonly=True)
    iteration_domain = fields.Char('Iteration Filter', required=False, default='')
    iteration_limit = fields.Integer('Limit', required=False, default='')
    iteration_sort_by = fields.Many2one('ir.model.fields', 'Sort By',
                               domain="[('store', '=', True), ('model_id', '=', iteration_model_id)]")
    iteration_sort = fields.Selection([('asc', 'Ascending'), ('desc', 'Descending')],
                                 string='Sort', required=True, default="desc")
    iteration_user_field_id = fields.Many2one('ir.model.fields', 'User Field',
                               domain="[('store', '=', True), ('model_id', '=', iteration_model_id), ('ttype', '=', 'many2one'), ('relation', '=', 'res.users')]")
    iteration_activate_record_rules = fields.Boolean('Activate Record Rules', default=True)

    @api.one
    def write(self, vals):
        res = super(Dashboard, self).write(vals)
        if self.id and 'parent_menu_id' in vals and self.parent_menu_id:
            if not self.menu_id:
                dashboard_action = self.env.ref('web_dynamic_dashboard.web_dashboard_action').copy({
                    'context': """{ 'dashboard_id' : %s }""" % self.id
                })
                menu = self.env['ir.ui.menu'].sudo().create({
                    'parent_id': self.parent_menu_id.id,
                    'name': self.name,
                    'action': 'ir.actions.act_window,%s' % dashboard_action.id,
                    'sequence': -100
                })
                self.menu_id = menu.id
            else:
                self.menu_id.write({
                    'name': self.name,
                    'parent_id': self.parent_menu_id.id,
                    'sequence': -100
                })
        elif self.id and 'parent_menu_id' in vals and not self.parent_menu_id and self.menu_id:
            self.menu_id.unlink()
        return res

    @api.model
    def create(self, vals):
        dashboard = super(Dashboard, self).create(vals)
        if dashboard.parent_menu_id:
            dashboard_action = self.env.ref('web_dynamic_dashboard.web_dashboard_action').copy({
                'context': """{ 'dashboard_id' : %s }""" % dashboard.id
            })
            menu = self.env['ir.ui.menu'].sudo().create({
                'parent_id': dashboard.parent_menu_id.id,
                'name': dashboard.name,
                'action': 'ir.actions.act_window,%s' % dashboard_action.id,
                'sequence': -100
            })
            dashboard.menu_id = menu.id
        return dashboard

class DashboardBlock(models.Model):
    _name = 'web.dashboard.block'
    _order = 'sequence'

    name = fields.Char('Name', required=True)
    dashboard_id = fields.Many2one('web.dashboard', 'Dashboard')
    block_type = fields.Selection([('tile', 'Tile'), ('line', 'Line'), ('area', 'Area'), ('bar', 'Bar'),
                                   ('stackbar', 'Stack Bar'), ('hbar', 'Horizontal Bar'), ('pie', 'Pie'),
                                   ('donut', 'Donut')], string='Block Type', required=True)
    block_size = fields.Selection([('6col', '1/6 (Suitable for Large Screen)'), ('4col', '1/4 (Suitable for Tile Block)'), ('3col', '1/3'),
                                   ('2col', '1/2'), ('1col', 'Full Screen')], string='Block Size', required=True)
    data_source = fields.Selection([('query', 'Configuration (Query)')],
                                   string='Data Source', required=True, default='query')
    # TODO: orm
    data_function = fields.Char('Function Name')
    model_id = fields.Many2one('ir.model', 'Model')
    model = fields.Char(related='model_id.model', readonly=True)
    field_id = fields.Many2one('ir.model.fields', 'Measured Field',
                               domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['float','integer','monetary'])]")  # Float / Int / Money
    operation = fields.Selection([('count', 'Count'), ('sum', 'Sum'),
                                  ('average', 'Average')], string='Operation', required=True, default='sum')

    # Group is for Chart only
    group_field_id = fields.Many2one('ir.model.fields', 'Group By',
                                     domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['char','date','datetime','many2one','boolean','selection'])]")
    group_field_id_model_name = fields.Char(
        'Group By Model', related='group_field_id.relation')
    group_relation_field_id = fields.Many2one('ir.model.fields', ' ',
                                              domain="[('store', '=', True), ('model_id.model', '=', group_field_id_model_name), ('ttype', 'in', ['char','date','datetime','many2one','boolean','selection'])]")
    group_field_ttype = fields.Selection(
        related='group_field_id.ttype', readonly=1)
    group_date_format = fields.Selection([('day', 'Day'), ('week', 'Week'),
                                          ('month', 'Month'), ('year', 'Year')],
                                         string='Date Format')
    show_group = fields.Boolean('Show Group If Empty')
    group_limit = fields.Integer('Limit')
    group_limit_selection = fields.Selection([(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '7'), (8, '8'), (9, '9'),
                                            (10, '10'), (15, '15'), (20, '20'), (30, '30')])
    show_group_others = fields.Boolean('Show Others')

    subgroup_field_id = fields.Many2one('ir.model.fields', 'Sub Group By',
                                        domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['char','date','datetime','many2one','boolean','selection'])]")
    subgroup_field_id_model_name = fields.Char(
        'Sub Group By Model', related='subgroup_field_id.relation')
    subgroup_relation_field_id = fields.Many2one('ir.model.fields', ' ',
                                                 domain="[('store', '=', True), ('model_id.model', '=', subgroup_field_id_model_name), ('ttype', 'in', ['char','date','datetime','many2one','boolean','selection'])]")
    subgroup_field_ttype = fields.Selection(
        related='subgroup_field_id.ttype', readonly=1)
    subgroup_date_format = fields.Selection([('day', 'Day'), ('week', 'Week'),
                                             ('month', 'Month'), ('year', 'Year')],
                                            string='Sub Group Date Format')
    show_subgroup = fields.Boolean('Show Sub Group If Empty')
    subgroup_limit = fields.Integer('Limit')
    subgroup_limit_selection = fields.Selection([(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '7'), (8, '8'), (9, '9'),
                                            (10, '10'), (15, '15'), (20, '20'), (30, '30')])
    show_subgroup_others = fields.Boolean('Show Others')

    # Domain, Limit, Sort
    time_calculation_method = fields.Selection([('normal', 'Normal'), ('cumulative', 'Cumulative'),
        ('before', 'Cumulative from before')], string='Calculation Method', default='normal')
    domain_date_field_id = fields.Many2one('ir.model.fields', 'Date Field', domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]")
    domain_date = fields.Selection([('today', 'Today'), ('this_week', 'This Week'),
                                    ('this_month', 'This Month'), ('this_year', 'This Year'),
                                    ('last_two_months', 'Last 2 Months'), ('last_three_months', 'Last 3 Months'),
                                    ('last_month', 'Last Month'), ('last_10', 'Last 10 Days'), 
                                    ('last_30', 'Last 30 Days'), ('last_60', 'Last 60 Days'),
                                    ('before_today', 'Before Today'), ('after_today', 'After Today'),
                                    ('before_and_today', 'Before and Today'), ('today_and_after', 'Today and After')],
                                   string='Date Filter')
    domain = fields.Char('Flexible Filter (Slow Performance)', required=False, default='')
    domain_values_field_id = fields.Many2one('ir.model.fields', 'Filter By', domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['char', 'many2one', 'integer', 'float', 'boolean', 'selection'])]")
    domain_values_string = fields.Text('Filter Values')
    subdomain_values_field_id = fields.Many2one('ir.model.fields', 'Sub Filter By', domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['char', 'many2one', 'integer', 'float', 'boolean', 'selection'])]")
    subdomain_values_string = fields.Text('Sub Filter Values')
    domain_line_ids = fields.One2many('web.domain.line', 'block_id', 'Domains')
    barang_masuk_id = fields.Many2one('barang.masuk', 'Barang Masuk')
    limit = fields.Integer('Limit', default=0)
    sort_by = fields.Many2one('ir.model.fields', 'Sort By')
    sort = fields.Selection([('asc', 'Ascending'), ('desc', 'Descending')],
                                 string='Sort', required=True, default="desc")
    others_operation = fields.Selection([('count', 'Count'), ('sum', 'Sum'),
                                         ('average', 'Average')], string='Others Operation', required=True, default="average")

    active = fields.Boolean('Active', required=True, default=True)
    menu_id = fields.Many2one('ir.ui.menu', 'Open Menu')
    link = fields.Char('Open URL')
    show_metadata = fields.Boolean('Show Metadata')
    sequence = fields.Integer('Sequence')

    # Styling
    tile_color = fields.Char(string='Tile Color')
    tile_icon = fields.Char('Tile Icon')
    # list_field_ids = fields.Many2many('ir.model.fields', 'Fields on List View', domain="[('store', '=', True), ('model_id', '=', model_id)]")

    # Action
    action_group_field_ids = fields.One2many('action.group.field', 'block_id', 'Action Group Fields')
    action_dashboard_id = fields.Many2one('web.dashboard', 'Open Dashboard')
    action_group_list_view = fields.Boolean('Group List View')

    # Iteration
    dashboard_iteration_model = fields.Char(string='Iteration Model', related='dashboard_id.iteration_model_id.model')
    dashboard_iteration_domain_field_id = fields.Many2one('ir.model.fields', 'Domain Field',
                                     domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', '=', 'many2one'), ('relation', '=', dashboard_iteration_model)]")
    block_iteration = fields.Boolean('Iterate Block')
    block_iteration_domain = fields.Char('Iteration Filter', required=False, default='')
    
    # Advanced Filters & Security
    user_field_id = fields.Many2one('ir.model.fields', 'User Field',
                               domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', '=', 'many2one'), ('relation', '=', 'res.users')]")
    activate_record_rules = fields.Boolean('Activate Record Rules', default=False)

    @api.onchange('block_type')
    def _change_block_type(self):
        for block in self:
            if block.block_type == 'tile':
                block.block_size = '4col'
            else:
                block.block_size = '2col'

class ActionGroupField(models.Model):
    _name = 'action.group.field'

    sequence = fields.Integer('Sequence')
    block_id = fields.Many2one('web.dashboard.block', 'Dashboard Block')
    model_id = fields.Many2one('ir.model', 'Model', related='block_id.model_id')
    field_id = fields.Many2one('ir.model.fields', 'Field', domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['char','date','datetime','many2one','boolean','selection'])]")
    block_type = fields.Selection([('tile', 'Tile'), ('line', 'Line'), ('area', 'Area'), ('bar', 'Bar'),
                                   ('stackbar', 'Stack Bar'), ('hbar', 'Horizontal Bar'), ('pie', 'Pie'),
                                   ('donut', 'Donut')], string='Block Type')
class DomainLine(models.Model):
    _name = 'web.domain.line'

    block_id = fields.Many2one('web.dashboard.block', 'Block')
    field_id = fields.Many2one('ir.model.fields', 'Field',
                               domain="[('ttype', 'in', ['char', 'selection', 'float', 'integer', 'monetary'])]", required=True)  # Float / Int / Money
    operator = fields.Selection([('=', '='), ('!=', '!='), ('<', '<'), ('>', '>'), ('>=', '>='), ('<=', '<='),
                                 ('like', 'like'), ('ilike', 'ilike'), ('in', 'in'), ('not in', 'not in')],
                                string='Operator', required=True)
    value = fields.Char('Value', required=True, default='')
