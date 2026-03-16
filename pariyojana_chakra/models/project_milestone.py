from odoo import api, fields, models


class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'

    target_date = fields.Date(string='Target Date')
    completion_date = fields.Date(string='Completion Date')
    deliverable_ids = fields.One2many(
        'project.deliverable', 'milestone_id', string='Deliverables',
    )
    deliverable_count = fields.Integer(
        compute='_compute_deliverable_count', store=True,
    )
    progress = fields.Float(
        compute='_compute_progress', store=True, string='Progress %',
    )
    status = fields.Selection([
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('delayed', 'Delayed'),
        ('completed', 'Completed'),
    ], default='on_track', tracking=True)

    @api.depends('deliverable_ids')
    def _compute_deliverable_count(self):
        for milestone in self:
            milestone.deliverable_count = len(milestone.deliverable_ids)

    @api.depends('deliverable_ids.state')
    def _compute_progress(self):
        for milestone in self:
            deliverables = milestone.deliverable_ids
            if deliverables:
                done = len(deliverables.filtered(lambda d: d.state == 'done'))
                milestone.progress = (done / len(deliverables)) * 100
            else:
                milestone.progress = 0.0
