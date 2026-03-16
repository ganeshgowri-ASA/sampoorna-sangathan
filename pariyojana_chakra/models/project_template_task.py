from odoo import fields, models


class ProjectTemplateTask(models.Model):
    _name = 'project.template.task'
    _description = 'Project Template Task'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    template_id = fields.Many2one(
        'project.template', required=True, ondelete='cascade',
    )
    description = fields.Html()
    planned_hours = fields.Float()
    tag_ids = fields.Many2many('project.tags', string='Tags')
