{
    'name': 'SampoornaSangathan Core (सम्पूर्णसंगठन)',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Unified Organisation OS - Core Module with Dashboard & Branding',
    'description': """
SampoornaSangathan (सम्पूर्णसंगठन) - Unified Organisation Operating System
=============================================================================

Core module providing:
- Centralised dashboard with module launcher tiles
- Organisation profile and branding settings
- Shared utility models and mixins (audit trail, tagging)
- Base security groups and access rules
- Configuration settings for all sub-modules

Sub-modules: jana_seva_hrms, sambandha_path_crm, kosha_prabandhan_finance,
bhandar_griha_inventory, pariyojana_chakra_projects, sutradhara_api
    """,
    'author': 'SampoornaSangathan',
    'website': 'https://sampoorna-sangathan.vercel.app',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        'security/sangathan_groups.xml',
        'security/ir.model.access.csv',
        'data/sangathan_config_data.xml',
        'views/org_profile_views.xml',
        'views/sangathan_dashboard_views.xml',
        'views/res_config_settings_views.xml',
        'views/sangathan_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sampoorna_sangathan_core/static/src/css/sangathan_dashboard.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
}
