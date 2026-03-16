from datetime import timedelta

from odoo import api, fields, models


class SutradharaApiLog(models.Model):
    _name = 'sutradhara.api.log'
    _description = 'API Request Log'
    _order = 'timestamp desc'

    api_key_id = fields.Many2one(
        'sutradhara.api.key', string='API Key', ondelete='set null', index=True,
    )
    user_id = fields.Many2one('res.users', string='User', index=True)
    endpoint = fields.Char(string='Endpoint', index=True)
    method = fields.Char(string='HTTP Method')
    ip_address = fields.Char(string='IP Address')
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now, index=True)
    response_code = fields.Integer(string='Response Code')
    response_time_ms = fields.Integer(string='Response Time (ms)')
    request_body = fields.Text(string='Request Body')
    error_message = fields.Text(string='Error Message')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )

    @api.autovacuum
    def _gc_old_logs(self):
        """Clean up API logs older than 30 days."""
        thirty_days_ago = fields.Datetime.now() - timedelta(days=30)
        old_logs = self.sudo().search([('timestamp', '<', thirty_days_ago)])
        old_logs.unlink()
