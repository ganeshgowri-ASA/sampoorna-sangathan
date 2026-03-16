from odoo import fields, models


class DocumentVersion(models.Model):
    _name = 'lekha.document.version'
    _description = 'Document Version History'
    _order = 'version_number desc'
    _rec_name = 'display_name'

    document_id = fields.Many2one(
        'lekha.document',
        string='Document',
        required=True,
        ondelete='cascade',
        index=True,
    )
    version_number = fields.Integer(string='Version', required=True)
    content_snapshot = fields.Html(string='Content at this Version')
    change_summary = fields.Text(string='Change Summary')
    state_at_version = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('archived', 'Archived'),
    ], string='State', readonly=True)
    created_by_id = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True,
    )
    create_date = fields.Datetime(string='Created On', readonly=True)
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )

    def _compute_display_name(self):
        for rec in self:
            doc = rec.document_id.name or ''
            rec.display_name = f'{doc} v{rec.version_number}'
