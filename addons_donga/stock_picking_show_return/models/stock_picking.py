# Copyright 2014-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    returned_ids = fields.Many2many(
        "stock.picking", 'sh_stock_picking_rel', 'picking_id', 'picking_returned_id', compute="_compute_returned_ids",
        string="Returned pickings", store=True)

    @api.multi
    def _compute_returned_ids(self):
        for picking in self:
            picking.returned_ids = picking.mapped(
                'move_lines.returned_move_ids.picking_id')
