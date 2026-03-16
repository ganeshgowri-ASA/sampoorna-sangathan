import json
import logging
import time

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError

from .auth import json_response, authenticate_request

_logger = logging.getLogger(__name__)

# Models explicitly exposed via the API, mapped to user-friendly route names.
# Add new models here as modules are created.
EXPOSED_MODELS = {
    # HRMS
    'employees': 'hr.employee',
    'departments': 'hr.department',
    'contracts': 'hr.contract',
    'attendance': 'hr.attendance',
    'leaves': 'hr.leave',
    'leave-types': 'hr.leave.type',
    'leave-allocations': 'hr.leave.allocation',
    'onboarding-tasks': 'hr.onboarding.task',
    'onboarding-stages': 'hr.onboarding.stage',
    'documents': 'hr.document',
    'document-types': 'hr.document.type',
    # CRM
    'leads': 'crm.lead',
    'crm-stages': 'crm.stage',
    'crm-teams': 'crm.team',
    # Finance / Accounting
    'invoices': 'account.move',
    'invoice-lines': 'account.move.line',
    'payments': 'account.payment',
    'journals': 'account.journal',
    'accounts': 'account.account',
    # Inventory
    'products': 'product.product',
    'product-templates': 'product.template',
    'stock-moves': 'stock.move',
    'stock-pickings': 'stock.picking',
    'stock-warehouses': 'stock.warehouse',
    'stock-locations': 'stock.location',
    # Projects
    'projects': 'project.project',
    'tasks': 'project.task',
    'task-stages': 'project.task.type',
    # Contacts
    'partners': 'res.partner',
    'users': 'res.users',
    'companies': 'res.company',
    # Sutradhara internal
    'api-keys': 'sutradhara.api.key',
    'webhooks': 'sutradhara.webhook',
    'api-logs': 'sutradhara.api.log',
}


def _parse_json_body():
    try:
        return json.loads(request.httprequest.data or '{}')
    except json.JSONDecodeError:
        return None


def _serialize_record(record, field_list=None):
    """Serialize an Odoo record to a JSON-safe dict."""
    if field_list:
        fields_to_read = [f for f in field_list if f in record._fields]
    else:
        # Default: return all stored, non-binary fields
        fields_to_read = [
            fname for fname, fobj in record._fields.items()
            if fobj.store and fobj.type != 'binary' and fname not in ('__last_update',)
        ]

    data = record.read(fields_to_read)
    return data


def _get_model_env(model_name):
    """Get model environment, return None if model doesn't exist."""
    try:
        return request.env[model_name]
    except KeyError:
        return None


class SutradharaApiController(http.Controller):

    # ─── LIST / SEARCH ───────────────────────────────────────────────

    @http.route('/api/v1/<string:resource>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def list_records(self, resource, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return json_response({})

        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)

        model_name = EXPOSED_MODELS.get(resource)
        if not model_name:
            return json_response({'error': f'Unknown resource: {resource}'}, status=404)

        model = _get_model_env(model_name)
        if model is None:
            return json_response({
                'error': f'Model {model_name} not installed',
            }, status=404)

        try:
            # Parse query parameters
            domain = json.loads(kwargs.get('domain', '[]'))
            fields_param = kwargs.get('fields', '')
            field_list = [f.strip() for f in fields_param.split(',') if f.strip()] or None
            limit = min(int(kwargs.get('limit', 80)), 500)
            offset = int(kwargs.get('offset', 0))
            order = kwargs.get('order', '')

            total = model.search_count(domain)
            records = model.search(domain, limit=limit, offset=offset, order=order or None)
            data = _serialize_record(records, field_list)

            return json_response({
                'count': total,
                'limit': limit,
                'offset': offset,
                'records': data,
            })
        except AccessError as e:
            return json_response({'error': str(e)}, status=403)
        except Exception as e:
            _logger.exception('API list error for %s', resource)
            return json_response({'error': str(e)}, status=500)

    # ─── READ SINGLE ─────────────────────────────────────────────────

    @http.route('/api/v1/<string:resource>/<int:record_id>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def read_record(self, resource, record_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return json_response({})

        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)

        model_name = EXPOSED_MODELS.get(resource)
        if not model_name:
            return json_response({'error': f'Unknown resource: {resource}'}, status=404)

        model = _get_model_env(model_name)
        if model is None:
            return json_response({'error': f'Model {model_name} not installed'}, status=404)

        try:
            record = model.browse(record_id)
            if not record.exists():
                return json_response({'error': 'Record not found'}, status=404)

            fields_param = kwargs.get('fields', '')
            field_list = [f.strip() for f in fields_param.split(',') if f.strip()] or None
            data = _serialize_record(record, field_list)

            return json_response({'record': data[0] if data else {}})
        except AccessError as e:
            return json_response({'error': str(e)}, status=403)
        except Exception as e:
            _logger.exception('API read error for %s/%s', resource, record_id)
            return json_response({'error': str(e)}, status=500)

    # ─── CREATE ──────────────────────────────────────────────────────

    @http.route('/api/v1/<string:resource>', type='http', auth='none', methods=['POST'], csrf=False)
    def create_record(self, resource, **kwargs):
        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)

        model_name = EXPOSED_MODELS.get(resource)
        if not model_name:
            return json_response({'error': f'Unknown resource: {resource}'}, status=404)

        model = _get_model_env(model_name)
        if model is None:
            return json_response({'error': f'Model {model_name} not installed'}, status=404)

        body = _parse_json_body()
        if body is None:
            return json_response({'error': 'Invalid JSON body'}, status=400)

        values = body.get('values', body)
        if isinstance(values, dict):
            values = [values]

        try:
            records = model.create(values)
            data = _serialize_record(records)

            # Dispatch webhook
            request.env['sutradhara.webhook'].dispatch_event(
                model_name, 'create', records.ids, data,
            )

            return json_response({
                'ids': records.ids,
                'records': data,
            }, status=201)
        except (AccessError,) as e:
            return json_response({'error': str(e)}, status=403)
        except (ValidationError, UserError) as e:
            return json_response({'error': str(e)}, status=400)
        except Exception as e:
            _logger.exception('API create error for %s', resource)
            return json_response({'error': str(e)}, status=500)

    # ─── UPDATE ──────────────────────────────────────────────────────

    @http.route('/api/v1/<string:resource>/<int:record_id>', type='http', auth='none', methods=['PUT', 'PATCH'], csrf=False)
    def update_record(self, resource, record_id, **kwargs):
        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)

        model_name = EXPOSED_MODELS.get(resource)
        if not model_name:
            return json_response({'error': f'Unknown resource: {resource}'}, status=404)

        model = _get_model_env(model_name)
        if model is None:
            return json_response({'error': f'Model {model_name} not installed'}, status=404)

        body = _parse_json_body()
        if body is None:
            return json_response({'error': 'Invalid JSON body'}, status=400)

        values = body.get('values', body)

        try:
            record = model.browse(record_id)
            if not record.exists():
                return json_response({'error': 'Record not found'}, status=404)

            record.write(values)
            data = _serialize_record(record)

            # Dispatch webhook
            request.env['sutradhara.webhook'].dispatch_event(
                model_name, 'write', [record_id], data,
            )

            return json_response({'record': data[0] if data else {}})
        except (AccessError,) as e:
            return json_response({'error': str(e)}, status=403)
        except (ValidationError, UserError) as e:
            return json_response({'error': str(e)}, status=400)
        except Exception as e:
            _logger.exception('API update error for %s/%s', resource, record_id)
            return json_response({'error': str(e)}, status=500)

    # ─── DELETE ──────────────────────────────────────────────────────

    @http.route('/api/v1/<string:resource>/<int:record_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_record(self, resource, record_id, **kwargs):
        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)

        model_name = EXPOSED_MODELS.get(resource)
        if not model_name:
            return json_response({'error': f'Unknown resource: {resource}'}, status=404)

        model = _get_model_env(model_name)
        if model is None:
            return json_response({'error': f'Model {model_name} not installed'}, status=404)

        try:
            record = model.browse(record_id)
            if not record.exists():
                return json_response({'error': 'Record not found'}, status=404)

            # Dispatch webhook before deletion
            request.env['sutradhara.webhook'].dispatch_event(
                model_name, 'unlink', [record_id],
            )

            record.unlink()

            return json_response({'deleted': True, 'id': record_id})
        except (AccessError,) as e:
            return json_response({'error': str(e)}, status=403)
        except Exception as e:
            _logger.exception('API delete error for %s/%s', resource, record_id)
            return json_response({'error': str(e)}, status=500)

    # ─── CALL METHOD ─────────────────────────────────────────────────

    @http.route(
        '/api/v1/<string:resource>/<int:record_id>/action/<string:method_name>',
        type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False,
    )
    def call_method(self, resource, record_id, method_name, **kwargs):
        """Call a method on a record. Only allows public action_ prefixed methods."""
        if request.httprequest.method == 'OPTIONS':
            return json_response({})

        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)

        if not method_name.startswith('action_'):
            return json_response({'error': 'Only action_ methods are callable'}, status=403)

        model_name = EXPOSED_MODELS.get(resource)
        if not model_name:
            return json_response({'error': f'Unknown resource: {resource}'}, status=404)

        model = _get_model_env(model_name)
        if model is None:
            return json_response({'error': f'Model {model_name} not installed'}, status=404)

        try:
            record = model.browse(record_id)
            if not record.exists():
                return json_response({'error': 'Record not found'}, status=404)

            method = getattr(record, method_name, None)
            if not method or not callable(method):
                return json_response({'error': f'Method {method_name} not found'}, status=404)

            body = _parse_json_body() or {}
            args = body.get('args', [])
            kw = body.get('kwargs', {})
            result = method(*args, **kw)

            # Try to serialize result
            if hasattr(result, 'ids'):
                result = {'ids': result.ids}
            elif result is None:
                result = {'success': True}

            return json_response({'result': result})
        except (AccessError,) as e:
            return json_response({'error': str(e)}, status=403)
        except Exception as e:
            _logger.exception('API call_method error: %s/%s/%s', resource, record_id, method_name)
            return json_response({'error': str(e)}, status=500)

    # ─── SCHEMA / METADATA ──────────────────────────────────────────

    @http.route('/api/v1/schema', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def list_resources(self, **kwargs):
        """List all available API resources."""
        if request.httprequest.method == 'OPTIONS':
            return json_response({})

        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)

        resources = []
        for route_name, model_name in sorted(EXPOSED_MODELS.items()):
            model = _get_model_env(model_name)
            resources.append({
                'resource': route_name,
                'model': model_name,
                'installed': model is not None,
                'description': model._description if model else None,
            })

        return json_response({'resources': resources})

    @http.route('/api/v1/schema/<string:resource>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def resource_schema(self, resource, **kwargs):
        """Get field definitions for a resource."""
        if request.httprequest.method == 'OPTIONS':
            return json_response({})

        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)

        model_name = EXPOSED_MODELS.get(resource)
        if not model_name:
            return json_response({'error': f'Unknown resource: {resource}'}, status=404)

        model = _get_model_env(model_name)
        if model is None:
            return json_response({'error': f'Model {model_name} not installed'}, status=404)

        fields_info = model.fields_get()
        schema = {}
        for fname, finfo in fields_info.items():
            schema[fname] = {
                'type': finfo.get('type'),
                'string': finfo.get('string'),
                'required': finfo.get('required', False),
                'readonly': finfo.get('readonly', False),
                'relation': finfo.get('relation'),
                'selection': finfo.get('selection'),
                'help': finfo.get('help'),
            }

        return json_response({
            'resource': resource,
            'model': model_name,
            'description': model._description,
            'fields': schema,
        })
