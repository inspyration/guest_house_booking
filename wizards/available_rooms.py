#-*- coding: utf8 -*-

from openerp.osv import osv, fields

class AvailableRoom(osv.TransientModel):
    _name = "bbs_booking.available.rooms.wizard"
    
    _columns = {
        'arrival_day': fields.date(
            string="Arrival day",
            required=True,
        ),
        'departure_day': fields.date(
            string="Departure day",
            required=True,
        ),
        'persons_number': fields.integer(
            string="Number of Persons",
            required=True,
        ),
    }
    
    def search_available_rooms(self, cr, uid, ids, context=None):
        room_model = self.pool.get('bbs_booking.room')
        # Wizard => one id
        current_id = ids[0]
        
        # Read wizard's data
        res = self.read(cr, uid, current_id, context=context)
        
        room_ids = room_model.search(cr, uid, [], context=context)
        room_ids = [id for id in room_ids if room_model.is_available(cr, uid, id, res['arrival_day'], res['departure_day'], context=context)]
        if len(room_ids)>0:
            return {
                'domain': "[('id','in',[" + ','.join(map(str,room_ids)) + "])]",
                'view_mode': 'tree,form',
                'view_type': 'tree',
                'context': {'tree_view_ref' : 'bbs_booking.view_bbs_booking_room_tree'},
                'res_model': 'bbs_booking.room',
                'type': 'ir.actions.act_window',
            }
        else:
            return {'type': 'ir.actions.act_window_close'}