from odoo import api, fields, models


class ProjectDeliverable(models.Model):
    _name = 'project.deliverable'
    _description = 'Project Deliverable'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10)
    milestone_id = fields.Many2one(
        'project.milestone', required=True, ondelete='cascade',
    )
    project_id = fields.Many2one(
        related='milestone_id.project_id', store=True,
    )
    description = fields.Html()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    due_date = fields.Date()
    completion_date = fields.Date()
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
        ('2', 'Urgent'),
    ], default='0')

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_review(self):
        self.write({'state': 'review'})

    def action_done(self):
        self.write({
            'state': 'done',
            'completion_date': fields.Date.today(),
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})
