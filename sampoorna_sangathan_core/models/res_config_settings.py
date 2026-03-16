from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sangathan_org_name = fields.Char(
        string='Organisation Name',
        config_parameter='sangathan.org_name',
        default='SampoornaSangathan',
    )
    sangathan_primary_color = fields.Char(
        string='Primary Brand Color',
        config_parameter='sangathan.primary_color',
        default='#714B67',
    )
    sangathan_enable_api = fields.Boolean(
        string='Enable API Gateway',
        config_parameter='sangathan.enable_api',
        default=False,
    )
    sangathan_enable_audit_trail = fields.Boolean(
        string='Enable Audit Trail',
        config_parameter='sangathan.enable_audit_trail',
        default=True,
    )
    sangathan_default_lang = fields.Selection([
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('ta', 'Tamil'),
        ('te', 'Telugu'),
    ], string='Default Language',
        config_parameter='sangathan.default_lang',
        default='en',
    )
