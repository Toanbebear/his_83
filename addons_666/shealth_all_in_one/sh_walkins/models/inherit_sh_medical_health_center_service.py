from odoo import api, fields, models, _

# Services
class InheritSHealthServices(models.Model):
    _inherit = "sh.medical.health.center.service"

    def name_get(self):
        result = super(InheritSHealthServices, self).name_get()
        if self._context.get('name_service_with_pathology'):
            new_result = []
            for service in result:
                record = self.env['sh.medical.health.center.service'].browse(service[0])
                name = '[%s] %s' % (record.default_code, record.name)
                for rec in record:
                    if rec.pathology:
                        name += ' - [ %s ]' % rec.pathology.name
                    else:
                        name += ''
                    new_result.append((service[0], name))
            return new_result
        return result
