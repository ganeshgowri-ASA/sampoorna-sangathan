import hashlib
import hmac
import json
import logging
import secrets

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SutradharaWebhook(models.Model):
    _name = 'sutradhara.webhook'
    _description = 'Webhook Configuration'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    url = fields.Char(string='Webhook URL', required=True)
    model_id = fields.Many2one(
        'ir.model', string='Model', required=True, ondelete='cascade',
        help='The Odoo model to watch for changes.',
    )
    model_name = fields.Char(string='Model Name', related='model_id.model', store=True, readonly=True)
    trigger_on_create = fields.Boolean(string='On Create', default=True)
    trigger_on_write = fields.Boolean(string='On Update', default=True)
    trigger_on_unlink = fields.Boolean(string='On Delete', default=False)
    active = fields.Boolean(default=True)
    secret = fields.Char(
        string='Signing Secret', readonly=True, copy=False,
        help='Used to sign webhook payloads for verification.',
    )
    headers = fields.Text(
        string='Custom Headers (JSON)',
        default='{}',
        help='Additional HTTP headers as JSON object.',
    )
    last_triggered = fields.Datetime(string='Last Triggered', readonly=True)
    last_status_code = fields.Integer(string='Last Status Code', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('secret'):
                vals['secret'] = secrets.token_hex(32)
        return super().create(vals_list)

    def action_regenerate_secret(self):
        for record in self:
            record.secret = secrets.token_hex(32)

    def action_test_webhook(self):
        """Send a test payload to the webhook URL."""
        self.ensure_one()
        payload = {
            'event': 'test',
            'model': self.model_name,
            'webhook_id': self.id,
            'message': 'Webhook test from Sutradhara API',
        }
        self._dispatch(payload)

    def _dispatch(self, payload):
        """Send payload to webhook URL with HMAC signature."""
        self.ensure_one()
        body = json.dumps(payload, default=str)
        signature = hmac.new(
            (self.secret or '').encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()

        try:
            custom_headers = json.loads(self.headers or '{}')
        except (json.JSONDecodeError, TypeError):
            custom_headers = {}

        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Webhook-Event': payload.get('event', 'unknown'),
            **custom_headers,
        }

        try:
            resp = requests.post(self.url, data=body, headers=headers, timeout=10)
            self.sudo().write({
                'last_triggered': fields.Datetime.now(),
                'last_status_code': resp.status_code,
            })
            if resp.status_code >= 400:
                _logger.warning(
                    'Webhook %s returned %s: %s', self.name, resp.status_code, resp.text[:200]
                )
        except requests.RequestException as e:
            _logger.error('Webhook %s failed: %s', self.name, e)
            self.sudo().write({
                'last_triggered': fields.Datetime.now(),
                'last_status_code': 0,
            })

    @api.model
    def dispatch_event(self, model_name, event, record_ids, data=None):
        """Find matching webhooks and dispatch payloads."""
        field_map = {
            'create': 'trigger_on_create',
            'write': 'trigger_on_write',
            'unlink': 'trigger_on_unlink',
        }
        trigger_field = field_map.get(event)
        if not trigger_field:
            return

        webhooks = self.sudo().search([
            ('model_name', '=', model_name),
            (trigger_field, '=', True),
            ('active', '=', True),
        ])

        for webhook in webhooks:
            payload = {
                'event': event,
                'model': model_name,
                'record_ids': record_ids,
                'data': data or {},
                'timestamp': fields.Datetime.to_string(fields.Datetime.now()),
            }
            try:
                webhook._dispatch(payload)
            except Exception as e:
                _logger.error('Failed to dispatch webhook %s: %s', webhook.name, e)
