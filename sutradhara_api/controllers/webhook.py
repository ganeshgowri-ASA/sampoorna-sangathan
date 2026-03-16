import json
import logging

from odoo import http
from odoo.http import request

from .auth import json_response, authenticate_request

_logger = logging.getLogger(__name__)


class SutradharaWebhookController(http.Controller):

    @http.route('/api/v1/webhooks/test/<int:webhook_id>', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def test_webhook(self, webhook_id, **kwargs):
        """Trigger a test dispatch for a specific webhook."""
        if request.httprequest.method == 'OPTIONS':
            return json_response({})

        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)

        webhook = request.env['sutradhara.webhook'].browse(webhook_id)
        if not webhook.exists():
            return json_response({'error': 'Webhook not found'}, status=404)

        webhook.action_test_webhook()

        return json_response({
            'success': True,
            'last_status_code': webhook.last_status_code,
        })

    @http.route('/api/v1/webhooks/dispatch', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def manual_dispatch(self, **kwargs):
        """Manually dispatch a webhook event."""
        if request.httprequest.method == 'OPTIONS':
            return json_response({})

        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)

        try:
            body = json.loads(request.httprequest.data or '{}')
        except json.JSONDecodeError:
            return json_response({'error': 'Invalid JSON body'}, status=400)

        model_name = body.get('model')
        event = body.get('event')
        record_ids = body.get('record_ids', [])
        data = body.get('data', {})

        if not model_name or not event:
            return json_response({'error': 'model and event are required'}, status=400)

        request.env['sutradhara.webhook'].dispatch_event(model_name, event, record_ids, data)

        return json_response({'success': True})
