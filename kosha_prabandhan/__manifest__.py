{
    'name': 'Kosha Prabandhan',
    'version': '17.0.1.1.0',
    'category': 'Accounting',
    'summary': 'Financial KPI dashboard, budget planning, expense approval, bank reconciliation, GST compliance & cash flow forecasting',
    'description': """
        Kosha Prabandhan - Sampoorna Sangathan
        =======================================
        Extends Odoo Accounting with:
        - Financial KPI dashboard with real-time metrics & multi-currency indicators
        - Budget planning model with variance tracking
        - Expense approval workflow with OCR receipt scanning
        - Invoice analytics (aging, trends, top vendors/customers)
        - Bank reconciliation (match bank statements to journal entries)
        - GST compliance reports (GSTR-1, GSTR-3B summaries)
        - GST filing status tracker (due dates, ARN, filing status)
        - Cash flow forecasting view
    """,
    'author': 'Sampoorna Sangathan',
    'website': 'https://sampoornasangathan.com',
    'license': 'LGPL-3',
    'depends': [
        'sampoorna_sangathan_core',
        'account',
        'account_payment',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/expense_approval_stages.xml',
        'data/bank_reconciliation_data.xml',
        'views/financial_kpi_views.xml',
        'views/budget_planning_views.xml',
        'views/expense_approval_views.xml',
        'views/invoice_analytics_views.xml',
        'views/gst_compliance_views.xml',
        'views/gst_filing_views.xml',
        'views/bank_reconciliation_views.xml',
        'views/cash_flow_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
