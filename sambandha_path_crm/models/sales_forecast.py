# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class SalesForecast(models.Model):
    _name = 'sambandha.sales.forecast'
    _description = 'Sales Forecasting Analytics'
    _auto = False
    _order = 'forecast_month desc'

    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    team_id = fields.Many2one('crm.team', string='Sales Team', readonly=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)

    forecast_month = fields.Char(string='Forecast Month', readonly=True)
    forecast_quarter = fields.Char(string='Quarter', readonly=True)

    # Pipeline metrics
    opportunity_count = fields.Integer(string='Opportunities', readonly=True)
    expected_revenue = fields.Float(string='Expected Revenue', readonly=True)
    weighted_revenue = fields.Float(string='Weighted Revenue', readonly=True)
    avg_probability = fields.Float(string='Avg Probability (%)', readonly=True)

    # Historical metrics
    won_revenue = fields.Float(string='Won Revenue', readonly=True)
    won_count = fields.Integer(string='Won Deals', readonly=True)
    lost_count = fields.Integer(string='Lost Deals', readonly=True)
    win_rate = fields.Float(string='Win Rate (%)', readonly=True)
    avg_deal_size = fields.Float(string='Avg Deal Size', readonly=True)
    avg_days_to_close = fields.Float(string='Avg Days to Close', readonly=True)

    # Forecast
    forecast_revenue = fields.Float(
        string='Forecast Revenue', readonly=True,
        help='Predicted revenue = weighted pipeline + historical win rate adjustment',
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH monthly_pipeline AS (
                    SELECT
                        TO_CHAR(COALESCE(l.date_deadline, l.create_date), 'YYYY-MM') AS forecast_month,
                        'Q' || EXTRACT(QUARTER FROM COALESCE(l.date_deadline, l.create_date))
                            || ' ' || EXTRACT(YEAR FROM COALESCE(l.date_deadline, l.create_date)) AS forecast_quarter,
                        l.user_id,
                        l.team_id,
                        l.stage_id,
                        l.partner_id,
                        COUNT(*) AS opportunity_count,
                        SUM(l.expected_revenue) AS expected_revenue,
                        SUM(l.expected_revenue * l.probability / 100.0) AS weighted_revenue,
                        AVG(l.probability) AS avg_probability
                    FROM crm_lead l
                    WHERE l.type = 'opportunity'
                        AND l.active = TRUE
                        AND l.probability < 100
                    GROUP BY
                        TO_CHAR(COALESCE(l.date_deadline, l.create_date), 'YYYY-MM'),
                        forecast_quarter,
                        l.user_id, l.team_id, l.stage_id, l.partner_id
                ),
                historical_wins AS (
                    SELECT
                        l.user_id,
                        l.team_id,
                        COUNT(*) FILTER (WHERE l.probability = 100) AS won_count,
                        COUNT(*) FILTER (WHERE l.active = FALSE AND l.probability = 0) AS lost_count,
                        COALESCE(SUM(l.expected_revenue) FILTER (WHERE l.probability = 100), 0) AS won_revenue,
                        CASE
                            WHEN COUNT(*) > 0
                            THEN (COUNT(*) FILTER (WHERE l.probability = 100))::float / COUNT(*)::float * 100
                            ELSE 0
                        END AS win_rate,
                        COALESCE(AVG(l.expected_revenue) FILTER (WHERE l.probability = 100), 0) AS avg_deal_size,
                        COALESCE(
                            AVG(EXTRACT(DAY FROM (l.date_closed - l.create_date)))
                            FILTER (WHERE l.probability = 100 AND l.date_closed IS NOT NULL), 0
                        ) AS avg_days_to_close
                    FROM crm_lead l
                    WHERE l.type = 'opportunity'
                    GROUP BY l.user_id, l.team_id
                )
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    p.forecast_month,
                    p.forecast_quarter,
                    p.user_id,
                    p.team_id,
                    p.stage_id,
                    p.partner_id,
                    p.opportunity_count,
                    p.expected_revenue,
                    p.weighted_revenue,
                    p.avg_probability,
                    COALESCE(h.won_revenue, 0) AS won_revenue,
                    COALESCE(h.won_count, 0) AS won_count,
                    COALESCE(h.lost_count, 0) AS lost_count,
                    COALESCE(h.win_rate, 0) AS win_rate,
                    COALESCE(h.avg_deal_size, 0) AS avg_deal_size,
                    COALESCE(h.avg_days_to_close, 0) AS avg_days_to_close,
                    p.weighted_revenue * (1 + COALESCE(h.win_rate, 50) / 200.0) AS forecast_revenue
                FROM monthly_pipeline p
                LEFT JOIN historical_wins h
                    ON p.user_id = h.user_id AND p.team_id = h.team_id
            )
        """ % self._table)
