from odoo.addons.portal.controllers import portal
from odoo.addons.web.controllers.home import Home
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo import http, _, fields
import binascii
from odoo.addons.portal.controllers.mail import _message_post_helper



class CustomerPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        pricelist_id = partner.property_product_pricelist
        if 'pricelist_count' in counters:
            values['pricelist_count']=len(pricelist_id) if pricelist_id else 0
        return values

    @http.route(['/my/pricelists/<int:partner_id>/<int:pricelist_id>/accept'], type='json', auth="public", website=True)
    def portal_pricelist_accept(self, partner_id, pricelist_id, access_token=None, name=None, signature=None, **kwargs):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            partner_sudo = self._document_check_access('res.partner', partner_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid partner.')}

        if not partner_sudo:
            return {'error': _('The partner is missing.')}

        try:
            pricelist_sudo = request.env['product.pricelist'].sudo().search([('id', '=', pricelist_id)])
        except (AccessError, MissingError):
            return {'error': _('Invalid pricelist.')}

        if not pricelist_id:
            return {'error': _('The pricelist is missing.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            partner_sudo.sudo().write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
                'status': 'active'
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}

        # _message_post_helper.sudo()(
        #     'res.partner',
        #     partner_sudo.sudo().id,
        #     _('Pricelist named %s signed by %s', pricelist_sudo.sudo().display_name, name),
        #     token=access_token,
        # )
        partner_sudo.sudo().message_post(body=_(
            'Pricelist named %s signed by %s', pricelist_sudo.sudo().display_name, name))

        query_string = '&message=sign_ok'

        return {
            'force_refresh': True,
            'query_string': query_string,
            'redirect_url': '/my/pricelists',
        }

    @http.route(['/my/pricelists/<int:partner_id>/<int:pricelist_id>/decline'], type='http', auth="public", methods=['POST'], website=True)
    def portal_pricelist_decline(self, partner_id, pricelist_id, access_token=None, decline_message=None, **kwargs):
        try:
            partner_sudo = self._document_check_access('res.partner', partner_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        try:
            pricelist_sudo = request.env['product.pricelist'].sudo().search([('id', '=', pricelist_id)])
        except (AccessError, MissingError):
            return {'error': _('Invalid pricelist.')}

        if not pricelist_id:
            return {'error': _('The pricelist is missing.')}

        query_string = ''
        if decline_message:
            # _message_post_helper.sudo()(
            #     'res.partner',
            #     partner_sudo.id,
            #     decline_message,
            #     token=access_token,
            # )
            try:
                partner_sudo.sudo().write({
                    'has_rejected': True
                })
                request.env.cr.commit()
            except (TypeError, binascii.Error) as e:
                return {'error': _('Invalid signature data.')}
            partner_sudo.sudo().message_post(body=_(
                'Pricelist named %s rejected by %s', pricelist_sudo.sudo().display_name, partner_sudo.sudo().name))
            query_string = '&message=rejected'

        return request.redirect('/my/pricelists?force_refresh=True')

        # return {
        #     'force_refresh': True,
        #     'query_string': query_string,
        #     'redirect_url': '/my/pricelists',
        # }


class CustomHome(Home):

    @http.route('/my/pricelists', type='http', auth="user", website=True)
    def my_pricelists(self, **kw):
        partner = request.env.user.partner_id
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        pricelist_id = partner.property_product_pricelist
        total_price = 0
        if pricelist_id:
            for item in pricelist_id.item_ids:
                    total_price += item.fixed_price
        currency_id = request.env.user.company_id.currency_id
        # ConfigValues = request.env['res.config.settings'].sudo().website_constant()
        # db = request.session.get('db')
        value = {
            'url': "%s/my/pricelists/%s" % (base_url, partner.id),
            'pricelist_id': pricelist_id,
            'total_price': total_price,
            'currency_id': currency_id,
            'partner_id': partner,
        }
        return http.request.render('custom_pricelist.portal_pricelist_verification', value)
