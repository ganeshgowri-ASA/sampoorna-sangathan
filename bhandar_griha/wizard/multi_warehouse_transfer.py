from odoo import api, fields, models
from odoo.exceptions import UserError


class MultiWarehouseTransfer(models.TransientModel):
    _name = 'bhandar.griha.transfer.wizard'
    _description = 'Multi-Warehouse Transfer Wizard'

    source_warehouse_id = fields.Many2one(
        'stock.warehouse', string='Source Warehouse', required=True,
    )
    dest_warehouse_id = fields.Many2one(
        'stock.warehouse', string='Destination Warehouse', required=True,
    )
    line_ids = fields.One2many(
        'bhandar.griha.transfer.wizard.line', 'wizard_id', string='Transfer Lines',
    )
    scheduled_date = fields.Datetime(
        string='Scheduled Date', default=fields.Datetime.now, required=True,
    )

    @api.constrains('source_warehouse_id', 'dest_warehouse_id')
    def _check_warehouses(self):
        for rec in self:
            if rec.source_warehouse_id == rec.dest_warehouse_id:
                raise UserError('Source and destination warehouses must be different.')

    def action_create_transfer(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError('Please add at least one product line.')

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', self.source_warehouse_id.id),
        ], limit=1)

        if not picking_type:
            raise UserError(
                f'No internal transfer type found for warehouse '
                f'{self.source_warehouse_id.name}.'
            )

        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': self.source_warehouse_id.lot_stock_id.id,
            'location_dest_id': self.dest_warehouse_id.lot_stock_id.id,
            'scheduled_date': self.scheduled_date,
            'origin': f'Multi-WH Transfer: {self.source_warehouse_id.name} → {self.dest_warehouse_id.name}',
            'move_ids': [],
        }

        move_vals_list = []
        for line in self.line_ids:
            move_vals_list.append((0, 0, {
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'location_id': self.source_warehouse_id.lot_stock_id.id,
                'location_dest_id': self.dest_warehouse_id.lot_stock_id.id,
            }))
        picking_vals['move_ids'] = move_vals_list

        picking = self.env['stock.picking'].create(picking_vals)
        picking.action_confirm()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfer Created',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }


class MultiWarehouseTransferLine(models.TransientModel):
    _name = 'bhandar.griha.transfer.wizard.line'
    _description = 'Transfer Wizard Line'

    wizard_id = fields.Many2one(
        'bhandar.griha.transfer.wizard', string='Wizard', required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
    )
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
