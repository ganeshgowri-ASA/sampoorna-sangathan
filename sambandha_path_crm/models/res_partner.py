# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sp_lead_ids = fields.One2many('crm.lead', 'partner_id', string='Leads/Opportunities')
    sp_lead_count = fields.Integer(string='Lead Count', compute='_compute_sp_lead_count')
    sp_customer_score = fields.Integer(
        string='Customer Score', compute='_compute_sp_customer_score', store=True,
    )
    sp_lifetime_revenue = fields.Monetary(
        string='Lifetime Revenue', compute='_compute_sp_lifetime_revenue',
        currency_field='currency_id',
    )
    sp_last_interaction_date = fields.Datetime(
        string='Last Interaction', compute='_compute_sp_last_interaction',
    )

    def _compute_sp_lead_count(self):
        for partner in self:
            partner.sp_lead_count = self.env['crm.lead'].search_count([
                ('partner_id', '=', partner.id),
            ])

    @api.depends('sp_lead_ids.sp_lead_score')
    def _compute_sp_customer_score(self):
        for partner in self:
            leads = self.env['crm.lead'].search([
                ('partner_id', '=', partner.id),
                ('active', '=', True),
            ])
            partner.sp_customer_score = max(leads.mapped('sp_lead_score') or [0])

    def _compute_sp_lifetime_revenue(self):
        for partner in self:
            orders = self.env['sale.order'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'sale'),
            ])
            partner.sp_lifetime_revenue = sum(orders.mapped('amount_total'))

    def _compute_sp_last_interaction(self):
        for partner in self:
            last_msg = self.env['mail.message'].search([
                ('model', '=', 'res.partner'),
                ('res_id', '=', partner.id),
                ('message_type', 'in', ['comment', 'email']),
            ], order='date desc', limit=1)
            partner.sp_last_interaction_date = last_msg.date if last_msg else False

    def action_view_customer_journey(self):
        """Open customer journey timeline for this partner."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journey - %s') % self.name,
            'res_model': 'sambandha.customer.journey',
            'view_mode': 'tree,graph',
            'domain': [('partner_id', '=', self.id)],
            'context': {'search_default_partner_id': self.id},
        }

    def action_view_customer_360(self):
        """Open the 360 view for this customer."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer 360 - %s') % self.name,
            'res_model': 'res.partner',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('sambandha_path_crm.view_partner_customer_360_form').id,
            'target': 'current',
        }
