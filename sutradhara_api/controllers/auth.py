import hashlib
import hmac
import json
import logging
import time

from odoo import http
from odoo.http import request, Response
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

TOKEN_EXPIRY = 3600 * 8  # 8 hours
JWT_SECRET_PARAM = 'sutradhara_api.jwt_secret'

CORS_ORIGIN = 'https://sampoorna-sangathan.vercel.app'


def _b64url_encode(data):
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def _b64url_decode(s):
    import base64
    s += '=' * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _get_jwt_secret():
    secret = request.env['ir.config_parameter'].sudo().get_param(JWT_SECRET_PARAM)
    if not secret:
        import secrets
        secret = secrets.token_hex(32)
        request.env['ir.config_parameter'].sudo().set_param(JWT_SECRET_PARAM, secret)
    return secret


def generate_token(uid, db):
    secret = _get_jwt_secret()
    header = json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode()
    payload = json.dumps({
        'uid': uid,
        'db': db,
        'exp': int(time.time()) + TOKEN_EXPIRY,
        'iat': int(time.time()),
    }).encode()
    segments = [_b64url_encode(header), _b64url_encode(payload)]
    signing_input = '.'.join(segments).encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    segments.append(_b64url_encode(sig))
    return '.'.join(segments)


def verify_token(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        secret = _get_jwt_secret()
        signing_input = f'{parts[0]}.{parts[1]}'.encode()
        sig = _b64url_decode(parts[2])
        expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64url_decode(parts[1]))
        if payload.get('exp', 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def json_response(data, status=200):
    headers = {
        'Access-Control-Allow-Origin': CORS_ORIGIN,
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
        'Access-Control-Allow-Credentials': 'true',
    }
    return Response(
        json.dumps(data, default=str),
        status=status,
        content_type='application/json',
        headers=headers,
    )


def authenticate_request():
    """Authenticate via JWT Bearer token or X-API-Key header. Returns user ID or None."""
    # JWT Bearer token
    auth_header = request.httprequest.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        payload = verify_token(auth_header[7:])
        if payload:
            return payload.get('uid')

    # API key
    api_key = request.httprequest.headers.get('X-API-Key', '')
    if api_key:
        key_rec = request.env['sutradhara.api.key'].sudo().search([
            ('key', '=', api_key),
            ('active', '=', True),
        ], limit=1)
        if key_rec and not key_rec._is_expired() and key_rec._check_rate_limit():
            key_rec.sudo().write({'last_used': time.strftime('%Y-%m-%d %H:%M:%S')})
            return key_rec.user_id.id

    return None


def require_auth(func):
    """Decorator that ensures request is authenticated."""
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)
        request.update_env(user=uid)
        return func(*args, **kwargs)
    return wrapper


def _log_request(endpoint, method, status, api_key_id=None, uid=None, error=None, duration_ms=0):
    """Log an API request."""
    try:
        request.env['sutradhara.api.log'].sudo().create({
            'api_key_id': api_key_id,
            'user_id': uid,
            'endpoint': endpoint,
            'method': method,
            'ip_address': request.httprequest.remote_addr,
            'response_code': status,
            'response_time_ms': duration_ms,
            'error_message': error,
        })
    except Exception as e:
        _logger.error('Failed to log API request: %s', e)


class SutradharaAuthController(http.Controller):

    @http.route('/api/v1/auth/login', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def login(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return json_response({})

        try:
            body = json.loads(request.httprequest.data or '{}')
        except json.JSONDecodeError:
            return json_response({'error': 'Invalid JSON body'}, status=400)

        db = body.get('db', request.db)
        login = body.get('login', '')
        password = body.get('password', '')

        if not login or not password:
            return json_response({'error': 'login and password are required'}, status=400)

        try:
            uid = request.session.authenticate(db, login, password)
        except AccessDenied:
            uid = False

        if not uid:
            return json_response({'error': 'Invalid credentials'}, status=401)

        token = generate_token(uid, db)
        user = request.env['res.users'].sudo().browse(uid)

        return json_response({
            'token': token,
            'token_type': 'Bearer',
            'expires_in': TOKEN_EXPIRY,
            'user': {
                'id': user.id,
                'name': user.name,
                'login': user.login,
                'email': user.email,
            },
        })

    @http.route('/api/v1/auth/refresh', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def refresh(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return json_response({})

        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Valid token required'}, status=401)

        db = request.db
        token = generate_token(uid, db)

        return json_response({
            'token': token,
            'token_type': 'Bearer',
            'expires_in': TOKEN_EXPIRY,
        })

    @http.route('/api/v1/auth/me', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def me(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return json_response({})

        uid = authenticate_request()
        if not uid:
            return json_response({'error': 'Authentication required'}, status=401)

        user = request.env['res.users'].sudo().browse(uid)
        if not user.exists():
            return json_response({'error': 'User not found'}, status=404)

        return json_response({
            'id': user.id,
            'name': user.name,
            'login': user.login,
            'email': user.email,
            'company_id': user.company_id.id,
            'company_name': user.company_id.name,
            'groups': user.groups_id.mapped('full_name'),
        })

    @http.route('/api/v1/health', type='http', auth='none', methods=['GET'], csrf=False)
    def health(self, **kwargs):
        return json_response({
            'status': 'ok',
            'service': 'sutradhara_api',
            'version': '1.0.0',
        })
