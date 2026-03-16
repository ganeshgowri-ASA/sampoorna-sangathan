from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrDocumentType(models.Model):
    _name = 'hr.document.type'
    _description = 'Employee Document Type'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
    has_expiry = fields.Boolean(string='Has Expiry Date')
    required_for_onboarding = fields.Boolean()
    days_before_expiry_alert = fields.Integer(
        string='Alert Days Before Expiry', default=30,
    )


class HrDocument(models.Model):
    _name = 'hr.document'
    _description = 'Employee Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', required=True, ondelete='cascade', tracking=True,
    )
    document_type_id = fields.Many2one('hr.document.type', required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
    )
    issue_date = fields.Date()
    expiry_date = fields.Date(tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)
    verified_by_id = fields.Many2one('res.users', string='Verified By', readonly=True)
    verified_date = fields.Datetime(readonly=True)
    rejection_reason = fields.Text()
    notes = fields.Text()
    is_expiring_soon = fields.Boolean(compute='_compute_expiry_status', store=True)
    is_expired = fields.Boolean(compute='_compute_expiry_status', store=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    @api.depends('expiry_date')
    def _compute_expiry_status(self):
        today = fields.Date.today()
        for doc in self:
            if doc.expiry_date:
                doc.is_expired = doc.expiry_date < today
                alert_days = doc.document_type_id.days_before_expiry_alert or 30
                doc.is_expiring_soon = (
                    not doc.is_expired
                    and doc.expiry_date <= today + relativedelta(days=alert_days)
                )
            else:
                doc.is_expired = False
                doc.is_expiring_soon = False

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_verify(self):
        self.write({
            'state': 'verified',
            'verified_by_id': self.env.uid,
            'verified_date': fields.Datetime.now(),
        })

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_reset_draft(self):
        self.write({'state': 'draft', 'rejection_reason': False})

    @api.model
    def _cron_check_expiry(self):
        """Mark expired documents and notify about expiring ones."""
        today = fields.Date.today()
        expired = self.search([
            ('expiry_date', '<', today),
            ('state', '=', 'verified'),
        ])
        expired.write({'state': 'expired'})


class HrEmployeeDocument(models.Model):
    _inherit = 'hr.employee'

    document_ids = fields.One2many(
        'hr.document', 'employee_id', string='Documents',
    )
    document_count = fields.Integer(compute='_compute_document_count')

    @api.depends('document_ids')
    def _compute_document_count(self):
        for emp in self:
            emp.document_count = len(emp.document_ids)
