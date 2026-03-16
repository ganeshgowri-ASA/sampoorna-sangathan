from odoo import api, fields, models


class DocumentTemplate(models.Model):
    _name = 'lekha.document.template'
    _description = 'Document Template'
    _order = 'sequence, name'

    name = fields.Char(string='Template Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    document_type = fields.Selection([
        ('general', 'General Document'),
        ('procedure', 'Procedure / SOP'),
        ('form', 'Form / Checklist'),
        ('report', 'Report'),
        ('letter', 'Letter / Memo'),
        ('policy', 'Policy Document'),
    ], string='Document Type', required=True, default='general')
    category_id = fields.Many2one(
        'lekha.document.category',
        string='Category',
        ondelete='set null',
    )
    tag_ids = fields.Many2many(
        'lekha.document.tag',
        'lekha_template_tag_rel',
        'template_id',
        'tag_id',
        string='Tags',
    )
    description = fields.Text(string='Description')
    content = fields.Html(string='Template Content')
    active = fields.Boolean(string='Active', default=True)
    color = fields.Integer(string='Color Index')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    document_count = fields.Integer(
        string='Documents Created',
        compute='_compute_document_count',
    )

    @api.depends('name')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = self.env['lekha.document'].search_count(
                [('template_id', '=', rec.id)]
            )

    def action_create_document(self):
        """Open new document form pre-filled from this template."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Document',
            'res_model': 'lekha.document',
            'view_mode': 'form',
            'context': {
                'default_template_id': self.id,
                'default_category_id': self.category_id.id,
                'default_tag_ids': [(6, 0, self.tag_ids.ids)],
                'default_description': self.content,
                'default_document_type': self.document_type,
            },
        }
