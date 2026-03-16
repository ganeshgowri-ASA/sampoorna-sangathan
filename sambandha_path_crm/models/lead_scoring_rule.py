# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LeadScoringRule(models.Model):
    _name = 'sambandha.lead.scoring.rule'
    _description = 'Lead Scoring Rule'
    _order = 'sequence, id'

    name = fields.Char(string='Rule Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)

    # Scoring criteria
    criteria_type = fields.Selection([
        ('field_value', 'Field Value Match'),
        ('email_domain', 'Email Domain'),
        ('country', 'Country'),
        ('revenue', 'Expected Revenue'),
        ('source', 'Lead Source'),
        ('tag', 'Lead Tag'),
    ], string='Criteria Type', required=True, default='field_value')

    # Criteria parameters
    field_name = fields.Char(string='Field Name', help='Technical field name on crm.lead')
    field_value = fields.Char(string='Field Value', help='Value to match against')
    country_ids = fields.Many2many('res.country', string='Countries')
    source_id = fields.Many2one('utm.source', string='UTM Source')
    tag_ids = fields.Many2many('crm.tag', string='Tags')
    revenue_min = fields.Float(string='Min Revenue')
    revenue_max = fields.Float(string='Max Revenue')

    # Score
    score_points = fields.Integer(string='Score Points', required=True, default=10)

    # Auto-assignment
    auto_assign = fields.Boolean(string='Auto-Assign', default=False)
    assign_user_id = fields.Many2one('res.users', string='Assign To User')
    assign_team_id = fields.Many2one('crm.team', string='Assign To Team')

    @api.constrains('score_points')
    def _check_score_points(self):
        for rule in self:
            if rule.score_points < -100 or rule.score_points > 100:
                raise ValidationError(_('Score points must be between -100 and 100.'))

    def evaluate_lead(self, lead):
        """Evaluate a lead against this rule. Returns score if matched, 0 otherwise."""
        self.ensure_one()
        if self.criteria_type == 'email_domain' and self.field_value:
            if lead.email_from and self.field_value.lower() in lead.email_from.lower():
                return self.score_points
        elif self.criteria_type == 'country':
            if lead.country_id and lead.country_id in self.country_ids:
                return self.score_points
        elif self.criteria_type == 'revenue':
            rev = lead.expected_revenue or 0.0
            if self.revenue_min <= rev <= (self.revenue_max or float('inf')):
                return self.score_points
        elif self.criteria_type == 'source':
            if lead.source_id and lead.source_id == self.source_id:
                return self.score_points
        elif self.criteria_type == 'tag':
            if lead.tag_ids & self.tag_ids:
                return self.score_points
        elif self.criteria_type == 'field_value' and self.field_name and self.field_value:
            lead_val = lead.mapped(self.field_name)
            if lead_val and str(lead_val[0]).lower() == self.field_value.lower():
                return self.score_points
        return 0


class LeadAutoAssignRule(models.Model):
    _name = 'sambandha.lead.auto.assign.rule'
    _description = 'Lead Auto-Assignment Rule'
    _order = 'sequence, id'

    name = fields.Char(string='Rule Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)

    # Conditions
    min_score = fields.Integer(string='Minimum Score', default=0)
    source_id = fields.Many2one('utm.source', string='Lead Source')
    country_ids = fields.Many2many('res.country', string='Countries')
    tag_ids = fields.Many2many('crm.tag', string='Tags')

    # Assignment target
    user_id = fields.Many2one('res.users', string='Assign To User')
    team_id = fields.Many2one('crm.team', string='Assign To Team')

    def evaluate_lead(self, lead):
        """Check if lead matches this assignment rule."""
        self.ensure_one()
        if self.min_score and (lead.sp_lead_score or 0) < self.min_score:
            return False
        if self.source_id and lead.source_id != self.source_id:
            return False
        if self.country_ids and lead.country_id not in self.country_ids:
            return False
        if self.tag_ids and not (lead.tag_ids & self.tag_ids):
            return False
        return True
