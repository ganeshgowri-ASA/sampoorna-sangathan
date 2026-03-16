{
    'name': 'Pariyojana Chakra - Project Management',
    'version': '17.0.1.0.0',
    'category': 'Project',
    'summary': 'Sprint planning, milestone tracking, resource allocation & timesheet analytics',
    'description': """
        Pariyojana Chakra - Sampoorna Sangathan Project Management
        ===========================================================
        Extends Odoo Project & Timesheets with:
        - Sprint planning with kanban board
        - Milestone & deliverable tracking
        - Resource allocation dashboard
        - Project templates for quick setup
        - Timesheet analytics with burndown charts
    """,
    'author': 'Sampoorna Sangathan',
    'website': 'https://sampoornasangathan.com',
    'license': 'LGPL-3',
    'depends': [
        'project',
        'hr_timesheet',
        'sampoorna_sangathan_core',
    ],
    'data': [
        'security/pariyojana_chakra_groups.xml',
        'security/ir.model.access.csv',
        'data/sprint_stage_data.xml',
        'data/project_template_data.xml',
        'views/project_sprint_views.xml',
        'views/project_milestone_views.xml',
        'views/project_deliverable_views.xml',
        'views/resource_allocation_views.xml',
        'views/project_template_views.xml',
        'views/timesheet_analytics_views.xml',
        'views/project_project_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pariyojana_chakra/static/src/css/dashboard.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
