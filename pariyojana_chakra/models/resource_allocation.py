from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResourceAllocation(models.Model):
    _name = 'project.resource.allocation'
    _description = 'Project Resource Allocation'
    _inherit = ['mail.thread']
    _order = 'date_from desc'

    employee_id = fields.Many2one(
        'hr.employee', required=True, tracking=True,
    )
    project_id = fields.Many2one(
        'project.project', required=True, tracking=True,
    )
    sprint_id = fields.Many2one('project.sprint', string='Sprint')
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    allocation_percentage = fields.Float(
        string='Allocation %', default=100.0, tracking=True,
    )
    role = fields.Char(string='Role')
    planned_hours = fields.Float(string='Planned Hours')
    actual_hours = fields.Float(
        compute='_compute_actual_hours', store=True,
    )
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    @api.depends('employee_id', 'project_id', 'date_from', 'date_to')
    def _compute_actual_hours(self):
        analytic_line = self.env['account.analytic.line']
        for alloc in self:
            if alloc.employee_id and alloc.project_id and alloc.date_from and alloc.date_to:
                lines = analytic_line.search([
                    ('employee_id', '=', alloc.employee_id.id),
                    ('project_id', '=', alloc.project_id.id),
                    ('date', '>=', alloc.date_from),
                    ('date', '<=', alloc.date_to),
                ])
                alloc.actual_hours = sum(lines.mapped('unit_amount'))
            else:
                alloc.actual_hours = 0.0

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for alloc in self:
            if alloc.date_from and alloc.date_to and alloc.date_from > alloc.date_to:
                raise ValidationError("End date must be after start date.")

    @api.constrains('allocation_percentage')
    def _check_allocation(self):
        for alloc in self:
            if alloc.allocation_percentage < 0 or alloc.allocation_percentage > 100:
                raise ValidationError("Allocation must be between 0 and 100%.")
