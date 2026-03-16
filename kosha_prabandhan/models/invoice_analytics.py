from odoo import api, fields, models, tools


class InvoiceAnalytics(models.Model):
    _name = 'kosha.invoice.analytics'
    _description = 'Invoice Analytics'
    _auto = False
    _order = 'invoice_date desc'

    move_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    invoice_date = fields.Date(readonly=True)
    due_date = fields.Date(string='Due Date', readonly=True)
    move_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Credit Note'),
        ('in_refund', 'Debit Note'),
    ], readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], readonly=True)
    amount_total = fields.Float(readonly=True)
    amount_residual = fields.Float(string='Amount Due', readonly=True)
    amount_paid = fields.Float(readonly=True)
    payment_state = fields.Char(readonly=True)
    days_overdue = fields.Integer(readonly=True)
    aging_bucket = fields.Char(string='Aging Bucket', readonly=True)
    month = fields.Char(readonly=True)
    year = fields.Integer(readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    am.id,
                    am.id AS move_id,
                    am.partner_id,
                    am.invoice_date,
                    am.invoice_date_due AS due_date,
                    am.move_type,
                    am.state,
                    ABS(am.amount_total_signed) AS amount_total,
                    ABS(am.amount_residual_signed) AS amount_residual,
                    ABS(am.amount_total_signed) - ABS(am.amount_residual_signed) AS amount_paid,
                    am.payment_state,
                    CASE
                        WHEN am.invoice_date_due < CURRENT_DATE AND am.amount_residual_signed != 0
                        THEN (CURRENT_DATE - am.invoice_date_due)::int
                        ELSE 0
                    END AS days_overdue,
                    CASE
                        WHEN am.amount_residual_signed = 0 THEN 'Paid'
                        WHEN am.invoice_date_due >= CURRENT_DATE THEN 'Current'
                        WHEN (CURRENT_DATE - am.invoice_date_due) <= 30 THEN '1-30 Days'
                        WHEN (CURRENT_DATE - am.invoice_date_due) <= 60 THEN '31-60 Days'
                        WHEN (CURRENT_DATE - am.invoice_date_due) <= 90 THEN '61-90 Days'
                        ELSE '90+ Days'
                    END AS aging_bucket,
                    TO_CHAR(am.invoice_date, 'YYYY-MM') AS month,
                    EXTRACT(YEAR FROM am.invoice_date)::int AS year,
                    am.company_id
                FROM account_move am
                WHERE am.state = 'posted'
                  AND am.move_type IN ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')
            )
        """ % self._table)
