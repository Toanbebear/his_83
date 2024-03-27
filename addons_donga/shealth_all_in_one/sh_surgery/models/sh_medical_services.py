##############################################################################
#    Copyright (C) 2018 shealth (<http://scigroup.com.vn/>). All Rights Reserved
#    shealth, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, shealth.in, openerpestore.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, AccessError, ValidationError, Warning

# Services
class SHealthServices(models.Model):
    _inherit = ['sh.medical.health.center.service']

    # service_room = fields.Many2one('sh.medical.health.center.ot', string='Room perform', domain="[('department', '=', service_department)]")
    # exam_room = fields.Many2one('sh.medical.health.center.ot', string='Room examination', domain="[('institution', '=', institution)]")
    service_room = fields.Many2many('sh.medical.health.center.ot','service_rooms_rel', string='Room perform')
    exam_room = fields.Many2many('sh.medical.health.center.ot','exam_rooms_rel', string='Room examination')

    # @api.onchange('service_department')
    # def _onchange_service_department(self):
    #     self.service_room = ''

# class SHealthServiceChild(models.Model):
#     _inherit = ['sh.medical.health.center.service.childs']
#
#     service_room = fields.Many2one('sh.medical.health.center.ot', string='Room perform',compute='_compute_service_childs_id')
#     exam_room = fields.Many2one('sh.medical.health.center.ot', string='Room examination', domain="[('institution', '=', institution)]")
#
#     @api.one
#     @api.depends('service_child_ids')
#     def _compute_service_childs_id(self):
#         res = super(SHealthServiceChild, self)._compute_service_childs_id()
#         if self.service_child_ids:
#             self.service_room = self.service_child_ids.service_room.id
#             self.exam_room = self.service_child_ids.exam_room.id
#
#         return res

