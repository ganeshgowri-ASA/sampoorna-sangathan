from odoo import api, fields, models, tools


class GstComplianceReport(models.Model):
    _name = 'kosha.gst.compliance'
    _description = 'GST Compliance Report'
    _auto = False
    _order = 'tax_month desc'

    tax_month = fields.Char(string='Tax Period', readonly=True)
    year = fields.Integer(readonly=True)
    move_type = fields.Selection([
        ('out_invoice', 'Sales (GSTR-1)'),
        ('in_invoice', 'Purchases (GSTR-3B)'),
    ], string='Type', readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True)
    partner_vat = fields.Char(string='GSTIN', readonly=True)
    base_amount = fields.Float(string='Taxable Amount', readonly=True)
    tax_amount = fields.Float(string='Tax Amount', readonly=True)
    total_amount = fields.Float(string='Total Amount', readonly=True)
    tax_name = fields.Char(string='Tax', readonly=True)
    tax_rate = fields.Float(string='Tax Rate (%)', readonly=True)
    invoice_count = fields.Integer(readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    TO_CHAR(am.invoice_date, 'YYYY-MM') AS tax_month,
                    EXTRACT(YEAR FROM am.invoice_date)::int AS year,
                    am.move_type,
                    am.partner_id,
                    rp.vat AS partner_vat,
                    COALESCE(at.name ->> 'en_US', at.name ->> 'en_IN', (at.name::text)) AS tax_name,
                    CASE
                        WHEN at.amount_type = 'percent' THEN at.amount
                        ELSE 0
                    END AS tax_rate,
                    SUM(ABS(aml.balance)) AS base_amount,
                    SUM(ABS(aml.balance) * COALESCE(at.amount, 0) / 100) AS tax_amount,
                    SUM(ABS(aml.balance) * (1 + COALESCE(at.amount, 0) / 100)) AS total_amount,
                    COUNT(DISTINCT am.id)::int AS invoice_count,
                    am.company_id
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                LEFT JOIN res_partner rp ON am.partner_id = rp.id
                LEFT JOIN account_move_line_account_tax_rel aml_at
                    ON aml_at.account_move_line_id = aml.id
                LEFT JOIN account_tax at ON aml_at.account_tax_id = at.id
                WHERE am.state = 'posted'
                  AND am.move_type IN ('out_invoice', 'in_invoice')
                  AND aml.display_type = 'product'
                  AND am.invoice_date IS NOT NULL
                GROUP BY
                    TO_CHAR(am.invoice_date, 'YYYY-MM'),
                    EXTRACT(YEAR FROM am.invoice_date),
                    am.move_type,
                    am.partner_id,
                    rp.vat,
                    at.name,
                    at.amount_type,
                    at.amount,
                    am.company_id
            )
        """ % self._table)
