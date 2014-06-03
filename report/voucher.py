# -*- coding: utf-8 -*-

import time
from openerp.report import report_sxw

class voucher(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        report_sxw.rml_parse.__init__(self, cr, uid, name, context=context)

        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw(
    'bbs_booking.voucher',
    'bbs_booking.booking',
    'addons/bbs_booking/report/voucher.rml',
)
