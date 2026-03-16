{
    'name': 'Lekha Peethika',
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Document management, meeting scheduler, announcements, policies & employee directory',
    'description': """
Lekha Peethika - Internal Communication & Document Hub
=======================================================
- Document management with categories and tags
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
