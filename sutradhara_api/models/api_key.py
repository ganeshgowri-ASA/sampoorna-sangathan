import secrets
import hashlib
from datetime import timedelta

from odoo import api, fields, models


class SutradharaApiKey(models.Model):
    _name = 'sutradhara.api.key'
    _description = 'API Key'
    _order = 'create_date desc'

    name = fields.Char(string='Name', required=True)
    key = fields.Char(
        string='API Key', readonly=True, copy=False,
        help='Auto-generated API key for authenticating requests.',
    )
    key_hash = fields.Char(string='Key Hash', readonly=True, copy=False)
    user_id = fields.Many2one(
        'res.users', string='User', required=True, ondelete='cascade',
        default=lambda self: self.env.user,
        help='The Odoo user this API key authenticates as.',
    )
    active = fields.Boolean(default=True)
    rate_limit = fields.Integer(
        string='Rate Limit (req/min)', default=60,
        help='Maximum requests per minute. 0 = unlimited.',
    )
    allowed_origins = fields.Char(
        string='Allowed Origins',
        default='https://sampoorna-sangathan.vercel.app',
        help='Comma-separated list of allowed CORS origins.',
    )
    last_used = fields.Datetime(string='Last Used', readonly=True)
    expires_at = fields.Datetime(string='Expires At')
    note = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )
    log_ids = fields.One2many('sutradhara.api.log', 'api_key_id', string='Request Logs')
    request_count = fields.Integer(string='Total Requests', compute='_compute_request_count')

    @api.depends('log_ids')
    def _compute_request_count(self):
        for record in self:
            record.request_count = len(record.log_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('key'):
                raw_key = secrets.token_urlsafe(48)
                vals['key'] = raw_key
                vals['key_hash'] = hashlib.sha256(raw_key.encode()).hexdigest()
        return super().create(vals_list)

    def action_regenerate_key(self):
        for record in self:
            raw_key = secrets.token_urlsafe(48)
            record.write({
                'key': raw_key,
                'key_hash': hashlib.sha256(raw_key.encode()).hexdigest(),
            })

    def action_deactivate(self):
        self.write({'active': False})

    def _check_rate_limit(self):
        """Check if this API key has exceeded its rate limit. Returns True if OK."""
        self.ensure_one()
        if not self.rate_limit:
            return True
        one_minute_ago = fields.Datetime.now() - timedelta(minutes=1)
        count = self.env['sutradhara.api.log'].sudo().search_count([
            ('api_key_id', '=', self.id),
            ('timestamp', '>=', one_minute_ago),
        ])
        return count < self.rate_limit

    def _is_expired(self):
        self.ensure_one()
        if not self.expires_at:
            return False
        return fields.Datetime.now() > self.expires_at
