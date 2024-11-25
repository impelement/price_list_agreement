from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request

class ResPartner(models.Model):
    _inherit = 'res.partner'

    signed_by = fields.Char(
        string="Signed By", copy=False)
    signed_on = fields.Datetime(
        string="Signed On", copy=False)
    signature = fields.Image(
        string="Signature",
        copy=False, attachment=True, max_width=1024, max_height=1024)
    has_signature = fields.Boolean(
        string="Has Signature",
        compute='_compute_has_signature',
        store=True
    )
    has_rejected = fields.Boolean(
        string="Has Rejected",
        default=False,
        store=True
    )
    partner_pricelist_ids = fields.One2many('partner.pricelist',
                                            'partner_id',
                                            string='Partner Pricelist')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='Status')
    previous_pricelist_id = fields.Many2one('product.pricelist',
                                            string='Previous Pricelist', store=True)
    previous_signed_on = fields.Datetime(
        string="Previous Signed On", copy=False)

    property_product_pricelist = fields.Many2one(
        comodel_name='product.pricelist',
        string="Pricelist",
        compute='_compute_product_pricelist',
        inverse="_inverse_product_pricelist",
        company_dependent=False,
        domain=lambda self: [('company_id', 'in', (self.env.company.id, False)),
                             ('is_published', '=', True)],
        help="This pricelist will be used, instead of the default one, for sales to the current partner")

    @api.depends('signature')
    def _compute_has_signature(self):
        for record in self:
            record.has_signature = bool(record.signature)

    def action_send_pricelist_verification_email(self):
        self.ensure_one()
        if not self.property_product_pricelist:
            raise UserError(_("Please set a pricelist for this partner first."))

        if self.property_product_pricelist.is_published == False:
            raise UserError(_("The pricelist should be published first."))

        template_id = self.env.ref('custom_pricelist.email_template_pricelist_verification').id
        email_values = {
            'email_to': self.email,
            'email_from': self.env.company.email
        }
        self.env['mail.template'].browse(template_id).sudo().send_mail(self.id, email_values=email_values, force_send=True)
        self.message_post(body=_("Pricelist verification email sent to the partner."))

    def get_portal_pricelist_verification_url(self):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # return f"{base_url}/my/pricelists/{self.id}"
        return f"{base_url}/web/login"

    @api.onchange('property_product_pricelist')
    def change_property_product_pricelist(self):
        for rec in self:
            rec.previous_signed_on = rec.signed_on
            rec.status = 'pending'
            rec.write({
                'signature': False,
                'has_signature': False,
                'signed_by': False,
                'signed_on': False,
                'has_rejected': False
            })

    def _inverse_product_pricelist(self):
        for partner in self:
            pls = self.env['product.pricelist'].search(
                [('country_group_ids.country_ids.code', '=', partner.country_id and partner.country_id.code or False)],
                limit=1
            )
            default_for_country = pls
            actual = self.env['ir.property']._get(
                'property_product_pricelist',
                'res.partner',
                'res.partner,%s' % partner.id)
            # update at each change country, and so erase old pricelist
            if partner.property_product_pricelist or (actual and default_for_country and default_for_country.id != actual.id):
                # keep the company of the current user before sudo
                self.env['ir.property']._set_multi(
                    'property_product_pricelist',
                    partner._name,
                    {partner.id: partner.property_product_pricelist or default_for_country.id},
                    default_value=default_for_country.id
                )
            ## update previous pricelist id
            if actual:
                partner.previous_pricelist_id = actual.id
                ## also make the previous pricelist shown in the pricelist agreement
                if partner.previous_pricelist_id:
                    partner.write({
                        'partner_pricelist_ids': [(0, 0,
                                                   {'status': 'archived',
                                                    'pricelist_id': partner.previous_pricelist_id.id,
                                                    'signed_on': partner.previous_signed_on
                                                    })]
                    })

    @api.depends('country_id')
    @api.depends_context('company')
    def _compute_product_pricelist(self):
        res = self.env['product.pricelist']._get_partner_pricelist_multi(self._ids)
        for partner in self:
            # partner.property_product_pricelist = res.get(partner.id)
            partner.property_product_pricelist = False

class PartnerPricelist(models.Model):
    _name = 'partner.pricelist'

    partner_id = fields.Many2one('res.partner', string='Partner ID')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='Status')
    signed_on = fields.Datetime(
        string="Signed On", copy=False)
