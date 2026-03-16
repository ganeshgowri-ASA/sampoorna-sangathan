{
    'name': 'Sambandha Path CRM',
    'version': '17.0.2.0.0',
    'category': 'Sales/CRM',
    'summary': 'Advanced CRM with AI scoring, forecasting, journey mapping, deal rooms & automation',
    'description': """
        Sambandha Path CRM - Sampoorna Sangathan
        ==========================================
        Extends Odoo CRM with:
        - AI-powered lead scoring (activity-based + configurable rules)
        - Sales forecasting dashboard with revenue predictions
        - Customer journey map (chronological interaction timeline)
        - Automated follow-up rules engine with cron execution
        - Deal rooms for collaborative opportunity management
        - Customer 360 view (all interactions in one place)
        - Pipeline analytics dashboard with SQL-based reporting
        - Email template library for sales outreach
    """,
    'author': 'Sampoorna Sangathan',
    'website': 'https://sampoornasangathan.com',
    'license': 'LGPL-3',
    'depends': [
        'sampoorna_sangathan_core',
        'crm',
        'sale',
        'sale_management',
        'mail',
        'calendar',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/lead_scoring_data.xml',
        'data/email_template_data.xml',
        'data/ir_cron_data.xml',
        'views/lead_scoring_rule_views.xml',
        'views/crm_lead_views.xml',
        'views/customer_360_views.xml',
        'views/pipeline_analytics_views.xml',
        'views/sales_forecast_views.xml',
        'views/customer_journey_views.xml',
        'views/followup_rule_views.xml',
        'views/deal_room_views.xml',
        'views/email_template_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
