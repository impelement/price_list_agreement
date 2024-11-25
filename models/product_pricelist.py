from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    is_published = fields.Boolean(string='Is Published', default=False)
    terms_conditions = fields.Html(string='Terms and Conditions')

    def _get_pricelist_portal_content_view(self):
        self.ensure_one()
        return 'custom_pricelist.product_pricelist_portal_content'

    @api.constrains('is_published')
    def _check_unpublish(self):
        for pricelist in self:
            if not pricelist.is_published and self.env['sale.order'].search([('pricelist_id', '=', pricelist.id)]):
                raise UserError('You cannot unpublish a pricelist that is used in a contract.')

    def action_publish_pricelist(self):
        for rec in self:

            rec.is_published = True

    def action_unpublish_pricelist(self):
        for rec in self:
            rec.is_published = False