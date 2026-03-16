# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Lead scoring
    sp_lead_score = fields.Integer(
        string='Lead Score', default=0, tracking=True,
        help='Computed score based on lead scoring rules',
    )
    sp_score_details = fields.Text(
        string='Score Breakdown', readonly=True,
        help='Detailed breakdown of how the score was computed',
    )
    sp_score_grade = fields.Selection([
        ('cold', 'Cold'),
        ('warm', 'Warm'),
        ('hot', 'Hot'),
        ('on_fire', 'On Fire'),
    ], string='Score Grade', compute='_compute_score_grade', store=True)

    # AI Activity-based scoring
    sp_activity_score = fields.Integer(
        string='Activity Score', compute='_compute_activity_score',
        help='Auto-computed score based on lead activity (emails, meetings, messages, recency)',
    )
    sp_email_count = fields.Integer(
        string='Email Count', compute='_compute_activity_metrics',
    )
    sp_meeting_count = fields.Integer(
        string='Meeting Count', compute='_compute_activity_metrics',
    )
    sp_message_count = fields.Integer(
        string='Message Count', compute='_compute_activity_metrics',
    )
    sp_activity_recency_days = fields.Integer(
        string='Days Since Last Activity', compute='_compute_activity_metrics',
    )

    # Follow-up tracking
    sp_last_followup_date = fields.Datetime(string='Last Follow-up Date', tracking=True)
    sp_next_followup_date = fields.Datetime(string='Next Follow-up Date', tracking=True)
    sp_followup_count = fields.Integer(string='Follow-up Count', default=0)
    sp_days_since_last_contact = fields.Integer(
        string='Days Since Last Contact',
        compute='_compute_days_since_last_contact',
    )
    sp_followup_status = fields.Selection([
        ('on_track', 'On Track'),
        ('due', 'Due'),
        ('overdue', 'Overdue'),
    ], string='Follow-up Status', compute='_compute_followup_status')

    # Deal Room
    sp_deal_room_ids = fields.One2many(
        'sambandha.deal.room', 'lead_id', string='Deal Rooms',
    )
    sp_deal_room_count = fields.Integer(
        string='Deal Rooms', compute='_compute_deal_room_count',
    )

    # Customer 360 linkages (computed)
    sp_sale_order_ids = fields.One2many(
        related='partner_id.sale_order_ids',
        string='Sales Orders',
    )
    sp_sale_order_count = fields.Integer(
        string='Sales Orders Count',
        compute='_compute_sale_order_count',
    )
    sp_total_revenue = fields.Monetary(
        string='Total Revenue',
        compute='_compute_total_revenue',
        currency_field='company_currency',
    )
    sp_interaction_summary = fields.Html(
        string='Interaction Summary',
        compute='_compute_interaction_summary',
    )

    @api.depends('sp_lead_score')
    def _compute_score_grade(self):
        for lead in self:
            score = lead.sp_lead_score
            if score >= 80:
                lead.sp_score_grade = 'on_fire'
            elif score >= 50:
                lead.sp_score_grade = 'hot'
            elif score >= 25:
                lead.sp_score_grade = 'warm'
            else:
                lead.sp_score_grade = 'cold'

    def _compute_activity_metrics(self):
        """Compute activity counts for AI scoring."""
        now = fields.Datetime.now()
        for lead in self:
            # Email count (sent/received on this lead)
            lead.sp_email_count = self.env['mail.message'].search_count([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('message_type', '=', 'email'),
            ])
            # Meeting count (calendar events linked to this lead)
            lead.sp_meeting_count = self.env['calendar.event'].search_count([
                ('opportunity_id', '=', lead.id),
            ]) if lead.id else 0
            # Message count (comments/notes)
            lead.sp_message_count = self.env['mail.message'].search_count([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('message_type', 'in', ['comment', 'email', 'notification']),
            ])
            # Recency: days since last activity
            last_msg = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
            ], order='date desc', limit=1)
            if last_msg:
                delta = now - last_msg.date
                lead.sp_activity_recency_days = delta.days
            else:
                lead.sp_activity_recency_days = 999

    def _compute_activity_score(self):
        """AI-powered activity scoring based on engagement signals."""
        for lead in self:
            score = 0
            details = []
            # Email engagement (max 25 pts)
            email_pts = min(lead.sp_email_count * 5, 25)
            if email_pts:
                details.append('Emails (%d): +%d' % (lead.sp_email_count, email_pts))
            score += email_pts
            # Meeting engagement (max 30 pts)
            meeting_pts = min(lead.sp_meeting_count * 10, 30)
            if meeting_pts:
                details.append('Meetings (%d): +%d' % (lead.sp_meeting_count, meeting_pts))
            score += meeting_pts
            # Message activity (max 15 pts)
            msg_pts = min(lead.sp_message_count * 3, 15)
            if msg_pts:
                details.append('Messages (%d): +%d' % (lead.sp_message_count, msg_pts))
            score += msg_pts
            # Recency bonus (max 20 pts)
            if lead.sp_activity_recency_days <= 1:
                recency_pts = 20
            elif lead.sp_activity_recency_days <= 3:
                recency_pts = 15
            elif lead.sp_activity_recency_days <= 7:
                recency_pts = 10
            elif lead.sp_activity_recency_days <= 14:
                recency_pts = 5
            else:
                recency_pts = 0
            if recency_pts:
                details.append('Recency (%dd ago): +%d' % (lead.sp_activity_recency_days, recency_pts))
            score += recency_pts
            # Stage progression bonus (max 10 pts)
            if lead.stage_id:
                stage_seq = lead.stage_id.sequence or 1
                stage_pts = min(stage_seq * 2, 10)
                details.append('Stage progress: +%d' % stage_pts)
                score += stage_pts
            lead.sp_activity_score = min(score, 100)

    def _compute_deal_room_count(self):
        for lead in self:
            lead.sp_deal_room_count = self.env['sambandha.deal.room'].search_count([
                ('lead_id', '=', lead.id),
            ])

    def action_open_deal_room(self):
        """Open or create deal room for this opportunity."""
        self.ensure_one()
        rooms = self.env['sambandha.deal.room'].search([('lead_id', '=', self.id)])
        if len(rooms) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Deal Room'),
                'res_model': 'sambandha.deal.room',
                'res_id': rooms.id,
                'view_mode': 'form',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deal Rooms'),
            'res_model': 'sambandha.deal.room',
            'view_mode': 'tree,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id,
                'default_name': _('Deal Room - %s') % self.name,
            },
        }

    def _compute_days_since_last_contact(self):
        now = fields.Datetime.now()
        for lead in self:
            if lead.sp_last_followup_date:
                delta = now - lead.sp_last_followup_date
                lead.sp_days_since_last_contact = delta.days
            elif lead.date_last_stage_update:
                delta = now - lead.date_last_stage_update
                lead.sp_days_since_last_contact = delta.days
            else:
                lead.sp_days_since_last_contact = 0

    def _compute_followup_status(self):
        now = fields.Datetime.now()
        for lead in self:
            if not lead.sp_next_followup_date:
                lead.sp_followup_status = 'on_track'
            elif lead.sp_next_followup_date < now - timedelta(days=1):
                lead.sp_followup_status = 'overdue'
            elif lead.sp_next_followup_date < now + timedelta(days=1):
                lead.sp_followup_status = 'due'
            else:
                lead.sp_followup_status = 'on_track'

    def _compute_sale_order_count(self):
        for lead in self:
            if lead.partner_id:
                lead.sp_sale_order_count = self.env['sale.order'].search_count([
                    ('partner_id', '=', lead.partner_id.id),
                ])
            else:
                lead.sp_sale_order_count = 0

    def _compute_total_revenue(self):
        for lead in self:
            if lead.partner_id:
                orders = self.env['sale.order'].search([
                    ('partner_id', '=', lead.partner_id.id),
                    ('state', '=', 'sale'),
                ])
                lead.sp_total_revenue = sum(orders.mapped('amount_total'))
            else:
                lead.sp_total_revenue = 0.0

    def _compute_interaction_summary(self):
        for lead in self:
            if not lead.partner_id:
                lead.sp_interaction_summary = False
                continue
            partner = lead.partner_id
            parts = []
            # Lead/opportunity count
            lead_count = self.search_count([
                ('partner_id', '=', partner.id),
            ])
            if lead_count:
                parts.append(_('<b>Leads/Opportunities:</b> %d') % lead_count)
            # Sale orders
            so_count = self.env['sale.order'].search_count([
                ('partner_id', '=', partner.id),
            ])
            if so_count:
                parts.append(_('<b>Sale Orders:</b> %d') % so_count)
            # Activities
            activity_count = self.env['mail.activity'].search_count([
                ('res_model', '=', 'crm.lead'),
                ('res_id', 'in', self.search([('partner_id', '=', partner.id)]).ids),
            ])
            if activity_count:
                parts.append(_('<b>Open Activities:</b> %d') % activity_count)
            # Messages
            msg_count = self.env['mail.message'].search_count([
                ('model', '=', 'crm.lead'),
                ('res_id', 'in', self.search([('partner_id', '=', partner.id)]).ids),
                ('message_type', 'in', ['comment', 'email']),
            ])
            if msg_count:
                parts.append(_('<b>Messages:</b> %d') % msg_count)

            lead.sp_interaction_summary = '<br/>'.join(parts) if parts else False

    def action_compute_lead_score(self):
        """Manually trigger lead score computation combining rules + activity."""
        rules = self.env['sambandha.lead.scoring.rule'].search([('active', '=', True)])
        for lead in self:
            rule_score = 0
            details = []
            # Rule-based scoring (50% weight)
            for rule in rules:
                pts = rule.evaluate_lead(lead)
                if pts:
                    rule_score += pts
                    details.append('%s: %+d' % (rule.name, pts))
            rule_score = max(0, min(100, rule_score))
            # Activity-based scoring (50% weight)
            activity_score = lead.sp_activity_score
            details.append('')
            details.append(_('--- Activity Score: %d ---') % activity_score)
            # Combined: weighted average
            combined = int(rule_score * 0.5 + activity_score * 0.5)
            lead.sp_lead_score = max(0, min(100, combined))
            lead.sp_score_details = '\n'.join(details) if details else _('No rules matched')

    def action_log_followup(self):
        """Log a follow-up and schedule next one."""
        now = fields.Datetime.now()
        for lead in self:
            lead.write({
                'sp_last_followup_date': now,
                'sp_next_followup_date': now + timedelta(days=7),
                'sp_followup_count': lead.sp_followup_count + 1,
            })

    def action_view_sale_orders(self):
        """Open sale orders for this lead's partner."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Orders'),
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id},
        }

    @api.model
    def _cron_compute_lead_scores(self):
        """Scheduled action: recompute scores for active leads."""
        leads = self.search([
            ('active', '=', True),
            ('probability', '<', 100),
        ])
        _logger.info('Computing lead scores for %d leads', len(leads))
        leads.action_compute_lead_score()

    @api.model
    def _cron_auto_assign_leads(self):
        """Scheduled action: auto-assign unassigned leads based on rules."""
        rules = self.env['sambandha.lead.auto.assign.rule'].search([
            ('active', '=', True),
        ])
        leads = self.search([
            ('user_id', '=', False),
            ('active', '=', True),
            ('type', '=', 'lead'),
        ])
        _logger.info('Auto-assigning %d unassigned leads', len(leads))
        for lead in leads:
            for rule in rules:
                if rule.evaluate_lead(lead):
                    vals = {}
                    if rule.user_id:
                        vals['user_id'] = rule.user_id.id
                    if rule.team_id:
                        vals['team_id'] = rule.team_id.id
                    if vals:
                        lead.write(vals)
                        _logger.info(
                            'Auto-assigned lead %s (ID: %d) via rule "%s"',
                            lead.name, lead.id, rule.name,
                        )
                    break

    @api.model
    def _cron_followup_reminders(self):
        """Scheduled action: create activities for overdue follow-ups."""
        overdue_leads = self.search([
            ('sp_next_followup_date', '<', fields.Datetime.now()),
            ('active', '=', True),
            ('probability', '<', 100),
            ('user_id', '!=', False),
        ])
        _logger.info('Creating follow-up reminders for %d leads', len(overdue_leads))
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        for lead in overdue_leads:
            existing = self.env['mail.activity'].search([
                ('res_model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('activity_type_id', '=', activity_type.id if activity_type else False),
                ('summary', '=', 'Follow-up Overdue'),
            ], limit=1)
            if not existing:
                lead.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Follow-up Overdue'),
                    note=_('This lead has an overdue follow-up since %s. Days since last contact: %d') % (
                        lead.sp_next_followup_date, lead.sp_days_since_last_contact,
                    ),
                    user_id=lead.user_id.id,
                )
