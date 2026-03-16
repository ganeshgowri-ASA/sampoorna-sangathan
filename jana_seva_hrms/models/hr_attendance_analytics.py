from odoo import api, fields, models, tools


class HrAttendanceAnalytics(models.Model):
    _name = 'hr.attendance.analytics'
    _description = 'Attendance Analytics'
    _auto = False
    _order = 'attendance_date desc'

    employee_id = fields.Many2one('hr.employee', readonly=True)
    department_id = fields.Many2one('hr.department', readonly=True)
    attendance_date = fields.Date(readonly=True)
    check_in = fields.Datetime(readonly=True)
    check_out = fields.Datetime(readonly=True)
    worked_hours = fields.Float(readonly=True)
    overtime_hours = fields.Float(readonly=True)
    is_late = fields.Boolean(readonly=True)
    month = fields.Char(readonly=True)
    year = fields.Integer(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    a.id,
                    a.employee_id,
                    e.department_id,
                    a.check_in::date AS attendance_date,
                    a.check_in,
                    a.check_out,
                    a.worked_hours,
                    GREATEST(a.worked_hours - 8.0, 0) AS overtime_hours,
                    CASE
                        WHEN EXTRACT(HOUR FROM a.check_in) >= 10 THEN TRUE
                        ELSE FALSE
                    END AS is_late,
                    TO_CHAR(a.check_in, 'YYYY-MM') AS month,
                    EXTRACT(YEAR FROM a.check_in)::int AS year
                FROM hr_attendance a
                JOIN hr_employee e ON a.employee_id = e.id
                WHERE a.check_out IS NOT NULL
            )
        """ % self._table)
