from odoo import fields, models


class DocumentTag(models.Model):
    _name = 'lekha.document.tag'
    _description = 'Document Tag'
    _order = 'name'

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index')
