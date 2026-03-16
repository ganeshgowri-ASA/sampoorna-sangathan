# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class PipelineAnalytics(models.Model):
    _name = 'sambandha.pipeline.analytics'
    _description = 'Pipeline Analytics'
    _auto = False
    _order = 'stage_id, id'

    lead_id = fields.Many2one('crm.lead', string='Lead', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    team_id = fields.Many2one('crm.team', string='Sales Team', readonly=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', readonly=True)
    country_id = fields.Many2one('res.country', string='Country', readonly=True)

    lead_type = fields.Selection([
        ('lead', 'Lead'),
        ('opportunity', 'Opportunity'),
    ], string='Type', readonly=True)
    expected_revenue = fields.Float(string='Expected Revenue', readonly=True)
    probability = fields.Float(string='Probability (%)', readonly=True)
    weighted_revenue = fields.Float(string='Weighted Revenue', readonly=True)
    sp_lead_score = fields.Integer(string='Lead Score', readonly=True)

    create_date = fields.Datetime(string='Created On', readonly=True)
    date_closed = fields.Datetime(string='Closed On', readonly=True)
    days_to_close = fields.Integer(string='Days to Close', readonly=True)
    days_in_stage = fields.Integer(string='Days in Stage', readonly=True)

    is_won = fields.Boolean(string='Won', readonly=True)
    is_lost = fields.Boolean(string='Lost', readonly=True)

    create_month = fields.Char(string='Month', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    l.id AS id,
                    l.id AS lead_id,
                    l.partner_id,
                    l.user_id,
                    l.team_id,
                    l.stage_id,
                    l.country_id,
                    l.type AS lead_type,
                    l.expected_revenue,
                    l.probability,
                    (l.expected_revenue * l.probability / 100.0) AS weighted_revenue,
                    l.sp_lead_score,
                    l.create_date,
                    l.date_closed,
                    CASE
                        WHEN l.date_closed IS NOT NULL
                        THEN EXTRACT(DAY FROM (l.date_closed - l.create_date))::int
                        ELSE NULL
                    END AS days_to_close,
                    EXTRACT(DAY FROM (NOW() - COALESCE(l.date_last_stage_update, l.create_date)))::int AS days_in_stage,
                    CASE WHEN l.probability = 100 THEN TRUE ELSE FALSE END AS is_won,
                    CASE WHEN l.active = FALSE AND l.probability = 0 THEN TRUE ELSE FALSE END AS is_lost,
                    TO_CHAR(l.create_date, 'YYYY-MM') AS create_month
                FROM crm_lead l
                WHERE l.type IN ('lead', 'opportunity')
            )
        """ % self._table)
