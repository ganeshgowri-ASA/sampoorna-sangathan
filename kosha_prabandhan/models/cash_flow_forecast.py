from odoo import api, fields, models, tools


class CashFlowForecast(models.Model):
    _name = 'kosha.cash.flow.forecast'
    _description = 'Cash Flow Forecast'
    _auto = False
    _order = 'forecast_date'

    forecast_date = fields.Date(readonly=True)
    month = fields.Char(readonly=True)
    year = fields.Integer(readonly=True)
    expected_inflow = fields.Float(string='Expected Inflow', readonly=True)
    expected_outflow = fields.Float(string='Expected Outflow', readonly=True)
    net_cash_flow = fields.Float(string='Net Cash Flow', readonly=True)
    cumulative_cash_flow = fields.Float(string='Cumulative Cash Flow', readonly=True)
    receivable_count = fields.Integer(string='Receivable Invoices', readonly=True)
    payable_count = fields.Integer(string='Payable Bills', readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY sub.forecast_date) AS id,
                    sub.forecast_date,
                    TO_CHAR(sub.forecast_date, 'YYYY-MM') AS month,
                    EXTRACT(YEAR FROM sub.forecast_date)::int AS year,
                    sub.expected_inflow,
                    sub.expected_outflow,
                    sub.expected_inflow - sub.expected_outflow AS net_cash_flow,
                    SUM(sub.expected_inflow - sub.expected_outflow)
                        OVER (PARTITION BY sub.company_id ORDER BY sub.forecast_date) AS cumulative_cash_flow,
                    sub.receivable_count,
                    sub.payable_count,
                    sub.company_id
                FROM (
                    SELECT
                        COALESCE(am.invoice_date_due, am.invoice_date)::date AS forecast_date,
                        am.company_id,
                        COALESCE(SUM(CASE
                            WHEN am.move_type IN ('out_invoice')
                            THEN ABS(am.amount_residual_signed)
                            ELSE 0
                        END), 0) AS expected_inflow,
                        COALESCE(SUM(CASE
                            WHEN am.move_type IN ('in_invoice')
                            THEN ABS(am.amount_residual_signed)
                            ELSE 0
                        END), 0) AS expected_outflow,
                        COUNT(CASE WHEN am.move_type = 'out_invoice' THEN 1 END)::int AS receivable_count,
                        COUNT(CASE WHEN am.move_type = 'in_invoice' THEN 1 END)::int AS payable_count
                    FROM account_move am
                    WHERE am.state = 'posted'
                      AND am.payment_state IN ('not_paid', 'partial')
                      AND am.move_type IN ('out_invoice', 'in_invoice')
                    GROUP BY COALESCE(am.invoice_date_due, am.invoice_date), am.company_id
                ) sub
            )
        """ % self._table)
