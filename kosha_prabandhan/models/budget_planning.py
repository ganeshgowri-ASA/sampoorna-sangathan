from odoo import api, fields, models


class BudgetPlan(models.Model):
    _name = 'kosha.budget.plan'
    _description = 'Budget Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc'

    name = fields.Char(required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('revised', 'Revised'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True, required=True)
    date_from = fields.Date(string='Start Date', required=True, tracking=True)
    date_to = fields.Date(string='End Date', required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True,
    )
    responsible_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    line_ids = fields.One2many('kosha.budget.line', 'budget_id', string='Budget Lines')
    total_planned = fields.Float(compute='_compute_totals', store=True, string='Total Planned')
    total_actual = fields.Float(compute='_compute_totals', store=True, string='Total Actual')
    total_variance = fields.Float(compute='_compute_totals', store=True, string='Total Variance')
    variance_pct = fields.Float(compute='_compute_totals', store=True, string='Variance (%)')
    notes = fields.Html()

    @api.depends('line_ids.planned_amount', 'line_ids.actual_amount')
    def _compute_totals(self):
        for rec in self:
            planned = sum(rec.line_ids.mapped('planned_amount'))
            actual = sum(rec.line_ids.mapped('actual_amount'))
            rec.total_planned = planned
            rec.total_actual = actual
            rec.total_variance = planned - actual
            rec.variance_pct = ((planned - actual) / planned * 100) if planned else 0.0

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_revise(self):
        self.write({'state': 'revised'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})


class BudgetLine(models.Model):
    _name = 'kosha.budget.line'
    _description = 'Budget Line'
    _order = 'sequence, id'

    budget_id = fields.Many2one('kosha.budget.plan', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    account_id = fields.Many2one('account.account', string='Account', required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    planned_amount = fields.Float(string='Planned Amount', required=True)
    actual_amount = fields.Float(string='Actual Amount', compute='_compute_actual', store=True)
    variance = fields.Float(compute='_compute_variance', store=True)
    variance_pct = fields.Float(string='Variance (%)', compute='_compute_variance', store=True)
    date_from = fields.Date(related='budget_id.date_from', store=True)
    date_to = fields.Date(related='budget_id.date_to', store=True)
    company_id = fields.Many2one(related='budget_id.company_id', store=True)
    notes = fields.Char()

    @api.depends('account_id', 'date_from', 'date_to', 'company_id', 'analytic_account_id')
    def _compute_actual(self):
        for line in self:
            if not line.account_id or not line.date_from or not line.date_to:
                line.actual_amount = 0.0
                continue
            domain = [
                ('account_id', '=', line.account_id.id),
                ('date', '>=', line.date_from),
                ('date', '<=', line.date_to),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', line.company_id.id),
            ]
            if line.analytic_account_id:
                domain.append(('analytic_distribution', 'ilike', str(line.analytic_account_id.id)))
            move_lines = self.env['account.move.line'].search(domain)
            line.actual_amount = abs(sum(move_lines.mapped('balance')))

    @api.depends('planned_amount', 'actual_amount')
    def _compute_variance(self):
        for line in self:
            line.variance = line.planned_amount - line.actual_amount
            line.variance_pct = (
                (line.variance / line.planned_amount * 100)
                if line.planned_amount else 0.0
            )
