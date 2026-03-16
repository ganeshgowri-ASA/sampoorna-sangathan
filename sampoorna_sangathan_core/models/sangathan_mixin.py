from odoo import api, fields, models


class SangathanAuditMixin(models.AbstractModel):
    """Mixin providing audit trail fields for all Sangathan models."""
    _name = 'sangathan.audit.mixin'
    _description = 'Sangathan Audit Mixin'

    sangathan_ref = fields.Char(
        string='Sangathan Reference',
        copy=False,
        readonly=True,
        help='Auto-generated reference for cross-module tracking',
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='0')
    tag_ids = fields.Many2many(
        'sangathan.tag',
        string='Tags',
    )
    notes = fields.Html(string='Internal Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sangathan_ref'):
                model_prefix = self._name.replace('.', '_').upper()[:8]
                vals['sangathan_ref'] = self.env['ir.sequence'].next_by_code(
                    'sangathan.ref.sequence'
                ) or f'{model_prefix}-NEW'
        return super().create(vals_list)


class SangathanTag(models.Model):
    """Shared tags across all Sangathan modules."""
    _name = 'sangathan.tag'
    _description = 'Sangathan Tag'
    _order = 'name'

    name = fields.Char(string='Tag Name', required=True)
    color = fields.Integer(string='Color Index')
    module_scope = fields.Selection([
        ('all', 'All Modules'),
        ('hrms', 'HRMS'),
        ('crm', 'CRM'),
        ('finance', 'Finance'),
        ('inventory', 'Inventory'),
        ('projects', 'Projects'),
    ], string='Module Scope', default='all')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_scope_unique', 'UNIQUE(name, module_scope)',
         'Tag name must be unique per module scope!'),
    ]
