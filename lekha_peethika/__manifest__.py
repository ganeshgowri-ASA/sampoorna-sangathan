{
    'name': 'Lekha Peethika',
    'version': '17.0.2.0.0',
    'category': 'Productivity',
    'summary': 'Document management with templates, version control, collaboration, announcements & policies',
    'description': """
Lekha Peethika - Internal Communication & Document Hub
=======================================================
Inspired by the vidyalaya-office AI-native document suite:

- Document management with categories and tags
- Document templates (general, SOP, form, report, letter, policy)
- Full version history with change summaries
- Document collaborators with view/comment/edit permissions
- Document classification (public, internal, confidential, restricted)
- Meeting scheduler with room booking
- Announcement board
- Company policy portal
- Enhanced employee directory view
    """,
    'author': 'Sampoorna Sangathan',
    'website': 'https://sampoornasangathan.com',
    'license': 'LGPL-3',
    'depends': [
        'sampoorna_sangathan_core',
        'mail',
        'calendar',
        'contacts',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/document_category_data.xml',
        'data/meeting_room_data.xml',
        'views/document_views.xml',
        'views/document_template_views.xml',
        'views/meeting_room_views.xml',
        'views/announcement_views.xml',
        'views/policy_views.xml',
        'views/employee_directory_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
