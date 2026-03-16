from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sangathan_code = fields.Char(string='Sangathan Code')
    sangathan_org_profile_id = fields.Many2one(
        'sangathan.org.profile',
        string='Organisation Profile',
    )
    sangathan_enabled = fields.Boolean(
        string='SampoornaSangathan Enabled',
        default=True,
    )
