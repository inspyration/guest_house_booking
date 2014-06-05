# -*- coding: utf-8 -*-

{
    'name' : 'Booking management',
    'version' : '1.1',
    'author' : 'Alicia FLOREZ & Sébastien CHAZALLET',
    'category': 'Sales Management',
    'summary': 'Management of B&Bs bookings.',
    'description' : """
        Management of B&Bs booking.
    """,
    'website': 'http://www.inspyration.fr',
    'images' : [],
    'depends' : ['base', 'mail', 'crm'],
    'data': [
        'security/booking_security.xml',
        'security/ir.model.access.csv',
        'views/wizard_room.xml',
        'views/booking_view.xml',
        'report/voucher.xml',
        'views/email.xml',
    ],
    'js': [
    ],
    'qweb' : [
    ],
    'css':[
    ],
    'demo': [
        'demo/bbs_booking_demo.xml',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
