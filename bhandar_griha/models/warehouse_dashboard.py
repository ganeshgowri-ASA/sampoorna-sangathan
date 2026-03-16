from odoo import api, fields, models


class WarehouseDashboard(models.Model):
    _name = 'bhandar.griha.dashboard'
    _description = 'Warehouse Dashboard'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    current_stock = fields.Float(
        string='Current Stock', compute='_compute_stock_levels', store=False,
    )
    reserved_qty = fields.Float(
        string='Reserved Qty', compute='_compute_stock_levels', store=False,
    )
    available_qty = fields.Float(
        string='Available Qty', compute='_compute_stock_levels', store=False,
    )
    reorder_level = fields.Float(string='Reorder Level', default=0.0)
    reorder_qty = fields.Float(string='Reorder Quantity', default=0.0)
    is_below_reorder = fields.Boolean(
        string='Below Reorder Level', compute='_compute_is_below_reorder', store=False,
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ('warehouse_product_uniq', 'unique(warehouse_id, product_id)',
         'Dashboard entry must be unique per warehouse and product.'),
    ]

    @api.depends('warehouse_id', 'product_id')
    def _compute_name(self):
        for rec in self:
            wh = rec.warehouse_id.name or ''
            prod = rec.product_id.display_name or ''
            rec.name = f'{wh} - {prod}'

    def _compute_stock_levels(self):
        for rec in self:
            if rec.product_id and rec.warehouse_id:
                location = rec.warehouse_id.lot_stock_id
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', 'child_of', location.id),
                ])
                rec.current_stock = sum(quants.mapped('quantity'))
                rec.reserved_qty = sum(quants.mapped('reserved_quantity'))
                rec.available_qty = rec.current_stock - rec.reserved_qty
            else:
                rec.current_stock = 0.0
                rec.reserved_qty = 0.0
                rec.available_qty = 0.0

    @api.depends('current_stock', 'reorder_level')
    def _compute_is_below_reorder(self):
        for rec in self:
            rec.is_below_reorder = (
                rec.reorder_level > 0 and rec.current_stock < rec.reorder_level
            )

    @api.model
    def _cron_check_reorder_levels(self):
        """Cron job: check all dashboard entries and create activities for low stock."""
        records = self.search([])
        for rec in records:
            rec._compute_stock_levels()
            if rec.is_below_reorder:
                warehouse_manager = rec.warehouse_id.partner_id or self.env.user.partner_id
                rec.product_id.activity_schedule(
                    'mail.mail_activity_data_warning',
                    summary=f'Low Stock Alert: {rec.product_id.display_name}',
                    note=(
                        f'Stock for <b>{rec.product_id.display_name}</b> in '
                        f'<b>{rec.warehouse_id.name}</b> is at '
                        f'<b>{rec.current_stock}</b>, below reorder level '
                        f'<b>{rec.reorder_level}</b>.'
                    ),
                    user_id=self.env.user.id,
                )
