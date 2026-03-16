{
    'name': 'Sutradhara API',
    'version': '17.0.1.0.0',
    'category': 'Technical',
    'summary': 'REST API bridge between Odoo backend and Vercel frontend',
    'description': """
        Sutradhara API - The Director/Orchestrator
        ============================================
        REST API controllers exposing JSON endpoints for all Sampoorna Sangathan
        modules (HRMS, CRM, Finance, Inventory, Projects).

        Features:
        - JWT token authentication
        - API key management
        - CRUD operations for all custom models
        - Webhook dispatcher
        - Rate limiting
        - CORS support for Vercel frontend
    """,
    'author': 'Sampoorna Sangathan',
    'website': 'https://sampoorna-sangathan.vercel.app',
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['requests'],
    },
    'depends': [
        'base',
        'sampoorna_sangathan_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'views/api_key_views.xml',
        'views/webhook_views.xml',
        'views/api_log_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
