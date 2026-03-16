from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BhandarGrihaReplenishment(models.Model):
    _name = 'bhandar.griha.replenishment'
    _description = 'Bhandar Griha Smart Replenishment Rule'
    _inherit = ['sangathan.audit.mixin']
    _order = 'product_id, warehouse_id'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain=[('type', '=', 'product')],
    )
    product_tmpl_id = fields.Many2one(
        related='product_id.product_tmpl_id',
        string='Product Template',
        store=True,
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
    )
    min_qty = fields.Float(
        string='Minimum Quantity',
        required=True,
        default=0.0,
        help='When on-hand drops to or below this level, replenishment triggers.',
    )
    max_qty = fields.Float(
        string='Maximum Quantity',
        required=True,
        default=0.0,
        help='Replenishment will order up to this quantity.',
    )
    on_hand_qty = fields.Float(
        string='On Hand',
        compute='_compute_on_hand_qty',
    )
    supplier_id = fields.Many2one(
        'res.partner',
        string='Preferred Supplier',
        domain=[('supplier_rank', '>', 0)],
    )
    auto_create_po = fields.Boolean(
        string='Auto-Create Purchase Order',
        default=True,
    )
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('ok', 'OK'),
        ('low', 'Low Stock'),
        ('critical', 'Critical'),
    ], string='Status', compute='_compute_state', store=True)
    last_replenishment_date = fields.Datetime(
        string='Last Replenishment',
        readonly=True,
    )

    _sql_constraints = [
        (
            'unique_product_warehouse',
            'UNIQUE(product_id, warehouse_id)',
            'A replenishment rule already exists for this product/warehouse combination.',
        ),
    ]

    @api.constrains('min_qty', 'max_qty')
    def _check_quantities(self):
        for rule in self:
            if rule.max_qty < rule.min_qty:
                raise ValidationError(
                    _('Maximum quantity must be greater than or equal to minimum quantity.')
                )
            if rule.min_qty < 0 or rule.max_qty < 0:
                raise ValidationError(
                    _('Quantities must be non-negative.')
                )

    def _compute_on_hand_qty(self):
        for rule in self:
            quants = self.env['stock.quant'].search([
                ('product_id', '=', rule.product_id.id),
                ('location_id', 'child_of', rule.warehouse_id.lot_stock_id.id),
                ('quantity', '>', 0),
            ])
            rule.on_hand_qty = sum(quants.mapped('quantity'))

    @api.depends('min_qty', 'on_hand_qty')
    def _compute_state(self):
        for rule in self:
            rule._compute_on_hand_qty()
            if rule.on_hand_qty <= 0:
                rule.state = 'critical'
            elif rule.on_hand_qty <= rule.min_qty:
                rule.state = 'low'
            else:
                rule.state = 'ok'

    def action_trigger_replenishment(self):
        for rule in self:
            if not rule.auto_create_po:
                continue
            if rule.on_hand_qty >= rule.min_qty:
                continue
            qty_to_order = rule.max_qty - rule.on_hand_qty
            if qty_to_order <= 0:
                continue

            supplier = rule.supplier_id
            if not supplier:
                supplierinfos = self.env['product.supplierinfo'].search([
                    ('product_tmpl_id', '=', rule.product_tmpl_id.id),
                ], limit=1)
                supplier = supplierinfos.partner_id if supplierinfos else False

            if not supplier:
                continue

            po = self.env['purchase.order'].create({
                'partner_id': supplier.id,
                'picking_type_id': rule.warehouse_id.in_type_id.id,
            })
            self.env['purchase.order.line'].create({
                'order_id': po.id,
                'product_id': rule.product_id.id,
                'product_qty': qty_to_order,
                'name': rule.product_id.display_name,
                'price_unit': rule.product_id.standard_price,
                'product_uom': rule.product_id.uom_po_id.id,
                'date_planned': fields.Datetime.now(),
            })
            rule.last_replenishment_date = fields.Datetime.now()

        return True

    @api.model
    def cron_check_replenishment(self):
        rules = self.search([('active', '=', True), ('auto_create_po', '=', True)])
        for rule in rules:
            rule._compute_on_hand_qty()
            if rule.on_hand_qty <= rule.min_qty:
                rule.action_trigger_replenishment()
        return True
