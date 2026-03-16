from odoo import models, fields, api


class StockWarehouseExtension(models.Model):
    _inherit = 'stock.warehouse'

    utilization_rate = fields.Float(
        string='Utilization Rate (%)',
        compute='_compute_utilization_rate',
        store=True,
        help='Percentage of warehouse capacity currently in use',
    )
    capacity_limit = fields.Integer(
        string='Capacity Limit (Units)',
        default=0,
        help='Maximum number of units this warehouse can hold. 0 = unlimited.',
    )
    current_stock_count = fields.Integer(
        string='Current Stock Count',
        compute='_compute_utilization_rate',
        store=True,
    )
    movement_frequency = fields.Float(
        string='Movement Frequency (Daily Avg)',
        compute='_compute_movement_frequency',
        help='Average number of stock moves per day over the last 30 days',
    )
    last_analytics_update = fields.Datetime(
        string='Last Analytics Update',
        readonly=True,
    )

    @api.depends('capacity_limit', 'lot_stock_id')
    def _compute_utilization_rate(self):
        for warehouse in self:
            quants = self.env['stock.quant'].search([
                ('location_id', 'child_of', warehouse.lot_stock_id.id),
                ('quantity', '>', 0),
            ])
            total_qty = sum(quants.mapped('quantity'))
            warehouse.current_stock_count = int(total_qty)
            if warehouse.capacity_limit > 0:
                warehouse.utilization_rate = min(
                    (total_qty / warehouse.capacity_limit) * 100, 100.0
                )
            else:
                warehouse.utilization_rate = 0.0

    def _compute_movement_frequency(self):
        for warehouse in self:
            thirty_days_ago = fields.Datetime.subtract(
                fields.Datetime.now(), days=30
            )
            move_count = self.env['stock.move'].search_count([
                '|',
                ('location_id', 'child_of', warehouse.lot_stock_id.id),
                ('location_dest_id', 'child_of', warehouse.lot_stock_id.id),
                ('date', '>=', thirty_days_ago),
                ('state', '=', 'done'),
            ])
            warehouse.movement_frequency = round(move_count / 30.0, 2)

    def action_refresh_analytics(self):
        self._compute_utilization_rate()
        self._compute_movement_frequency()
        self.write({'last_analytics_update': fields.Datetime.now()})
        return True
