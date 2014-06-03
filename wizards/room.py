#-*- coding: utf8 -*-

from openerp.osv import osv, fields

class BookingRoomWizard(osv.TransientModel):
    _name = 'bbs_booking.booking.room.wizard'
    
    def default_get(self, cr, uid, fields, context=None):
        ret = osv.TransientModel.default_get(self, cr, uid, fields, context=context)
        booking_id = context.get('booking_id', False)
        if booking_id:
            ret['booking_id'] = booking_id
        return ret

    def _room_selection(self, cr, uid, context=None):
        booking_room_model = self.pool.get('bbs_booking.booking.room')
        room_model = self.pool.get('bbs_booking.room')

        if context is None or not context.has_key("booking_id"):
            return []

        # search the rooms already selected
        booking_room_ids = booking_room_model.search(
            cr,
            uid,
            [('booking_id','=',context['booking_id'])],
            context=context,
        )
        excluded_ids = list(set([r['room_id'][0] for r in booking_room_model.read(
            cr,
            uid, 
            booking_room_ids,
            ['room_id'],
            context=context,
        )]))

        # search the other room
        room_ids = room_model.search(
            cr,
            uid,
            [('id','not in',excluded_ids)],
            context=context,
        )

        # return 2 uplets (id, name)
        return [(r['id'], r['name']) for r in room_model.read(
            cr,
            uid,
            room_ids,
            ['id','name'],
            context=context,
        )]

    def add_room_to_booking(self, cr, uid, ids, context=None):
        booking_room_model = self.pool.get('bbs_booking.booking.room')
        # Wizard => one id
        current_id = ids[0]
        
        # Read wizard's data
        res = self.read(cr, uid, current_id, context=context)
        
        # Create 
        booking_room_model.create(
            cr,
            uid,
            {
                'booking_id': res['booking_id'][0],
                'room_id': res['room_id'][0],
                })
        
        # Close the window
        return {'type': 'ir.actions.act_window_close'}


    _columns = {
        'booking_id': fields.many2one(
            'bbs_booking.booking',
            string="Booking",
            required=True,
        ),
        'room_id': fields.selection(
            _room_selection,
            string="Room",
            required=True,
        ),
    }