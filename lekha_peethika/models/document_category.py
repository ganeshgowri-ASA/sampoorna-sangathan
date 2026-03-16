from odoo import fields, models


class DocumentCategory(models.Model):
    _name = 'lekha.document.category'
    _description = 'Document Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    code = fields.Char(string='Code')
    parent_id = fields.Many2one(
        'lekha.document.category',
        string='Parent Category',
        ondelete='cascade',
        index=True,
    )
    child_ids = fields.One2many(
        'lekha.document.category',
        'parent_id',
        string='Subcategories',
    )
    document_count = fields.Integer(
        string='Documents',
        compute='_compute_document_count',
    )
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(default=True)

    def _compute_document_count(self):
        doc_data = self.env['lekha.document'].read_group(
            [('category_id', 'in', self.ids)],
            ['category_id'],
            ['category_id'],
        )
        counts = {d['category_id'][0]: d['category_id_count'] for d in doc_data}
        for rec in self:
            rec.document_count = counts.get(rec.id, 0)
