# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class FollowupRule(models.Model):
    _name = 'sambandha.followup.rule'
    _description = 'Automated Follow-up Rule'
    _order = 'sequence, id'

    name = fields.Char(string='Rule Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    # Trigger conditions
    trigger_type = fields.Selection([
        ('no_activity', 'No Activity For X Days'),
        ('stage_duration', 'In Stage For X Days'),
        ('score_below', 'Score Below Threshold'),
        ('no_followup', 'No Follow-up For X Days'),
    ], string='Trigger', required=True, default='no_activity')
    trigger_days = fields.Integer(
        string='Days Threshold', default=7,
        help='Number of days for time-based triggers',
    )
    trigger_score = fields.Integer(
        string='Score Threshold', default=25,
        help='Score threshold for score-based triggers',
    )

    # Filter conditions
    stage_ids = fields.Many2many(
        'crm.stage', string='Apply to Stages',
        help='Leave empty to apply to all stages',
    )
    team_id = fields.Many2one('crm.team', string='Sales Team')
    lead_type = fields.Selection([
        ('lead', 'Leads Only'),
        ('opportunity', 'Opportunities Only'),
        ('both', 'Both'),
    ], string='Apply To', default='both')

    # Action
    action_type = fields.Selection([
        ('activity', 'Create Activity'),
        ('notify', 'Notify Salesperson'),
        ('both', 'Activity + Notification'),
    ], string='Action', required=True, default='activity')
    activity_type_id = fields.Many2one(
        'mail.activity.type', string='Activity Type',
        default=lambda self: self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False),
    )
    activity_summary = fields.Char(
        string='Activity Summary', default='Follow-up Required',
    )
    activity_note = fields.Text(string='Activity Note')
    activity_deadline_days = fields.Integer(
        string='Deadline (days from now)', default=2,
    )

    # Execution tracking
    last_run = fields.Datetime(string='Last Run', readonly=True)
    leads_matched = fields.Integer(string='Leads Matched (Last Run)', readonly=True)

    @api.constrains('trigger_days')
    def _check_trigger_days(self):
        for rule in self:
            if rule.trigger_type in ('no_activity', 'stage_duration', 'no_followup') and rule.trigger_days < 1:
                raise models.ValidationError(_('Days threshold must be at least 1.'))

    def _get_matching_leads(self):
        """Find leads matching this rule's trigger conditions."""
        self.ensure_one()
        now = fields.Datetime.now()
        domain = [
            ('active', '=', True),
            ('probability', '<', 100),
            ('user_id', '!=', False),
        ]
        # Lead type filter
        if self.lead_type == 'lead':
            domain.append(('type', '=', 'lead'))
        elif self.lead_type == 'opportunity':
            domain.append(('type', '=', 'opportunity'))
        # Stage filter
        if self.stage_ids:
            domain.append(('stage_id', 'in', self.stage_ids.ids))
        # Team filter
        if self.team_id:
            domain.append(('team_id', '=', self.team_id.id))

        leads = self.env['crm.lead'].search(domain)
        threshold = now - timedelta(days=self.trigger_days)
        matched = self.env['crm.lead']

        for lead in leads:
            if self.trigger_type == 'no_activity':
                # Check last message date
                last_msg = self.env['mail.message'].search([
                    ('model', '=', 'crm.lead'),
                    ('res_id', '=', lead.id),
                    ('message_type', 'in', ['comment', 'email']),
                ], order='date desc', limit=1)
                last_date = last_msg.date if last_msg else lead.create_date
                if last_date and last_date < threshold:
                    matched |= lead

            elif self.trigger_type == 'stage_duration':
                stage_date = lead.date_last_stage_update or lead.create_date
                if stage_date and stage_date < threshold:
                    matched |= lead

            elif self.trigger_type == 'score_below':
                if lead.sp_lead_score < self.trigger_score:
                    matched |= lead

            elif self.trigger_type == 'no_followup':
                last_fu = lead.sp_last_followup_date or lead.create_date
                if last_fu and last_fu < threshold:
                    matched |= lead

        return matched

    def _execute_action(self, leads):
        """Execute the configured action on matched leads."""
        self.ensure_one()
        now = fields.Datetime.now()
        deadline = fields.Date.today() + timedelta(days=self.activity_deadline_days)

        for lead in leads:
            # Skip if already has a pending activity with same summary
            existing = self.env['mail.activity'].search([
                ('res_model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('summary', '=', self.activity_summary),
            ], limit=1)
            if existing:
                continue

            if self.action_type in ('activity', 'both'):
                activity_type = self.activity_type_id or self.env.ref(
                    'mail.mail_activity_data_todo', raise_if_not_found=False
                )
                note = self.activity_note or _(
                    'Auto-generated by follow-up rule: %s'
                ) % self.name
                if activity_type:
                    lead.activity_schedule(
                        activity_type.xml_id or 'mail.mail_activity_data_todo',
                        summary=self.activity_summary,
                        note=note,
                        date_deadline=deadline,
                        user_id=lead.user_id.id,
                    )

            if self.action_type in ('notify', 'both'):
                lead.message_notify(
                    partner_ids=lead.user_id.partner_id.ids,
                    subject=_('Follow-up Alert: %s') % lead.name,
                    body=_(
                        '<p>Follow-up rule <b>%s</b> triggered for lead <b>%s</b>.</p>'
                        '<p>Lead Score: %d | Days since last contact: %d</p>'
                    ) % (self.name, lead.name, lead.sp_lead_score, lead.sp_days_since_last_contact),
                )

    @api.model
    def _cron_execute_followup_rules(self):
        """Cron job: evaluate all active follow-up rules."""
        rules = self.search([('active', '=', True)])
        for rule in rules:
            try:
                leads = rule._get_matching_leads()
                if leads:
                    rule._execute_action(leads)
                    _logger.info(
                        'Follow-up rule "%s" matched %d leads',
                        rule.name, len(leads),
                    )
                rule.write({
                    'last_run': fields.Datetime.now(),
                    'leads_matched': len(leads),
                })
            except Exception:
                _logger.exception('Error executing follow-up rule "%s"', rule.name)
