# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

import operator

import logging
_logger = logging.getLogger('INSPY_booking')


#==============================================================================#
#                                     Booking                                  #
#==============================================================================#
class Booking(osv.Model):
    _name = "bbs_booking.booking"
    _description = "booking"
    _inherit = ['mail.thread']

    _states = [
        ('pending', "Pending"),
        ('approved', "Approved"),
        ('denied', "Denied"),
    ]

    def _get_guarantee(self, cr, uid, ids, field, arg, context=None):
        res = {}
        for reserv in self.browse(cr, uid, ids, context=context):
            if reserv.config_id and reserv.price > 0:
                res[reserv.id] = int(round(reserv.price*reserv.config_id.guarantee/100, -2))
            else:
                res[reserv.id] = 0
        return res

    def _get_balance_due(self, cr, uid, ids, field, arg, context=None):
        res = {}
        for reserv in self.browse(cr, uid, ids, context=context):
            res[reserv.id] = int(reserv.price - reserv.guarantee)
        return res

    def _date_to_datetime(self, cr, uid, ids, field, arg, context=None):
        if field == 'arrival_date':
            f, h = operator.attrgetter('arrival_day'), " 16:00:00"
        else: # departure_date
            f, h = operator.attrgetter('departure_day'), " 10:00:00"

        for b in self.browse(cr, uid, ids, context=context):
            _logger.debug("f(b, %s, %s)=%s" % (field, b.id, f(b)))

        result = {b.id: f(b) + h for b in self.browse(cr, uid, ids, context=context)}

        _logger.debug("_date_to_datetime %s: %s" % (field, result))

        return result

    _columns = {
        'name': fields.char(
            'Title',
            size=256,
            required=True,
            select=True,
        ),
        'arrival_day': fields.date(
            string="Arrival day",
            required=True,
        ),
        'arrival_date': fields.function(
            _date_to_datetime,
            type='datetime',
            string="Arrival date",
            store=True,
        ),
        'departure_day': fields.date(
            string="Departure day",
            required=True,
        ),
        'departure_date': fields.function(
            _date_to_datetime,
            type='datetime',
            string="Departure date",
            store=True,
        ),
        'create_date' : fields.datetime(
            'Creation date',
             readonly=True,
        ),
        'persons_number': fields.integer(
            string="Number of Persons",
        ),
        'partner_id': fields.many2one(
            'res.partner',
            string="Client",
            required=True,
        ),
        'state': fields.selection(
            _states,
            string="Booking's state",
        ),
        'price': fields.integer(
            string="Price of booking",
        ),
        'guarantee': fields.function(
            _get_guarantee,
            type='integer',
            string="Guarantee",
        ),
        'balance_due': fields.function(
            _get_balance_due,
            type='integer',
            string="Balance due",
        ),
        'config_id': fields.many2one(
            'bbs_booking.config',
            string="Booking configuration",
        ),
        'room_ids': fields.one2many(
            'bbs_booking.booking.room',
            'booking_id',
            string="Rooms",
        ),
    }

    _order = 'create_date desc'

    _defaults = {
        'state': 'pending',
    }

    _sql_constraints = [
        (
            "bbs_booking_arrival_before_departure_date_constraint",
            "CHECK(arrival_date < departure_date)",
            "'Arrival date' should be before 'Departure date'",
        ),
        (
            "bbs_booking_arrival_before_departure_day_constraint",
            "CHECK(arrival_day < departure_day)",
            "'Arrival day' should be before 'Departure day'",
        ),
    ]


    def create(self, cr, uid, values, context=None):
        """
        Check availablity before creating.
        """
        arrival_date, departure_date, = values['arrival_day'] + " 16:00:00", values['departure_day'] + " 10:00:00"
        _logger.info("Date arrivee : %s (%s)" % (arrival_date, type(arrival_date)))
        _logger.info("Date depart : %s (%s)" % (departure_date, type(departure_date)))
        _logger.info("Jour arrivee : %s (%s)" % (values['arrival_day'], type(values['arrival_day'])))
        _logger.info("Jour depart  : %s (%s)" % (values['departure_day'], type(values['departure_day'])))
        if not self.check_availability(cr, uid, arrival_date, departure_date, context=context):
            raise osv.except_osv(_('Unavailable dates !'), _("Unable to book for the selected dates."))
        return osv.Model.create(self, cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        """
        Check availablity before writing.
        """
        # Can't change many booking dates at once.
        if type(ids) == list and len(ids) > 1 and ('arrival_date' in values or 'departure_date' in values):
            raise osv.except_osv(('Date Change denied !'), ("Changing departure or arrival dates for several bookings at the same time is not allowed."))
        elif type(ids) != list:
            ids = [ids]

        arrival_date, departure_date = None, None

        # Get the two dates (if it is true, we are sure that there is one and only one id in 'ids')
        if 'arrival_day' in values and 'departure_day' not in values:
            _logger.debug("Only arrival_date")
            read = self.read(cr, uid, ids[0], ['departure_date'], context=context)
            arrival_date, departure_date = values['arrival_day'] + " 16:00:00", read['departure_date']
        elif 'departure_day' in values and 'arrival_day' not in values:
            _logger.debug("Only date_départ")
            read = self.read(cr, uid, ids[0], ['arrival_date'], context=context)
            arrival_date, departure_date = read['arrival_date'], values['departure_day'] + " 10:00:00"

        if arrival_date is not None: # departure_date is not None too !
            _logger.debug("Calcul de plage disponible en update !")
            # Checking available periods. (if it is true, we are sure that there is one and only one id in 'ids')
            if not self.check_availability(cr, uid, arrival_date, departure_date, current_id=ids[0], context=context):
                raise osv.except_osv(('Unavailable dates !'), ("Unable to book for the selected dates."))

#         self.message_post(cr, uid, ids, _('Booking <b>updated</b>'), context=context)

        return osv.Model.write(self, cr, uid, ids, values, context=context)


    def accept_booking(self, cr, uid, ids, context=None, *args):
        """
        Change state to 'approved'.
        """
        if type(ids) != list:
            ids = [ids]
        read = self.read(cr, uid, ids, ['price','config_id'], context=context)
        if any(r['price'] <= 0 for r in read):
            raise osv.except_osv(_('Price not set !'), _("Booking price has to be set."))
        if any(not r['config_id'] for r in read): 
            raise osv.except_osv(_('No booking configuration!'), _("Please choose a booking configuration"))
        self.write(cr, uid, ids, {'state': 'approved'})
        self.message_post(cr, uid, ids, _('Booking <b>approved</b>'), context=context)
        
        self.send_email(cr, uid, ids, context=context)   
        return True
    
    
    def send_email(self, cr, uid, ids, context=None):
        _logger.info('================send email==================')
        template_id=self.pool.get('email.template').search(cr, uid, [('name', '=', 'House booking - Send by Email')], context=context)[0]
        _logger.info('........template id..........', template_id)
        email_obj=self.pool.get('email.template').send_mail(cr, uid, template_id, ids[0], force_send=True)
        _logger.info('email_obj................', email_obj)
    
    
    
    def refuse_booking(self, cr, uid, ids, context=None, *args):
        """
        Change state to 'denied'.
        """
        self.write(cr, uid, ids, {'state': 'denied'})
        self.message_post(cr, uid, ids, _('Booking <b>denied</b>'), context=context)
        return True

    def check_availability(self, cr, uid, arrival_date, departure_date, current_id=None, context=None):
        """
        Return True if all dates between arrival_date and departure_date are available, False otherwise.
        """
        # sch : supprimé au 15 mai
        #if len(arrival_date) == 10:
        #    arrival_date += " 16:00:00"
        #if len(departure_date) == 10:
        #    departure_date += " 16:00:00"
        # Domain of bookings crossing targeted period.
        domaine = [
            ('state', '!=', 'denied'),
            '!',
            '|',
            ('arrival_date','>=',departure_date),
            ('departure_date','<=',arrival_date),
        ]
        
        sch = self.search(cr, uid, [], context=context)
        brw = self.browse(cr, uid, sch, context=context)
        for b in brw:
            _logger.debug("Dates courantes : %s, %s" % (b.arrival_date, b.departure_date))


        # Remove current booking.
        if current_id is not None:
            _logger.debug("Rajout de l'identifiant : %s" % current_id)
            domaine.insert(0, ('id', '!=', current_id))

        search = self.search(cr, uid, domaine, context=context)
        _logger.debug("------\nsearch : %s\n%s\n" % (search, domaine))
        long = len(search)
        _logger.debug("len du search : %s" % long)
        res = long == 0
        _logger.debug("res (true or false) : %s" % res)
        return res




#==============================================================================#
#                                Booking - Room                                #
#==============================================================================#
class BookingRoom(osv.Model):
    _name = "bbs_booking.booking.room"
    _description = ""
    
    _columns = {
        'booking_id': fields.many2one(
            'bbs_booking.booking',
            string="Booking",
        ),
        'room_id': fields.many2one(
            'bbs_booking.room',
            string="Room",
        ),
        # Fields related to the booking
        'arrival_date': fields.related(
            'booking_id',
            'arrival_day',
            readonly=True,
            type='datetime',
            relation='bbs_booking.booking',
            string="Arrival day",
        ),
        'departure_date': fields.related(
            'booking_id',
            'departure_day',
            readonly=True,
            type='datetime',
            relation='bbs_booking.booking',
            string="Departure day",
        ),
        'state': fields.related(
            'booking_id',
            'state',
            readonly=True,
            type='selection',
            relation='bbs_booking.booking',
            string="State",
        ),
        # Fields related to the room
        'type_id': fields.related(
            'room_id',
            'type_id',
            readonly=True,
            type='many2one',
            relation='bbs_booking.room.type',
            string="Type of the room",
        ),
    }





#==============================================================================#
#                                      Room                                    #
#==============================================================================#
class Room(osv.Model):
    _name = "bbs_booking.room"
    _description = ""
    
    _columns = {
        'name': fields.char(
            'Title',
            size=256,
            required=True,
            select=True,
        ),
        'type_id': fields.many2one(
            'bbs_booking.room.type',
            string="Type of the room",
        ),
        'booking_ids': fields.one2many(
            'bbs_booking.booking.room',
            'room_id',
            string="Bookings",
        ),
    }



#==============================================================================#
#                                    Room type                                 #
#==============================================================================#
class RoomType(osv.Model):
    _name = "bbs_booking.room.type"
    _description = ""
    
    _columns = {
        'name': fields.char(
            'Title',
            size=256,
            required=True,
            select=True,
        ),
        'nb_berth': fields.integer( 
            string="Number of place in this room",
        ),
    }


#==============================================================================#
#                                     Config                                   #
#==============================================================================#
class BookingConfig(osv.Model):
    _name = "bbs_booking.config"
    _description = ""
    
    # Simple room, double, twin, triple, quadruple, etc.
    
    _columns = {
        'name': fields.char(
            string="Name",
            help="Used for the voucher's title"
        ),
        'guarantee': fields.integer(
            string="Guarantee (%)",
        ),
        'deposit': fields.integer(
            string="Deposit",
        ),
    }