from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    dashboard_line_ids = fields.One2many(
        'bhandar.griha.dashboard', 'warehouse_id',
        string='Dashboard Lines',
    )
