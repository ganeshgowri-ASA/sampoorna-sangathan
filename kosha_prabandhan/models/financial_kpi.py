from odoo import api, fields, models, tools


class FinancialKpi(models.Model):
    _name = 'kosha.financial.kpi'
    _description = 'Financial KPI Dashboard'
    _auto = False
    _order = 'kpi_date desc'

    kpi_date = fields.Date(readonly=True)
    month = fields.Char(readonly=True)
    year = fields.Integer(readonly=True)
    total_revenue = fields.Float(string='Total Revenue', readonly=True)
    total_expenses = fields.Float(string='Total Expenses', readonly=True)
    net_profit = fields.Float(string='Net Profit', readonly=True)
    profit_margin = fields.Float(string='Profit Margin (%)', readonly=True)
    accounts_receivable = fields.Float(string='Accounts Receivable', readonly=True)
    accounts_payable = fields.Float(string='Accounts Payable', readonly=True)
    invoice_count = fields.Integer(string='Invoice Count', readonly=True)
    bill_count = fields.Integer(string='Bill Count', readonly=True)
    currency_count = fields.Integer(string='Currencies Used', readonly=True)
    has_foreign_currency = fields.Boolean(string='Multi-Currency', readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    sub.kpi_date,
                    TO_CHAR(sub.kpi_date, 'YYYY-MM') AS month,
                    EXTRACT(YEAR FROM sub.kpi_date)::int AS year,
                    sub.total_revenue,
                    sub.total_expenses,
                    sub.total_revenue - sub.total_expenses AS net_profit,
                    CASE
                        WHEN sub.total_revenue > 0
                        THEN ROUND(((sub.total_revenue - sub.total_expenses) / sub.total_revenue * 100)::numeric, 2)
                        ELSE 0
                    END AS profit_margin,
                    sub.accounts_receivable,
                    sub.accounts_payable,
                    sub.invoice_count,
                    sub.bill_count,
                    sub.currency_count,
                    sub.has_foreign_currency,
                    sub.company_id
                FROM (
                    SELECT
                        DATE_TRUNC('month', am.invoice_date)::date AS kpi_date,
                        am.company_id,
                        COALESCE(SUM(CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total_signed ELSE 0 END), 0) AS total_revenue,
                        COALESCE(SUM(CASE WHEN am.move_type = 'in_invoice' THEN ABS(am.amount_total_signed) ELSE 0 END), 0) AS total_expenses,
                        COALESCE(SUM(CASE WHEN am.move_type = 'out_invoice' THEN am.amount_residual_signed ELSE 0 END), 0) AS accounts_receivable,
                        COALESCE(SUM(CASE WHEN am.move_type = 'in_invoice' THEN ABS(am.amount_residual_signed) ELSE 0 END), 0) AS accounts_payable,
                        COUNT(CASE WHEN am.move_type = 'out_invoice' THEN 1 END)::int AS invoice_count,
                        COUNT(CASE WHEN am.move_type = 'in_invoice' THEN 1 END)::int AS bill_count,
                        COUNT(DISTINCT am.currency_id)::int AS currency_count,
                        CASE WHEN COUNT(DISTINCT am.currency_id) > 1 THEN true ELSE false END AS has_foreign_currency
                    FROM account_move am
                    WHERE am.state = 'posted'
                      AND am.move_type IN ('out_invoice', 'in_invoice')
                      AND am.invoice_date IS NOT NULL
                    GROUP BY DATE_TRUNC('month', am.invoice_date), am.company_id
                ) sub
            )
        """ % self._table)
