# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class CustomerJourney(models.Model):
    _name = 'sambandha.customer.journey'
    _description = 'Customer Journey Timeline'
    _auto = False
    _order = 'event_date desc'

    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    event_date = fields.Datetime(string='Date', readonly=True)
    event_type = fields.Selection([
        ('lead_created', 'Lead Created'),
        ('stage_change', 'Stage Change'),
        ('email_sent', 'Email Sent'),
        ('email_received', 'Email Received'),
        ('meeting', 'Meeting'),
        ('note', 'Note/Comment'),
        ('sale_order', 'Sale Order'),
        ('won', 'Deal Won'),
        ('lost', 'Deal Lost'),
    ], string='Event Type', readonly=True)
    summary = fields.Char(string='Summary', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    revenue_impact = fields.Float(string='Revenue Impact', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                -- Lead creation events
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    l.partner_id,
                    l.create_date AS event_date,
                    'lead_created' AS event_type,
                    'Lead created: ' || COALESCE(l.name, 'Untitled') AS summary,
                    l.user_id,
                    l.id AS lead_id,
                    NULL::int AS sale_order_id,
                    l.expected_revenue AS revenue_impact
                FROM crm_lead l
                WHERE l.partner_id IS NOT NULL

                UNION ALL

                -- Email messages on leads
                SELECT
                    ROW_NUMBER() OVER () + 1000000 AS id,
                    l.partner_id,
                    m.date AS event_date,
                    CASE
                        WHEN m.message_type = 'email' AND m.author_id = l.partner_id
                        THEN 'email_received'
                        ELSE 'email_sent'
                    END AS event_type,
                    COALESCE(m.subject, 'Email') AS summary,
                    m.create_uid AS user_id,
                    l.id AS lead_id,
                    NULL::int AS sale_order_id,
                    0 AS revenue_impact
                FROM mail_message m
                JOIN crm_lead l ON m.res_id = l.id AND m.model = 'crm.lead'
                WHERE m.message_type = 'email'
                    AND l.partner_id IS NOT NULL

                UNION ALL

                -- Comments/notes on leads
                SELECT
                    ROW_NUMBER() OVER () + 2000000 AS id,
                    l.partner_id,
                    m.date AS event_date,
                    'note' AS event_type,
                    COALESCE(m.subject, 'Note added') AS summary,
                    m.create_uid AS user_id,
                    l.id AS lead_id,
                    NULL::int AS sale_order_id,
                    0 AS revenue_impact
                FROM mail_message m
                JOIN crm_lead l ON m.res_id = l.id AND m.model = 'crm.lead'
                WHERE m.message_type = 'comment'
                    AND l.partner_id IS NOT NULL

                UNION ALL

                -- Meetings linked to leads
                SELECT
                    ROW_NUMBER() OVER () + 3000000 AS id,
                    l.partner_id,
                    ce.start AS event_date,
                    'meeting' AS event_type,
                    'Meeting: ' || COALESCE(ce.name, 'Untitled') AS summary,
                    ce.user_id,
                    l.id AS lead_id,
                    NULL::int AS sale_order_id,
                    0 AS revenue_impact
                FROM calendar_event ce
                JOIN crm_lead l ON ce.opportunity_id = l.id
                WHERE l.partner_id IS NOT NULL

                UNION ALL

                -- Sale orders
                SELECT
                    ROW_NUMBER() OVER () + 4000000 AS id,
                    so.partner_id,
                    so.date_order AS event_date,
                    'sale_order' AS event_type,
                    'Order: ' || so.name AS summary,
                    so.user_id,
                    NULL::int AS lead_id,
                    so.id AS sale_order_id,
                    so.amount_total AS revenue_impact
                FROM sale_order so
                WHERE so.partner_id IS NOT NULL

                UNION ALL

                -- Won deals
                SELECT
                    ROW_NUMBER() OVER () + 5000000 AS id,
                    l.partner_id,
                    l.date_closed AS event_date,
                    'won' AS event_type,
                    'Deal Won: ' || COALESCE(l.name, 'Untitled') AS summary,
                    l.user_id,
                    l.id AS lead_id,
                    NULL::int AS sale_order_id,
                    l.expected_revenue AS revenue_impact
                FROM crm_lead l
                WHERE l.probability = 100
                    AND l.date_closed IS NOT NULL
                    AND l.partner_id IS NOT NULL

                UNION ALL

                -- Lost deals
                SELECT
                    ROW_NUMBER() OVER () + 6000000 AS id,
                    l.partner_id,
                    l.date_closed AS event_date,
                    'lost' AS event_type,
                    'Deal Lost: ' || COALESCE(l.name, 'Untitled') AS summary,
                    l.user_id,
                    l.id AS lead_id,
                    NULL::int AS sale_order_id,
                    l.expected_revenue AS revenue_impact
                FROM crm_lead l
                WHERE l.active = FALSE
                    AND l.probability = 0
                    AND l.date_closed IS NOT NULL
                    AND l.partner_id IS NOT NULL
            )
        """ % self._table)
