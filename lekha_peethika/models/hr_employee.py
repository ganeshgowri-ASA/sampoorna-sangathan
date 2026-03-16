from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    bio = fields.Text(string='Bio')
    skills_text = fields.Text(string='Skills & Expertise')
    linkedin_url = fields.Char(string='LinkedIn Profile')
    employee_type_display = fields.Selection([
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
        ('volunteer', 'Volunteer'),
    ], string='Employment Type')
