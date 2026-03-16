from odoo import api, fields, models


class HrOnboardingStage(models.Model):
    _name = 'hr.onboarding.stage'
    _description = 'Onboarding Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(string='Folded in Kanban')
    description = fields.Text()


class HrOnboardingTask(models.Model):
    _name = 'hr.onboarding.task'
    _description = 'Onboarding Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10)
    employee_id = fields.Many2one('hr.employee', required=True, ondelete='cascade')
    stage_id = fields.Many2one(
        'hr.onboarding.stage',
        string='Stage',
        tracking=True,
        group_expand='_read_group_stage_ids',
        default=lambda self: self._default_stage_id(),
    )
    assigned_to_id = fields.Many2one('res.users', string='Assigned To', tracking=True)
    date_deadline = fields.Date(string='Deadline')
    date_done = fields.Date(string='Completed On', readonly=True)
    is_done = fields.Boolean(compute='_compute_is_done', store=True)
    notes = fields.Html()
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    def _default_stage_id(self):
        return self.env['hr.onboarding.stage'].search([], limit=1, order='sequence')

    @api.depends('stage_id', 'stage_id.fold')
    def _compute_is_done(self):
        for task in self:
            task.is_done = task.stage_id.fold

    def action_mark_done(self):
        done_stage = self.env['hr.onboarding.stage'].search(
            [('fold', '=', True)], limit=1, order='sequence desc',
        )
        if done_stage:
            self.write({'stage_id': done_stage.id, 'date_done': fields.Date.today()})

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.env['hr.onboarding.stage'].search([], order=order)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    onboarding_task_ids = fields.One2many(
        'hr.onboarding.task', 'employee_id', string='Onboarding Tasks',
    )
    onboarding_progress = fields.Float(
        compute='_compute_onboarding_progress',
        string='Onboarding Progress (%)',
    )
    onboarding_state = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
    ], compute='_compute_onboarding_progress', string='Onboarding Status')

    @api.depends('onboarding_task_ids', 'onboarding_task_ids.is_done')
    def _compute_onboarding_progress(self):
        for emp in self:
            tasks = emp.onboarding_task_ids
            if not tasks:
                emp.onboarding_progress = 0.0
                emp.onboarding_state = 'not_started'
            else:
                done = tasks.filtered('is_done')
                emp.onboarding_progress = (len(done) / len(tasks)) * 100
                if len(done) == len(tasks):
                    emp.onboarding_state = 'done'
                elif done:
                    emp.onboarding_state = 'in_progress'
                else:
                    emp.onboarding_state = 'not_started'
