from odoo import fields, models


class ProjectTemplate(models.Model):
    _name = 'project.template'
    _description = 'Project Template'
    _order = 'name'

    name = fields.Char(required=True)
    description = fields.Html()
    task_ids = fields.One2many(
        'project.template.task', 'template_id', string='Template Tasks',
    )
    tag_ids = fields.Many2many('project.tags', string='Default Tags')
    default_sprint_duration = fields.Integer(
        string='Default Sprint Duration (days)', default=14,
    )
    milestone_names = fields.Text(
        string='Default Milestones',
        help='One milestone name per line',
    )

    def action_create_project(self):
        self.ensure_one()
        project = self.env['project.project'].create({
            'name': '%s (from template)' % self.name,
            'description': self.description,
            'tag_ids': [(6, 0, self.tag_ids.ids)],
        })
        # Create milestones
        if self.milestone_names:
            for mname in self.milestone_names.strip().split('\n'):
                mname = mname.strip()
                if mname:
                    self.env['project.milestone'].create({
                        'name': mname,
                        'project_id': project.id,
                    })
        # Create tasks from template
        for tmpl_task in self.task_ids:
            self.env['project.task'].create({
                'name': tmpl_task.name,
                'project_id': project.id,
                'description': tmpl_task.description,
                'allocated_hours': tmpl_task.planned_hours,
                'tag_ids': [(6, 0, tmpl_task.tag_ids.ids)],
            })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': project.id,
            'view_mode': 'form',
        }
