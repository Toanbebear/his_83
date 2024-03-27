# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import logging

from odoo.tools.sql import column_exists, table_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    print('Xóa constraint')
    cr.execute(
        """
        ALTER TABLE purchase_order
        DROP CONSTRAINT purchase_order_name_partner_uniq;
    """
    )
