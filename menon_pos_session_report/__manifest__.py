# -*- coding: utf-8 -*-
{
    'name': 'Menon POS Session Sales Report',
    'version': '19.0.1.0.0',
    'summary': 'Print a PDF sales report from inside the POS interface',
    'author': 'Sayed Mohamed',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'reports/pos_session_report.xml',
        'views/pos_session_report_action.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'menon_pos_session_report/static/src/xml/pos_session_report_button.xml',
            'menon_pos_session_report/static/src/js/pos_session_report_button.js',
            'menon_pos_session_report/static/src/xml/product_card_price.xml',
            'menon_pos_session_report/static/src/js/product_card_price.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
