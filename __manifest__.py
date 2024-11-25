# -*- coding: utf-8 -*-
{
    'name': 'Custom Pricelist',
    'version': '17.0.0.1',
    'category': 'Sales',
    'summary': """This module allows the client to have published pricelist which the client    
        will sign via portal""",
    'author': 'Nida Zehra',
    'depends': ['base', 'sale_management', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'views/product_pricelist_view.xml',
        'views/res_partner_view.xml',
        'views/portal_template.xml',
        'views/portal_pricelist_verification.xml'
    ],
    'assets': {
            'web.assets_frontend': [
                'custom_pricelist/static/src/js/pricelist_portal.js',
                'custom_pricelist/static/src/js/custom_js.js',
            ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
