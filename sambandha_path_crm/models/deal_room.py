# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class DealRoom(models.Model):
    _name = 'sambandha.deal.room'
    _description = 'Deal Room - Collaborative Space for Opportunities'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Room Name', required=True, tracking=True)
    lead_id = fields.Many2one(
        'crm.lead', string='Opportunity', required=True,
        domain="[('type', '=', 'opportunity')]", tracking=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        related='lead_id.partner_id', string='Customer',
        store=True, readonly=True,
    )
    user_id = fields.Many2one(
        'res.users', string='Room Owner', default=lambda self: self.env.user,
        tracking=True,
    )
    team_member_ids = fields.Many2many(
        'res.users', string='Team Members',
        help='Users who can collaborate in this deal room',
    )

    state = fields.Selection([
        ('active', 'Active'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('archived', 'Archived'),
    ], string='Status', default='active', tracking=True)

    # Deal info (from linked opportunity)
    expected_revenue = fields.Monetary(
        related='lead_id.expected_revenue', string='Expected Revenue', readonly=True,
    )
    probability = fields.Float(
        related='lead_id.probability', string='Probability', readonly=True,
    )
    stage_id = fields.Many2one(
        related='lead_id.stage_id', string='Pipeline Stage', readonly=True,
    )
    currency_id = fields.Many2one(
        related='lead_id.company_id.currency_id', string='Currency', readonly=True,
    )

    # Action items
    action_item_ids = fields.One2many(
        'sambandha.deal.room.action', 'room_id', string='Action Items',
    )
    action_item_count = fields.Integer(
        string='Action Items', compute='_compute_action_item_count',
    )
    pending_action_count = fields.Integer(
        string='Pending Actions', compute='_compute_action_item_count',
    )

    # Notes & Documents
    notes = fields.Html(string='Strategy Notes')
    document_ids = fields.Many2many(
        'ir.attachment', string='Documents',
        help='Shared documents for this deal',
    )
    document_count = fields.Integer(
        string='Documents', compute='_compute_document_count',
    )

    # Key dates
    target_close_date = fields.Date(string='Target Close Date', tracking=True)
    next_meeting_date = fields.Datetime(string='Next Meeting', tracking=True)

    # Competitor info
    competitor_info = fields.Text(string='Competitor Intelligence')
    win_strategy = fields.Html(string='Win Strategy')

    def _compute_action_item_count(self):
        for room in self:
            actions = room.action_item_ids
            room.action_item_count = len(actions)
            room.pending_action_count = len(actions.filtered(lambda a: a.state != 'done'))

    def _compute_document_count(self):
        for room in self:
            room.document_count = len(room.document_ids)

    @api.model_create_multi
    def create(self, vals_list):
        rooms = super().create(vals_list)
        for room in rooms:
            # Auto-add team members as followers
            if room.team_member_ids:
                room.message_subscribe(partner_ids=room.team_member_ids.mapped('partner_id').ids)
        return rooms

    def write(self, vals):
        res = super().write(vals)
        if 'team_member_ids' in vals:
            for room in self:
                room.message_subscribe(partner_ids=room.team_member_ids.mapped('partner_id').ids)
        return res

    def action_mark_won(self):
        self.write({'state': 'won'})

    def action_mark_lost(self):
        self.write({'state': 'lost'})

    def action_archive(self):
        self.write({'state': 'archived'})

    def action_reactivate(self):
        self.write({'state': 'active'})


class DealRoomAction(models.Model):
    _name = 'sambandha.deal.room.action'
    _description = 'Deal Room Action Item'
    _order = 'deadline, sequence, id'

    room_id = fields.Many2one(
        'sambandha.deal.room', string='Deal Room',
        required=True, ondelete='cascade',
    )
    name = fields.Char(string='Action Item', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    deadline = fields.Date(string='Deadline')
    state = fields.Selection([
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='todo')
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
        ('2', 'Urgent'),
    ], string='Priority', default='0')
    notes = fields.Text(string='Notes')

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
