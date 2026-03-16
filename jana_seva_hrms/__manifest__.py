{
    'name': 'Jana Seva HRMS',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Extended HR with onboarding workflows, document management, leave dashboard & attendance analytics',
    'description': """
        Jana Seva HRMS - Sampoorna Sangathan
        =====================================
        Extends Odoo HR with:
        - Employee onboarding workflows with stage tracking
        - Document management (upload, verify, expire tracking)
        - Leave dashboard with team calendar view
        - Attendance analytics with overtime and summary reports
    """,
    'author': 'Sampoorna Sangathan',
    'website': 'https://sampoornasangathan.com',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'hr_attendance',
        'hr_holidays',
        'hr_contract',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/onboarding_stage_data.xml',
        'views/hr_onboarding_views.xml',
        'views/hr_document_views.xml',
        'views/hr_leave_dashboard_views.xml',
        'views/hr_attendance_analytics_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
