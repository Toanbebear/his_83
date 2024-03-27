# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InheritStockOverProcessedTransfer(models.TransientModel):
    _name = 'inherit.stock.overprocessed.transfer'
    _description = 'Transfer Over Processed Stock'

    picking_id = fields.Many2one('stock.picking')
    overprocessed_product_name = fields.Char(compute='_compute_overprocessed_product_name1',
                                             readonly=True)

    @api.multi
    def _compute_overprocessed_product_name1(self):
        for wizard in self:
            moves = wizard.picking_id._get_check_stock()
            wizard.overprocessed_product_name = moves[0].product_id.display_name

