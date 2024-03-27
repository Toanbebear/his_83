
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError

class ShealthServicesWalkinAnalysis(models.Model):
    _name = 'analysis.shealth.services.walkin'
    _description = "Phân tích: Dịch vụ theo phiếu khám bệnh"
    _auto = False

    patient = fields.Many2one('sh.medical.patient', 'Bệnh nhân')
    product_id = fields.Many2one('sh.medical.health.center.service', 'Dịch vụ')
    product_name = fields.Char('Sản phẩm')
    room_name = fields.Char('Phòng khám')
    walkin_date = fields.Datetime('Ngày khám')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT
                service.id AS id,
                service.product_id as product_id, 
                product_template.name as product_name, 
                walkin.date AS walkin_date, 
                ot.name AS room_name,
                walkin.patient
            FROM sh_walkin_service_rel ws
            LEFT JOIN sh_medical_health_center_service service on (ws.service_id = service.id)
            LEFT JOIN sh_medical_appointment_register_walkin walkin on (ws.walkin_id = walkin.id)   
            LEFT JOIN product_product ON (product_product.id = service.product_id)
            LEFT JOIN product_template ON (product_template.id = product_product.product_tmpl_id)         
            LEFT JOIN sh_medical_health_center_ot ot ON (walkin.service_room = ot.id)         
        )""" % (self._table,))
