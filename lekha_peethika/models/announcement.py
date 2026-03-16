from odoo import api, fields, models


class Announcement(models.Model):
    _name = 'lekha.announcement'
    _description = 'Announcement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'is_pinned desc, publish_date desc, create_date desc'

    name = fields.Char(string='Title', required=True, tracking=True)
    content = fields.Html(string='Content', required=True)
    summary = fields.Text(string='Summary')
    publish_date = fields.Datetime(
        string='Publish Date',
        default=fields.Datetime.now,
        tracking=True,
    )
    expiry_date = fields.Date(string='Expiry Date')
    is_pinned = fields.Boolean(string='Pinned', default=False)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
        ('2', 'Urgent'),
    ], string='Priority', default='0')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', tracking=True, required=True)
    author_id = fields.Many2one(
        'res.users',
        string='Author',
        default=lambda self: self.env.user,
        tracking=True,
    )
    target_audience = fields.Selection([
        ('all', 'All Employees'),
        ('department', 'Specific Department'),
        ('company', 'Specific Company'),
    ], string='Target Audience', default='all')
    department_id = fields.Many2one('hr.department', string='Department')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    is_active = fields.Boolean(string='Active', compute='_compute_is_active', store=True)
    color = fields.Integer(string='Color Index')

    @api.depends('state', 'expiry_date')
    def _compute_is_active(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_active = (
                rec.state == 'published'
                and (not rec.expiry_date or rec.expiry_date >= today)
            )

    def action_publish(self):
        self.write({'state': 'published'})

    def action_expire(self):
        self.write({'state': 'expired'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
