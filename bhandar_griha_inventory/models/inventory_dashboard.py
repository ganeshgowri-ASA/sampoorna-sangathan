from odoo import models, fields, api


class BhandarGrihaDashboard(models.Model):
    _name = 'bhandar.griha.dashboard'
    _description = 'Bhandar Griha Inventory Dashboard'
    _inherit = ['sangathan.audit.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Dashboard Entry',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'bhandar.griha.dashboard'
        ) or 'New',
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        required=True,
    )
    total_products = fields.Integer(
        string='Total Products',
        compute='_compute_kpis',
        store=True,
    )
    total_stock_value = fields.Float(
        string='Total Stock Value',
        compute='_compute_kpis',
        store=True,
    )
    low_stock_count = fields.Integer(
        string='Low Stock Alerts',
        compute='_compute_kpis',
        store=True,
    )
    incoming_moves = fields.Integer(
        string='Incoming Moves (Today)',
        compute='_compute_move_summary',
    )
    outgoing_moves = fields.Integer(
        string='Outgoing Moves (Today)',
        compute='_compute_move_summary',
    )
    internal_moves = fields.Integer(
        string='Internal Moves (Today)',
        compute='_compute_move_summary',
    )
    state = fields.Selection([
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ], string='Status', compute='_compute_state', store=True)

    @api.depends('warehouse_id')
    def _compute_kpis(self):
        for rec in self:
            if not rec.warehouse_id:
                rec.total_products = 0
                rec.total_stock_value = 0.0
                rec.low_stock_count = 0
                continue
            quants = self.env['stock.quant'].search([
                ('location_id', 'child_of', rec.warehouse_id.lot_stock_id.id),
                ('quantity', '>', 0),
            ])
            rec.total_products = len(quants.mapped('product_id'))
            rec.total_stock_value = sum(
                q.quantity * q.product_id.standard_price for q in quants
            )
            # Low stock: products with qty below their reorder min
            replenish_rules = self.env['bhandar.griha.replenishment'].search([
                ('warehouse_id', '=', rec.warehouse_id.id),
                ('active', '=', True),
            ])
            low_count = 0
            for rule in replenish_rules:
                product_quants = quants.filtered(
                    lambda q: q.product_id == rule.product_id
                )
                on_hand = sum(product_quants.mapped('quantity'))
                if on_hand <= rule.min_qty:
                    low_count += 1
            rec.low_stock_count = low_count

    def _compute_move_summary(self):
        today_start = fields.Datetime.start_of(fields.Datetime.now(), 'day')
        today_end = fields.Datetime.end_of(fields.Datetime.now(), 'day')
        for rec in self:
            if not rec.warehouse_id:
                rec.incoming_moves = 0
                rec.outgoing_moves = 0
                rec.internal_moves = 0
                continue
            loc_id = rec.warehouse_id.lot_stock_id.id
            base_domain = [
                ('date', '>=', today_start),
                ('date', '<=', today_end),
                ('state', '=', 'done'),
            ]
            rec.incoming_moves = self.env['stock.move'].search_count(
                base_domain + [('location_dest_id', 'child_of', loc_id)]
            )
            rec.outgoing_moves = self.env['stock.move'].search_count(
                base_domain + [('location_id', 'child_of', loc_id)]
            )
            rec.internal_moves = self.env['stock.move'].search_count(
                base_domain + [
                    ('location_id', 'child_of', loc_id),
                    ('location_dest_id', 'child_of', loc_id),
                ]
            )

    @api.depends('low_stock_count')
    def _compute_state(self):
        for rec in self:
            if rec.low_stock_count >= 10:
                rec.state = 'critical'
            elif rec.low_stock_count >= 5:
                rec.state = 'warning'
            else:
                rec.state = 'normal'

    def action_refresh_kpis(self):
        self._compute_kpis()
        self._compute_move_summary()
        return True

    @api.model
    def action_open_dashboard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inventory Dashboard',
            'res_model': 'bhandar.griha.dashboard',
            'view_mode': 'tree,form,graph,pivot',
            'target': 'current',
        }
