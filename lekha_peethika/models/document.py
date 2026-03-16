from odoo import api, fields, models


class Document(models.Model):
    _name = 'lekha.document'
    _description = 'Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Document Title', required=True, tracking=True)
    reference = fields.Char(string='Reference', copy=False, readonly=True, default='New')
    description = fields.Html(string='Description')
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

    def action_submit_review(self):
        self.write({'state': 'review'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_archive(self):
        self.write({'state': 'archived'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
