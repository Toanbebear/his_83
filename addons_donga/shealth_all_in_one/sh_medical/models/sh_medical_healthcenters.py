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

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
from odoo.tools.translate import _
import re

_logger = logging.getLogger(__name__)

# Health Center Management

class SHealthCenters(models.Model):
    _name = 'sh.medical.health.center'
    _description = "Information about the health centers"
    _inherits={
        'res.partner': 'partner_id',
    }

    # HEALTH_CENTERS = [
    #     ('Hospital', 'Hospital'),
    #     ('Nursing Home', 'Nursing Home'),
    #     ('Clinic', 'Clinic'),
    #     ('Community Health Center', 'Community Health Center'),
    #     ('Military Medical Facility', 'Military Medical Facility'),
    #     ('Other', 'Other'),
    # ]

    # @api.multi
    # def _building_count(self):
    #     oe_buildings = self.env['sh.medical.health.center.building']
    #     for hec in self:
    #         domain = [('institution', '=', hec.id)]
    #         buildings_ids = oe_buildings.search(domain)
    #         buildings = oe_buildings.browse(buildings_ids)
    #         bu_count = 0
    #         for bul in buildings:
    #             bu_count+=1
    #         hec.building_count = bu_count
    #     return True

    # @api.multi
    # def _pharmacy_count(self):
    #     oe_pharmacies = self.env['sh.medical.health.center.pharmacy']
    #     for hec in self:
    #         domain = [('institution', '=', hec.id)]
    #         pharmacies_ids = oe_pharmacies.search(domain)
    #         pharmacies = oe_pharmacies.browse(pharmacies_ids)
    #         pha_count = 0
    #         for pha in pharmacies:
    #             pha_count+=1
    #         hec.pharmacy_count = pha_count
    #     return True

    @api.multi
    def _ward_count(self):
        oe_wards = self.env['sh.medical.health.center.ward']
        for hec in self:
            domain = [('institution', '=', hec.id)]
            wards_ids = oe_wards.search(domain)
            wards = oe_wards.browse(wards_ids)
            ward_count = 0
            for ward in wards:
                ward_count += 1
            hec.ward_count = ward_count
        return True

    @api.multi
    def _room_count(self):
        oe_rooms = self.env['sh.medical.health.center.ot']
        for hec in self:
            domain = [('institution', '=', hec.id)]
            rooms_ids = oe_rooms.search(domain)
            rooms = oe_rooms.browse(rooms_ids)
            room_count = 0
            for room in rooms:
                room_count += 1
            hec.room_count = room_count
        return True


    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True,ondelete='cascade', help='Partner-related data of the hospitals')
    branch = fields.Many2one('sh.branch', string="Branch")

    # health_center_type = fields.Selection(HEALTH_CENTERS, string='Type', help="Health center type", index=True)
    info = fields.Text('Extra Information')
    company_name = fields.Text('Tên công ty')
    # building_count = fields.Integer(compute=_building_count, string="Buildings")

    # pharmacy_count = fields.Integer(compute=_pharmacy_count, string="Pharmacies")
    ward_count = fields.Integer(compute=_ward_count, string="Departments")
    room_count = fields.Integer(compute=_room_count, string="Rooms")
    warehouse_ids = fields.One2many('stock.warehouse', 'healthcenter_stock_wh', string='Warehouse')
    # pharmacy = fields.One2many('sh.medical.health.center.pharmacy', 'institution', string='Pharmacy')

    location_medicine_stock = fields.Many2one('stock.location','Stock Medicine', domain="[('usage', '=', 'internal')]")
    location_emergency_stock = fields.Many2one('stock.location','Stock Emergency', domain="[('usage', '=', 'internal')]")

    #department hr
    department_hr = fields.Many2one('hr.department', string="Department of HR")
    # user_access = fields.Many2many('res.users', string="User access",compute="_compute_department_hr", store=True)
    user_access = fields.Many2many('res.users', 'sh_users_health_center_rel', 'ins_id', 'user_id', string="User access",store=True)
    # group_user_access = fields.Many2one('res.groups', string="Group user access health", default=lambda self: self.env.ref('base.group_user').id)
        # [(6,0,[self.env.ref['shealth_all_in_one.group_sh_medical_manager'].id,
        #        self.env.ref['shealth_all_in_one.group_sh_medical_physician'].id],
        #        self.env.ref['shealth_all_in_one.group_sh_medical_nurse'].id)])

    # @api.one
    # @api.depends('group_user_access.users')
    # def _compute_group_user_access(self):
    #     admins = self.group_user_access.users
    #     self.user_access = [(6,0, admins)]

    # @api.one
    # @api.depends('department_hr.member_ids','group_user_access.users')
    # def _compute_department_hr(self):
    #     list_user = [member.user_id.id for member in self.department_hr.member_ids]
    #     admins = self.group_user_access.users
    #     final_list = list(set(list_user + admins.ids))
    #     self.user_access = [(6,0, final_list)]
    #     print(admins, final_list)

    # Hệ thông quốc gia
    url_prescription = fields.Char('Domain Đơn thuốc quốc gia', help='TRang web đơn thuốc quốc gia')
    ma_lien_thong_co_so_kham_chua_benh = fields.Char('Mã liên thông CSKCB')
    password_co_so = fields.Char('Mật khẩu')
    login = fields.Char('Tài khoản', help='Tài khoản đăng nhập đơn thuốc Điện tử đối tác')
    password = fields.Char('Mật khẩu', help='Mật khẩu đăng nhập đơn thuốc Điện tử đối tác')
    url_api_prescription = fields.Char('Api Từng đơn thuốc', help='token bác sĩ')

    def no_accent_vietnamese(selft, s):
        s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
        s = re.sub(r'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
        s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
        s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
        s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
        s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
        s = re.sub(r'[ìíịỉĩ]', 'i', s)
        s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
        s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
        s = re.sub(r'[ƯỪỨỰỬỮÙÚỤỦŨ]', 'U', s)
        s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
        s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
        s = re.sub(r'[Đ]', 'D', s)
        s = re.sub(r'[đ]', 'd', s)
        s = re.sub(r'[^\w.]', '', s)
        return s

    @api.model
    def create(self, vals):
        str_name = vals['name'].split()
        codeWH = ''
        for str in str_name:
            codeWH += str[0]
        codeWH = self.no_accent_vietnamese(codeWH).upper()

        vals["is_institution"] = True
        # vals["is_company"] = True
        health_center = super(SHealthCenters, self).create(vals)

        #create warehouse default for health center
        #StockWarehouse = self.env['stock.warehouse']
        # tạo kho cho bệnh viện
        # wh_health_center = StockWarehouse.create({'name': health_center.name,'code': codeWH,'partner_id':health_center.partner_id.id,'healthcenter_stock_wh':health_center.id})

        # create location for pharmacy of health center
        # StockLocation = self.env['stock.location']
        # pharmacy_location = StockLocation.create({'name': 'Nhà thuốc ' + health_center.name, 'location_id': wh_health_center.lot_stock_id.id})

        #create Pharmacy default for health center
        # Pharmacy = self.env['sh.medical.health.center.pharmacy']
        # pharmacy_health_center = Pharmacy.create(
        #     {'name': health_center.name, 'institution': health_center.id, 'location_id': pharmacy_location.id, 'partner_id': health_center.partner_id.id})

        return health_center

    @api.onchange('state_id')
    def onchange_state(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id

class ResUsers(models.Model):
    _inherit = "res.users"

    institution = fields.Many2many('sh.medical.health.center', 'sh_users_health_center_rel', 'user_id', 'ins_id', string="Cơ sở y tế",store=True)

class stockWarehouse(models.Model):
    _inherit = ['stock.warehouse']

    healthcenter_stock_wh = fields.Many2one('sh.medical.health.center','Health center stock warehouse')

class stockLocation(models.Model):
    _inherit = ['stock.location']

    def name_get(self):
        ret_list = []
        for location in self:
            orig_location = location
            name = location.name
            while location.location_id and location.usage != 'view':
                location = location.location_id
                if not name:
                    raise UserError(_('You have to set a name for this location.'))
                name = location.name + "/" + name

            if self.env.context.get('view_only_name'):
                name = orig_location.name

            ret_list.append((orig_location.id, name))

        return ret_list


# Health Center Building
# class shealthCentersBuilding(models.Model):
#     _name = 'sh.medical.health.center.building'
#     _description = "Health Centers buildings"
#
#     @api.multi
#     def _ward_count(self):
#         oe_wards = self.env['sh.medical.health.center.ward']
#         for building in self:
#             domain = [('building', '=', building.id)]
#             wards_ids = oe_wards.search(domain)
#             wards = oe_wards.browse(wards_ids)
#             wa_count = 0
#             for war in wards:
#                 wa_count+=1
#             building.ward_count = wa_count
#         return True
#
#     @api.multi
#     def _bed_count(self):
#         oe_beds = self.env['sh.medical.health.center.beds']
#         for building in self:
#             domain = [('building', '=', building.id)]
#             beds_ids = oe_beds.search(domain)
#             beds = oe_beds.browse(beds_ids)
#             be_count = 0
#             for bed in beds:
#                 be_count+=1
#             building.bed_count = be_count
#         return True
#
#     name = fields.Char(string='Name', size=128, required=True, help="Name of the building within the institution")
#     institution = fields.Many2one('sh.medical.health.center', string='Health Center',required=True)
#     code = fields.Char (string='Code', size=64)
#     info = fields.Text (string='Extra Info')
#     ward_count = fields.Integer(compute=_ward_count, string="Wards")
#     bed_count = fields.Integer(compute=_bed_count, string="Beds")
#
#     _sql_constraints = [
#         ('name_uniq', 'unique (name)', 'The building name must be unique !')
#     ]

# Health Center Wards Management

class SHealthCentersWards(models.Model):
    _name = "sh.medical.health.center.ward"
    _description = "Information about Department of Health center"

    GENDER = [
        ('Men Ward','Men Ward'),
        ('Women Ward','Women Ward'),
        ('Unisex','Unisex'),
    ]

    WARD_STATES = [
        ('Beds Available','Beds Available'),
        ('Full','Full'),
    ]

    WARD_TYPE = [
        ('Examination', 'Examination'),
        ('Laboratory', 'Laboratory'),
        ('Imaging', 'Imaging'),
        ('Surgery', 'Surgery'),
        ('Inpatient', 'Inpatient'),
        ('Specialty', 'Specialty'),
    ]

    # @api.multi
    # def _bed_count(self):
    #     oe_beds = self.env['sh.medical.health.center.beds']
    #     for ward in self:
    #         domain = [('ward', '=', ward.id)]
    #         beds_ids = oe_beds.search(domain)
    #         beds = oe_beds.browse(beds_ids)
    #         be_count = 0
    #         for bed in beds:
    #             be_count+=1
    #         ward.bed_count = be_count
    #     return True

    @api.multi
    def _room_count(self):
        oe_rooms = self.env['sh.medical.health.center.ot']
        for ward in self:
            domain = [('department', '=', ward.id)]
            rooms_ids = oe_rooms.search(domain)
            rooms = oe_rooms.browse(rooms_ids)
            ro_count = 0
            for room in rooms:
                ro_count+=1
            ward.room_count = ro_count
        return True

    name = fields.Char(string='Name', size=128, required=True, help="Ward / Room code")
    institution = fields.Many2one('sh.medical.health.center',string='Health Center', required=True)
    # building = fields.Many2one('sh.medical.health.center.building',string='Building')
    floor = fields.Integer(string='Floor Number')
    private = fields.Boolean(string='Private Room',help="Check this option for private room")
    bio_hazard = fields.Boolean(string='Bio Hazard',help="Check this option if there is biological hazard")
    telephone = fields.Boolean(string='Telephone access')
    ac = fields.Boolean(string='Air Conditioning')
    private_bathroom = fields.Boolean(string='Private Bathroom')
    guest_sofa = fields.Boolean(string='Guest sofa-bed')
    tv = fields.Boolean(string='Television')
    internet = fields.Boolean(string='Internet Access')
    refrigerator = fields.Boolean(string='Refrigerator')
    microwave = fields.Boolean(string='Microwave')
    gender = fields.Selection(GENDER,string='Gender',default=lambda *a: 'Unisex')
    state = fields.Selection(WARD_STATES,string='Status',default='Beds Available')
    info = fields.Text('Extra Info')
    # bed_count = fields.Integer(compute=_bed_count, string="Beds")
    room_count = fields.Integer(compute=_room_count, string="Rooms")

    location_id = fields.Many2one('stock.location', string='Stock Location', domain="[('usage', '=', 'internal')]")

    type = fields.Selection(WARD_TYPE, string='Type', default='Specialty')

    # _sql_constraints = [
    #     ('name_ward_uniq', 'unique (name,building)', 'The ward name is already configured in selected building !')
    # ]
    _sql_constraints = [
        ('name_ward_uniq', 'unique (name,institution)', 'The ward name is already configured in selected institution !')
    ]

    @api.model
    def create(self, vals):
        if not(vals.get('location_id')):
            #TODO: CẦN SỬA KHI LÀM PHẦN MỀM VẬN HÀNH
            institution = self.env['sh.medical.health.center'].browse(vals['institution'])
            # institution_wh = self.env['stock.warehouse'].browse(institution.warehouse_ids[0].id)
            institution_wh = self.env.ref('stock.warehouse0')
            stockLocation = self.env['stock.location']
            #tao địa điểm kho cho Khoa
            ward_location = stockLocation.create({'name': vals['name'], 'location_id': institution_wh.lot_stock_id.id})
            vals['location_id'] = ward_location.id

        ward = super(SHealthCentersWards, self).create(vals)
        return ward

    # @api.onchange('location_id', 'institution')
    # def _change_location_id(self):
    #     if self.institution:
    #         if not self.location_id:
    #             raise Warning(_('Location of department must be filled!'))

# Beds Management
class shealthCentersBeds(models.Model):

    BED_TYPES = [
        ('Gatch Bed','Gatch Bed'),
        ('Electric','Electric'),
        ('Stretcher','Stretcher'),
        ('Low Bed','Low Bed'),
        ('Low Air Loss','Low Air Loss'),
        ('Circo Electric','Circo Electric'),
        ('Clinitron','Clinitron'),
    ]

    BED_STATES = [
        ('Free', 'Free'),
        ('Reserved', 'Reserved'),
        ('Occupied', 'Occupied'),
        ('Not Available', 'Not Available'),
    ]

    CHANGE_BED_STATUS = [
        ('Mark as Available', 'Mark as Available'),
        ('Mark as Reserved', 'Mark as Reserved'),
        ('Mark as Not Available', 'Mark as Not Available'),
    ]
    _name = 'sh.medical.health.center.beds'
    _description = "Information about the health centers beds"
    _inherits={
        'product.product': 'product_id',
    }

    product_id = fields.Many2one('product.product', string='Related Product', required=True, ondelete='cascade', help='Product-related data of the hospital beds')
    institution = fields.Many2one('sh.medical.health.center',string='Health Center')
    # building = fields.Many2one('sh.medical.health.center.building', string='Building')
    ward = fields.Many2one('sh.medical.health.center.ward','Ward', domain="[('building', '=', building)]", help="Ward or room", ondelete='cascade')
    bed_type = fields.Selection(BED_TYPES,string='Bed Type', required=True, default=lambda *a: 'Gatch Bed')
    telephone_number = fields.Char (string='Telephone Number', size=128, help="Telephone Number / Extension")
    info = fields.Text(string='Extra Info')
    state = fields.Selection(BED_STATES, string='Status', default='Free')
    change_bed_status = fields.Selection(CHANGE_BED_STATUS, string='Change Bed Status')
    list_price = fields.Float(default=0)

    @api.onchange('change_bed_status','state')
    def onchange_bed_status(self):
        res = {}
        if self.state and self.change_bed_status:
            if self.state=="Occupied":
                raise UserError(_('Bed status can not change if it already occupied!'))
            else:
                if self.change_bed_status== "Mark as Reserved":
                    self.state = "Reserved"
                elif self.change_bed_status== "Mark as Available":
                    self.state = "Free"
                else:
                    self.state = "Not Available"
        return res


    # Preventing deletion of a beds which is not in draft state
    @api.multi
    def unlink(self):
        for beds in self.filtered(lambda beds: beds.state not in ['Free','Not Available']):
            raise UserError(_('You can not delete bed(s) which is in "Reserved" or "Occupied" state !!'))
        return super(shealthCentersBeds, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name') and vals.get('ward'):
            query_bed = _("select count(*) from sh_medical_health_center_beds oeb, product_product pr, product_template pt where pr.id=oeb.product_id and pr.product_tmpl_id=pt.id and pt.name='%s' and oeb.ward=%s")%(str(vals.get('name')), str(vals.get('ward')))
            self.env.cr.execute(query_bed)
            val = self.env.cr.fetchone()
            if val and int(val[0]) > 0:
               raise UserError(_('The bed name is already configured in selected ward !'))
        if vals.get('change_bed_status') and vals.get('state') and vals.get('state')=="Occupied":
            raise AccessError(_('Bed status can not change if it already occupied!'))
        vals["is_bed"] = True
        beds = super(shealthCentersBeds, self).create(vals)
        return beds

    @api.multi
    def write(self, vals):
        if 'change_bed_status' in vals:
            if vals.get('change_bed_status') in ('Mark as Reserved','Mark as Not Available'):
                for beds in self.filtered(lambda beds: beds.state in ['Occupied']):
                    raise AccessError(_('Bed status can not change if it already occupied!'))
        return super(shealthCentersBeds, self).write(vals)

