from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BankReconciliation(models.Model):
    _name = 'kosha.bank.reconciliation'
    _description = 'Bank Reconciliation'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference', required=True, tracking=True,
        default=lambda self: _('New'),
    )
    journal_id = fields.Many2one(
        'account.journal', string='Bank Journal', required=True,
        domain=[('type', '=', 'bank')], tracking=True,
    )
    date = fields.Date(
        string='Reconciliation Date',
        default=fields.Date.context_today, required=True,
    )
    date_from = fields.Date(string='Statement From', required=True)
    date_to = fields.Date(string='Statement To', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Reconciled'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True, required=True)
    statement_balance = fields.Float(
        string='Bank Statement Balance', tracking=True,
    )
    book_balance = fields.Float(
        string='Book Balance', compute='_compute_book_balance', store=True,
    )
    difference = fields.Float(
        string='Difference', compute='_compute_difference', store=True,
    )
    line_ids = fields.One2many(
        'kosha.bank.reconciliation.line', 'reconciliation_id',
        string='Reconciliation Lines',
    )
    matched_count = fields.Integer(
        compute='_compute_match_stats', string='Matched',
    )
    unmatched_count = fields.Integer(
        compute='_compute_match_stats', string='Unmatched',
    )
    notes = fields.Text()
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'kosha.bank.reconciliation',
                ) or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.move_line_id', 'line_ids.amount')
    def _compute_book_balance(self):
        for rec in self:
            rec.book_balance = sum(
                line.amount for line in rec.line_ids if line.move_line_id
            )

    @api.depends('statement_balance', 'book_balance')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.statement_balance - rec.book_balance

    @api.depends('line_ids.is_matched')
    def _compute_match_stats(self):
        for rec in self:
            matched = len(rec.line_ids.filtered('is_matched'))
            rec.matched_count = matched
            rec.unmatched_count = len(rec.line_ids) - matched

    def action_load_entries(self):
        """Load unreconciled journal entries from the bank journal."""
        for rec in self:
            if not rec.journal_id:
                raise UserError(_('Please select a bank journal first.'))
            existing_move_lines = rec.line_ids.mapped('move_line_id').ids
            move_lines = self.env['account.move.line'].search([
                ('journal_id', '=', rec.journal_id.id),
                ('date', '>=', rec.date_from),
                ('date', '<=', rec.date_to),
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', False),
                ('account_id.reconcile', '=', True),
                ('id', 'not in', existing_move_lines),
            ])
            lines_vals = []
            for ml in move_lines:
                lines_vals.append({
                    'reconciliation_id': rec.id,
                    'move_line_id': ml.id,
                    'partner_id': ml.partner_id.id,
                    'ref': ml.ref or ml.move_id.name,
                    'date': ml.date,
                    'amount': ml.debit - ml.credit,
                })
            if lines_vals:
                self.env['kosha.bank.reconciliation.line'].create(lines_vals)
            rec.state = 'in_progress'

    def action_reconcile(self):
        for rec in self:
            if rec.unmatched_count > 0:
                raise UserError(_(
                    'There are %d unmatched lines. '
                    'Please match all lines before reconciling.'
                ) % rec.unmatched_count)
            rec.state = 'done'

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})


class BankReconciliationLine(models.Model):
    _name = 'kosha.bank.reconciliation.line'
    _description = 'Bank Reconciliation Line'
    _order = 'date, id'

    reconciliation_id = fields.Many2one(
        'kosha.bank.reconciliation', ondelete='cascade', required=True,
    )
    move_line_id = fields.Many2one(
        'account.move.line', string='Journal Entry Line',
    )
    partner_id = fields.Many2one('res.partner')
    ref = fields.Char(string='Reference')
    date = fields.Date()
    amount = fields.Float()
    statement_amount = fields.Float(string='Bank Statement Amount')
    is_matched = fields.Boolean(
        string='Matched', compute='_compute_is_matched', store=True,
    )
    match_difference = fields.Float(
        compute='_compute_is_matched', store=True,
    )
    company_id = fields.Many2one(
        related='reconciliation_id.company_id', store=True,
    )

    @api.depends('amount', 'statement_amount')
    def _compute_is_matched(self):
        for line in self:
            line.match_difference = line.statement_amount - line.amount
            line.is_matched = (
                line.statement_amount != 0
                and abs(line.match_difference) < 0.01
            )
