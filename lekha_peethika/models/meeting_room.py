from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MeetingRoom(models.Model):
    _name = 'lekha.meeting.room'
    _description = 'Meeting Room'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string='Room Name', required=True)
    code = fields.Char(string='Room Code')
    capacity = fields.Integer(string='Capacity', default=10)
    location = fields.Char(string='Location')
    facilities = fields.Text(string='Facilities')
    has_projector = fields.Boolean(string='Projector')
    has_whiteboard = fields.Boolean(string='Whiteboard')
    has_video_conf = fields.Boolean(string='Video Conferencing')
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Color Index')
    booking_ids = fields.One2many(
        'lekha.room.booking',
        'room_id',
        string='Bookings',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )


class RoomBooking(models.Model):
    _name = 'lekha.room.booking'
    _description = 'Room Booking'
    _inherit = ['mail.thread']
    _order = 'start_datetime desc'

    name = fields.Char(string='Meeting Subject', required=True)
    room_id = fields.Many2one(
        'lekha.meeting.room',
        string='Meeting Room',
        required=True,
        tracking=True,
    )
    calendar_event_id = fields.Many2one(
        'calendar.event',
        string='Calendar Event',
        ondelete='cascade',
    )
    start_datetime = fields.Datetime(string='Start', required=True, tracking=True)
    stop_datetime = fields.Datetime(string='End', required=True, tracking=True)
    organizer_id = fields.Many2one(
        'res.users',
        string='Organizer',
        default=lambda self: self.env.user,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    @api.constrains('room_id', 'start_datetime', 'stop_datetime')
    def _check_room_availability(self):
        for booking in self:
            if booking.state == 'cancelled':
                continue
            overlapping = self.search([
                ('id', '!=', booking.id),
                ('room_id', '=', booking.room_id.id),
                ('state', '!=', 'cancelled'),
                ('start_datetime', '<', booking.stop_datetime),
                ('stop_datetime', '>', booking.start_datetime),
            ])
            if overlapping:
                raise ValidationError(
                    'Room "%s" is already booked for the selected time slot.'
                    % booking.room_id.name
                )

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
