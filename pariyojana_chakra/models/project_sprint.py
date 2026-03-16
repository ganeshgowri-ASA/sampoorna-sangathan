from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectSprint(models.Model):
    _name = 'project.sprint'
    _description = 'Project Sprint'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(required=True, tracking=True)
    project_id = fields.Many2one('project.project', required=True, tracking=True)
    stage_id = fields.Many2one(
        'project.sprint.stage',
        string='Stage',
        tracking=True,
        group_expand='_read_group_stage_ids',
        default=lambda self: self.env['project.sprint.stage'].search([], limit=1),
    )
    date_start = fields.Date(string='Start Date', required=True, tracking=True)
    date_end = fields.Date(string='End Date', required=True, tracking=True)
    goal = fields.Html(string='Sprint Goal')
    task_ids = fields.Many2many(
        'project.task',
        'sprint_task_rel',
        'sprint_id',
        'task_id',
        string='Tasks',
    )
    task_count = fields.Integer(compute='_compute_task_count', store=True)
    velocity = fields.Float(string='Planned Velocity (Hours)', tracking=True)
    actual_hours = fields.Float(compute='_compute_actual_hours', store=True)
    progress = fields.Float(compute='_compute_progress', store=True)
    color = fields.Integer()
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    @api.depends('task_ids')
    def _compute_task_count(self):
        for sprint in self:
            sprint.task_count = len(sprint.task_ids)

    @api.depends('task_ids.effective_hours')
    def _compute_actual_hours(self):
        for sprint in self:
            sprint.actual_hours = sum(sprint.task_ids.mapped('effective_hours'))

    @api.depends('velocity', 'actual_hours')
    def _compute_progress(self):
        for sprint in self:
            if sprint.velocity:
                sprint.progress = min(100.0, (sprint.actual_hours / sprint.velocity) * 100)
            else:
                sprint.progress = 0.0

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for sprint in self:
            if sprint.date_start and sprint.date_end and sprint.date_start > sprint.date_end:
                raise ValidationError("Sprint end date must be after start date.")

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        return self.env['project.sprint.stage'].search([])
