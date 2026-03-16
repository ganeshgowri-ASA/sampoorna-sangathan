from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    sprint_id = fields.Many2one(
        'project.sprint', string='Sprint',
    )
    is_billable = fields.Boolean(string='Billable', default=True)
    work_type = fields.Selection([
        ('development', 'Development'),
        ('testing', 'Testing'),
        ('design', 'Design'),
        ('meeting', 'Meeting'),
        ('research', 'Research'),
        ('other', 'Other'),
    ], string='Work Type', default='development')
