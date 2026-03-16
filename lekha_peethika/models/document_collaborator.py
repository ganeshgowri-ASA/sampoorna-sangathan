from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DocumentCollaborator(models.Model):
    _name = 'lekha.document.collaborator'
    _description = 'Document Collaborator'
    _rec_name = 'user_id'

    document_id = fields.Many2one(
        'lekha.document',
        string='Document',
        required=True,
        ondelete='cascade',
        index=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
    )
    permission = fields.Selection([
        ('view', 'View Only'),
        ('comment', 'Can Comment'),
        ('edit', 'Can Edit'),
    ], string='Permission', required=True, default='view')
    added_by_id = fields.Many2one(
        'res.users',
        string='Added By',
        default=lambda self: self.env.user,
        readonly=True,
    )
    added_date = fields.Date(
        string='Added On',
        default=fields.Date.context_today,
        readonly=True,
    )

    _sql_constraints = [
        ('doc_user_uniq', 'unique(document_id, user_id)',
         'A user can only be added once per document.'),
    ]

    @api.constrains('document_id', 'user_id')
    def _check_not_owner(self):
        for rec in self:
            if rec.user_id == rec.document_id.owner_id:
                raise ValidationError(
                    'The document owner is already the primary owner and '
                    'cannot be added as a collaborator.'
                )
