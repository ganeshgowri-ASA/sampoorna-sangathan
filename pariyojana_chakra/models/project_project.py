from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    sprint_ids = fields.One2many(
        'project.sprint', 'project_id', string='Sprints',
    )
    sprint_count = fields.Integer(compute='_compute_sprint_count')
    allocation_ids = fields.One2many(
        'project.resource.allocation', 'project_id',
        string='Resource Allocations',
    )

    @api.depends('sprint_ids')
    def _compute_sprint_count(self):
        for project in self:
            project.sprint_count = len(project.sprint_ids)

    def action_view_sprints(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sprints',
            'res_model': 'project.sprint',
            'view_mode': 'kanban,tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_allocations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Resource Allocations',
            'res_model': 'project.resource.allocation',
            'view_mode': 'tree,form,pivot,graph',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
