from odoo import api, fields, models


class Document(models.Model):
    _name = 'lekha.document'
    _description = 'Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Document Title', required=True, tracking=True)
    reference = fields.Char(string='Reference', copy=False, readonly=True, default='New')
    document_type = fields.Selection([
        ('general', 'General Document'),
        ('procedure', 'Procedure / SOP'),
        ('form', 'Form / Checklist'),
        ('report', 'Report'),
        ('letter', 'Letter / Memo'),
        ('policy', 'Policy Document'),
    ], string='Document Type', default='general', tracking=True)
    classification = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ], string='Classification', default='internal', tracking=True)
    description = fields.Html(string='Content')
    category_id = fields.Many2one(
        'lekha.document.category',
        string='Category',
        required=True,
        tracking=True,
    )
    tag_ids = fields.Many2many(
        'lekha.document.tag',
        'lekha_document_tag_rel',
        'document_id',
        'tag_id',
        string='Tags',
    )
    template_id = fields.Many2one(
        'lekha.document.template',
        string='Created from Template',
        ondelete='set null',
        tracking=True,
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lekha_document_attachment_rel',
        'document_id',
        'attachment_id',
        string='Attachments',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True)
    owner_id = fields.Many2one(
        'res.users',
        string='Owner',
        default=lambda self: self.env.user,
        tracking=True,
    )
    version = fields.Integer(string='Version', default=1, readonly=True)
    version_history_ids = fields.One2many(
        'lekha.document.version',
        'document_id',
        string='Version History',
    )
    collaborator_ids = fields.One2many(
        'lekha.document.collaborator',
        'document_id',
        string='Collaborators',
    )
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    is_expired = fields.Boolean(string='Expired', compute='_compute_is_expired', store=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    color = fields.Integer(string='Color Index')

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_expired = rec.expiry_date and rec.expiry_date < today

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code('lekha.document') or 'New'
        return super().create(vals_list)

    def _create_version_snapshot(self, change_summary=''):
        """Create a version history entry for the current document state."""
        self.ensure_one()
        self.env['lekha.document.version'].create({
            'document_id': self.id,
            'version_number': self.version,
            'content_snapshot': self.description,
            'change_summary': change_summary,
            'state_at_version': self.state,
            'created_by_id': self.env.user.id,
        })

    def action_submit_review(self):
        for rec in self:
            rec._create_version_snapshot(change_summary='Submitted for review')
            rec.write({'state': 'review'})

    def action_approve(self):
        for rec in self:
            new_version = rec.version + 1
            rec._create_version_snapshot(change_summary=f'Approved — version {new_version} created')
            rec.write({'state': 'approved', 'version': new_version})

    def action_archive(self):
        for rec in self:
            rec._create_version_snapshot(change_summary='Archived')
            rec.write({'state': 'archived'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
