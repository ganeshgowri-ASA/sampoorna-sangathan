from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    room_booking_id = fields.Many2one(
        'lekha.room.booking',
        string='Room Booking',
    )
    meeting_room_id = fields.Many2one(
        related='room_booking_id.room_id',
        string='Meeting Room',
        store=True,
        readonly=True,
    )
