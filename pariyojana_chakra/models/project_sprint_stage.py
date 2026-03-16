from odoo import fields, models


class ProjectSprintStage(models.Model):
    _name = 'project.sprint.stage'
    _description = 'Sprint Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(string='Folded in Kanban')
    description = fields.Text()
