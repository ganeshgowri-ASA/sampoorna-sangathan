from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GstFiling(models.Model):
    _name = 'kosha.gst.filing'
    _description = 'GST Filing Status Tracker'
    _inherit = ['mail.thread']
    _order = 'period desc'
    _rec_name = 'display_name'

    period = fields.Char(
        string='Tax Period', required=True, tracking=True,
        help='e.g. 2025-04 for April 2025',
    )
    return_type = fields.Selection([
        ('gstr1', 'GSTR-1 (Outward Supplies)'),
        ('gstr3b', 'GSTR-3B (Summary Return)'),
        ('gstr9', 'GSTR-9 (Annual Return)'),
        ('gstr2a', 'GSTR-2A (Auto-drafted)'),
    ], string='Return Type', required=True, tracking=True)
    state = fields.Selection([
        ('not_due', 'Not Due'),
        ('pending', 'Pending'),
        ('filed', 'Filed'),
        ('late', 'Filed Late'),
        ('overdue', 'Overdue'),
    ], default='not_due', tracking=True, required=True)
    due_date = fields.Date(string='Due Date', required=True)
    filing_date = fields.Date(string='Filed On', tracking=True)
    arn_number = fields.Char(string='ARN Number', tracking=True)
    taxable_amount = fields.Float(
        string='Taxable Amount', compute='_compute_tax_amounts', store=True,
    )
    cgst_amount = fields.Float(
        string='CGST', compute='_compute_tax_amounts', store=True,
    )
    sgst_amount = fields.Float(
        string='SGST', compute='_compute_tax_amounts', store=True,
    )
    igst_amount = fields.Float(
        string='IGST', compute='_compute_tax_amounts', store=True,
    )
    total_tax = fields.Float(
        string='Total Tax', compute='_compute_tax_amounts', store=True,
    )
    invoice_count = fields.Integer(
        compute='_compute_tax_amounts', store=True,
    )
    notes = fields.Text()
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('unique_filing', 'unique(period, return_type, company_id)',
         'A filing record for this period and return type already exists.'),
    ]

    def _get_display_name(self):
        for rec in self:
            rec.display_name = '%s - %s' % (
                rec.period, dict(self._fields['return_type'].selection).get(rec.return_type, ''),
            )

    display_name = fields.Char(compute='_get_display_name')

    @api.depends('period', 'return_type')
    def _compute_tax_amounts(self):
        """Pull tax amounts from posted invoices for the period."""
        for rec in self:
            if not rec.period or not rec.return_type:
                rec.taxable_amount = rec.cgst_amount = rec.sgst_amount = 0
                rec.igst_amount = rec.total_tax = rec.invoice_count = 0
                continue

            move_type = 'out_invoice' if rec.return_type == 'gstr1' else 'in_invoice'
            # Parse period YYYY-MM
            try:
                year, month = rec.period.split('-')
                date_from = fields.Date.to_date('%s-%s-01' % (year, month))
                if int(month) == 12:
                    date_to = fields.Date.to_date('%s-01-01' % (int(year) + 1))
                else:
                    date_to = fields.Date.to_date('%s-%02d-01' % (year, int(month) + 1))
            except (ValueError, AttributeError):
                rec.taxable_amount = rec.cgst_amount = rec.sgst_amount = 0
                rec.igst_amount = rec.total_tax = rec.invoice_count = 0
                continue

            moves = self.env['account.move'].search([
                ('move_type', '=', move_type),
                ('state', '=', 'posted'),
                ('invoice_date', '>=', date_from),
                ('invoice_date', '<', date_to),
                ('company_id', '=', rec.company_id.id),
            ])
            rec.invoice_count = len(moves)
            rec.taxable_amount = sum(moves.mapped('amount_untaxed_signed'))

            # Aggregate tax lines
            cgst = sgst = igst = 0.0
            for move in moves:
                for tax_line in move.line_ids.filtered(
                    lambda l: l.tax_line_id
                ):
                    tax_name = (tax_line.tax_line_id.name or '').lower()
                    amt = abs(tax_line.balance)
                    if 'cgst' in tax_name:
                        cgst += amt
                    elif 'sgst' in tax_name:
                        sgst += amt
                    elif 'igst' in tax_name:
                        igst += amt
                    else:
                        # Default: split evenly as CGST+SGST
                        cgst += amt / 2
                        sgst += amt / 2

            rec.cgst_amount = cgst
            rec.sgst_amount = sgst
            rec.igst_amount = igst
            rec.total_tax = cgst + sgst + igst

    def action_mark_filed(self):
        for rec in self:
            if not rec.filing_date:
                rec.filing_date = fields.Date.today()
            if rec.filing_date > rec.due_date:
                rec.state = 'late'
            else:
                rec.state = 'filed'

    def action_mark_pending(self):
        self.write({'state': 'pending'})

    @api.model
    def _cron_check_overdue(self):
        """Mark filings as overdue if past due date and not filed."""
        overdue = self.search([
            ('state', 'in', ('not_due', 'pending')),
            ('due_date', '<', fields.Date.today()),
        ])
        overdue.write({'state': 'overdue'})
