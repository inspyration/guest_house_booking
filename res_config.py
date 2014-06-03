
from openerp.osv import fields, osv

class booking_config_settings(osv.osv_memory):
    _name = 'booking.config.settings'
    _inherit = 'base.config.settings'

    _columns = {
        'company_id': fields.many2one('res.company', string="Company", required=True), 
        
        'booking_title': fields.text(string="Booking title"),
    }
    
