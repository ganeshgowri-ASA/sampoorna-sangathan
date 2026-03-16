import base64
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ExpenseApprovalStage(models.Model):
    _name = 'kosha.expense.stage'
    _description = 'Expense Approval Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(string='Folded in Kanban')
    is_approved = fields.Boolean(string='Approval Stage')


class ExpenseApproval(models.Model):
    _name = 'kosha.expense.approval'
    _description = 'Expense Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    date = fields.Date(default=fields.Date.context_today, required=True)
    employee_id = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, required=True)
    department = fields.Char(string='Department')
    stage_id = fields.Many2one(
        'kosha.expense.stage',
        string='Stage',
        tracking=True,
        group_expand='_read_group_stage_ids',
        default=lambda self: self._default_stage_id(),
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ], default='draft', tracking=True, required=True)
    amount = fields.Float(string='Amount', required=True)
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id,
    )
    category = fields.Selection([
        ('travel', 'Travel'),
        ('office', 'Office Supplies'),
        ('utilities', 'Utilities'),
        ('marketing', 'Marketing'),
        ('it', 'IT & Software'),
        ('other', 'Other'),
    ], default='other', required=True)
    description = fields.Text()
    attachment_ids = fields.Many2many('ir.attachment', string='Receipts')
    ocr_status = fields.Selection([
        ('none', 'No Receipt'),
        ('pending', 'Pending OCR'),
        ('done', 'OCR Complete'),
        ('failed', 'OCR Failed'),
    ], default='none', string='OCR Status', tracking=True)
    ocr_raw_text = fields.Text(string='OCR Extracted Text', readonly=True)
    approver_id = fields.Many2one('res.users', string='Approver', tracking=True)
    approved_date = fields.Date(readonly=True)
    account_move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)

    def _default_stage_id(self):
        return self.env['kosha.expense.stage'].search([], limit=1, order='sequence')

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        return self.env['kosha.expense.stage'].search([])

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('Only submitted expenses can be approved.'))
            rec.write({
                'state': 'approved',
                'approver_id': self.env.user.id,
                'approved_date': fields.Date.today(),
            })
            approved_stage = self.env['kosha.expense.stage'].search(
                [('is_approved', '=', True)], limit=1,
            )
            if approved_stage:
                rec.stage_id = approved_stage

    def action_reject(self):
        for rec in self:
            if rec.state not in ('submitted', 'approved'):
                raise UserError(_('Only submitted or approved expenses can be rejected.'))
            rec.write({'state': 'rejected'})

    def action_pay(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('Only approved expenses can be marked as paid.'))
            rec.write({'state': 'paid'})

    def action_draft(self):
        self.write({'state': 'draft', 'approver_id': False, 'approved_date': False})

    def action_ocr_scan(self):
        """Placeholder for OCR receipt scanning.

        This method is designed to be extended with a real OCR provider
        (e.g., Google Vision, Tesseract, or a dedicated invoice OCR API).
        Currently extracts basic file metadata from the first attachment.
        """
        for rec in self:
            if not rec.attachment_ids:
                raise UserError(_('Please upload a receipt first.'))
            rec.ocr_status = 'pending'
            attachment = rec.attachment_ids[0]
            try:
                # Placeholder: In production, send attachment.datas to OCR API
                file_size = len(base64.b64decode(attachment.datas)) if attachment.datas else 0
                rec.ocr_raw_text = _(
                    'OCR Placeholder Result\n'
                    '----------------------\n'
                    'File: %s\n'
                    'Size: %s bytes\n'
                    'Type: %s\n\n'
                    'To enable real OCR, integrate with an OCR provider '
                    '(Google Vision API, Tesseract, etc.) by overriding '
                    'action_ocr_scan() in a custom module.'
                ) % (attachment.name, file_size, attachment.mimetype or 'unknown')
                rec.ocr_status = 'done'
                rec.message_post(body=_('OCR scan completed for receipt: %s') % attachment.name)
            except Exception as e:
                rec.ocr_status = 'failed'
                rec.ocr_raw_text = _('OCR failed: %s') % str(e)
                _logger.exception('OCR scan failed for expense %s', rec.name)
