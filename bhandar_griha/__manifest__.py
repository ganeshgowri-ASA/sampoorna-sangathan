{
    'name': 'Bhandar Griha - Warehouse Management',
    'version': '17.0.1.0.0',
    'category': 'Inventory/Warehouse',
    'summary': 'Warehouse dashboard, reorder alerts, multi-warehouse transfers, stock valuation & vendor ratings',
    'description': """
        Bhandar Griha - Sampoorna Sangathan Warehouse Management
        =========================================================
        Extends Stock and Purchase with:
        - Warehouse dashboard with real-time stock levels
        - Reorder level alerts with automated cron job
        - Multi-warehouse transfer wizard
        - Stock valuation reports
        - Vendor rating model
    """,
    'author': 'Sampoorna Sangathan',
    'website': 'https://sampoornasangathan.com',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'purchase',
        'mail',
        'sampoorna_sangathan_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'wizard/multi_warehouse_transfer_views.xml',
        'views/warehouse_dashboard_views.xml',
        'views/vendor_rating_views.xml',
        'views/stock_valuation_report_views.xml',
        'views/menu_views.xml',
        'report/stock_valuation_report_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
