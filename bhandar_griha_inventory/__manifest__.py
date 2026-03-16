{
    'name': 'Bhandar Griha - Inventory Management',
    'version': '17.0.1.0.0',
    'summary': 'Extended Inventory Management with Dashboard, Smart Replenishment & Analytics',
    'description': """
        Bhandar Griha Inventory extends Odoo Stock with:
        - Custom inventory dashboard with KPIs
        - Smart replenishment rules (min/max auto-reorder)
        - Warehouse utilization analytics
        - Barcode quick actions for stock moves
    """,
    'author': 'SampoornaSangathan',
    'category': 'Inventory/Inventory',
    'sequence': 5,
    'depends': [
        'stock',
        'purchase',
        'sampoorna_sangathan_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/inventory_dashboard_views.xml',
        'views/warehouse_extension_views.xml',
        'views/menu_items.xml',
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
