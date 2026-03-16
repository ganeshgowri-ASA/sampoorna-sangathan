from odoo import api, fields, models


class SangathanOrgProfile(models.Model):
    """Organisation profile with branding and configuration."""
    _name = 'sangathan.org.profile'
    _description = 'Organisation Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Organisation Name',
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string='Organisation Code',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    logo = fields.Binary(string='Logo', attachment=True)
    tagline = fields.Char(string='Tagline')
    description = fields.Html(string='Description')

    # Contact
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    website = fields.Char(string='Website')
    address = fields.Text(string='Address')

    # Branding
    primary_color = fields.Char(
        string='Primary Color',
        default='#714B67',
        help='Hex color code for primary branding',
    )
    secondary_color = fields.Char(
        string='Secondary Color',
        default='#017E84',
    )
    accent_color = fields.Char(
        string='Accent Color',
        default='#F06050',
    )

    # Module toggles
    module_hrms = fields.Boolean(string='Enable HRMS', default=True)
    module_crm = fields.Boolean(string='Enable CRM & Sales', default=True)
    module_finance = fields.Boolean(string='Enable Finance', default=True)
    module_inventory = fields.Boolean(string='Enable Inventory', default=True)
    module_projects = fields.Boolean(string='Enable Projects', default=True)
    module_api = fields.Boolean(string='Enable API Gateway', default=False)

    # Status
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ], string='Status', default='draft', tracking=True)

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Organisation code must be unique!'),
    ]

    def action_activate(self):
        self.write({'state': 'active'})

    def action_suspend(self):
        self.write({'state': 'suspended'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
