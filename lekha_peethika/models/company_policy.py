from odoo import api, fields, models


class CompanyPolicy(models.Model):
    _name = 'lekha.company.policy'
    _description = 'Company Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'category, sequence, name'

    name = fields.Char(string='Policy Title', required=True, tracking=True)
    reference = fields.Char(string='Reference', copy=False, readonly=True, default='New')
    category = fields.Selection([
        ('hr', 'Human Resources'),
        ('it', 'Information Technology'),
        ('finance', 'Finance'),
        ('safety', 'Health & Safety'),
        ('compliance', 'Compliance'),
        ('general', 'General'),
    ], string='Category', required=True, default='general', tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    content = fields.Html(string='Policy Content', required=True)
    summary = fields.Text(string='Summary')
    version = fields.Char(string='Version', default='1.0', tracking=True)
    effective_date = fields.Date(string='Effective Date', tracking=True)
    review_date = fields.Date(string='Next Review Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('active', 'Active'),
        ('superseded', 'Superseded'),
    ], string='Status', default='draft', tracking=True, required=True)
    approved_by_id = fields.Many2one('res.users', string='Approved By', tracking=True)
    owner_id = fields.Many2one(
        'res.users',
        string='Policy Owner',
        default=lambda self: self.env.user,
        tracking=True,
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lekha_policy_attachment_rel',
        'policy_id',
        'attachment_id',
        string='Attachments',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    color = fields.Integer(string='Color Index')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code('lekha.company.policy') or 'New'
        return super().create(vals_list)

    def action_submit_review(self):
        self.write({'state': 'review'})

    def action_activate(self):
        self.write({'state': 'active', 'approved_by_id': self.env.user.id})

    def action_supersede(self):
        self.write({'state': 'superseded'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
