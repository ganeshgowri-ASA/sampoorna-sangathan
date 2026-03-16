from odoo import api, fields, models


class VendorRating(models.Model):
    _name = 'bhandar.griha.vendor.rating'
    _description = 'Vendor Rating'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner', string='Vendor', required=True,
        domain=[('supplier_rank', '>', 0)], tracking=True,
    )
    rating_date = fields.Date(
        string='Rating Date', default=fields.Date.context_today, required=True,
    )
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order',
    )
    delivery_score = fields.Float(
        string='Delivery Score (1-5)', default=3.0, tracking=True,
    )
    quality_score = fields.Float(
        string='Quality Score (1-5)', default=3.0, tracking=True,
    )
    price_score = fields.Float(
        string='Price Score (1-5)', default=3.0, tracking=True,
    )
    overall_score = fields.Float(
        string='Overall Score', compute='_compute_overall_score', store=True,
    )
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )

    @api.depends('delivery_score', 'quality_score', 'price_score')
    def _compute_overall_score(self):
        for rec in self:
            rec.overall_score = (
                rec.delivery_score + rec.quality_score + rec.price_score
            ) / 3.0

    @api.constrains('delivery_score', 'quality_score', 'price_score')
    def _check_scores(self):
        for rec in self:
            for field_name in ('delivery_score', 'quality_score', 'price_score'):
                val = getattr(rec, field_name)
                if val < 0 or val > 5:
                    raise models.ValidationError(
                        f'{field_name.replace("_", " ").title()} must be between 0 and 5.'
                    )
