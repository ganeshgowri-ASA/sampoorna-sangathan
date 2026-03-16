# -*- coding: utf-8 -*-
from odoo import fields, models


class CrmEmailTemplate(models.Model):
    _name = 'sambandha.email.template'
    _description = 'CRM Email Template Library'
    _order = 'sequence, name'
    _inherit = ['mail.thread']

    name = fields.Char(string='Template Name', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)

    category = fields.Selection([
        ('introduction', 'Introduction'),
        ('followup', 'Follow-up'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('closing', 'Closing'),
        ('reengagement', 'Re-engagement'),
    ], string='Category', required=True, default='followup', tracking=True)

    subject = fields.Char(string='Subject Line', required=True)
    body_html = fields.Html(string='Email Body', required=True, sanitize_style=True)

    stage_id = fields.Many2one('crm.stage', string='Suggested Stage',
        help='CRM stage where this template is most relevant')

    usage_count = fields.Integer(string='Times Used', default=0, readonly=True)
    notes = fields.Text(string='Internal Notes')

    def action_use_template(self):
        """Increment usage counter when template is used."""
        self.ensure_one()
        self.sudo().write({'usage_count': self.usage_count + 1})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subject': self.subject,
                'default_body': self.body_html,
            },
        }
