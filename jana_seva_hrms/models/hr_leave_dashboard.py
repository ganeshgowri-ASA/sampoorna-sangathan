from odoo import api, fields, models, tools


class HrLeaveDashboard(models.Model):
    _name = 'hr.leave.dashboard'
    _description = 'Leave Dashboard Summary'
    _auto = False
    _order = 'employee_name'

    employee_id = fields.Many2one('hr.employee', readonly=True)
    employee_name = fields.Char(readonly=True)
    department_id = fields.Many2one('hr.department', readonly=True)
    leave_type_id = fields.Many2one('hr.leave.type', readonly=True)
    total_allocated = fields.Float(string='Allocated', readonly=True)
    total_taken = fields.Float(string='Taken', readonly=True)
    total_remaining = fields.Float(string='Remaining', readonly=True)
    year = fields.Integer(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    alloc.employee_id,
                    emp.name AS employee_name,
                    emp.department_id,
                    alloc.holiday_status_id AS leave_type_id,
                    COALESCE(alloc.total_allocated, 0) AS total_allocated,
                    COALESCE(taken.total_taken, 0) AS total_taken,
                    COALESCE(alloc.total_allocated, 0)
                        - COALESCE(taken.total_taken, 0) AS total_remaining,
                    EXTRACT(YEAR FROM CURRENT_DATE)::int AS year
                FROM (
                    SELECT
                        employee_id,
                        holiday_status_id,
                        SUM(number_of_days) AS total_allocated
                    FROM hr_leave_allocation
                    WHERE state = 'validate'
                    GROUP BY employee_id, holiday_status_id
                ) alloc
                LEFT JOIN (
                    SELECT
                        employee_id,
                        holiday_status_id,
                        SUM(number_of_days) AS total_taken
                    FROM hr_leave
                    WHERE state = 'validate'
                        AND EXTRACT(YEAR FROM date_from) = EXTRACT(YEAR FROM CURRENT_DATE)
                    GROUP BY employee_id, holiday_status_id
                ) taken ON alloc.employee_id = taken.employee_id
                    AND alloc.holiday_status_id = taken.holiday_status_id
                JOIN hr_employee emp ON alloc.employee_id = emp.id
            )
        """ % self._table)
