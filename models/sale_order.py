from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('partner_id', 'company_id')
    def _compute_pricelist_id(self):
        for order in self:
            if order.state != 'draft':
                continue
            if not order.partner_id:
                order.pricelist_id = False
                continue
            order = order.with_company(order.company_id)
            ## new code
            if not order.pricelist_id:
                order.pricelist_id = order.partner_id.property_product_pricelist
                if order.pricelist_id:
                    if order.pricelist_id.is_published == False:
                        raise UserError('Pricelist must be Published')
                    else:
                        pricelist = self.env['product.pricelist'].browse(order.pricelist_id.id)
                        order_line = []

                        for item in pricelist.item_ids:
                            if item.product_id:
                                order_line.append((0, 0, {
                                    'product_template_id': item.product_tmpl_id.id,
                                    'product_id': item.product_id.id,
                                    'name': item.product_id.get_product_multiline_description_sale(),
                                    'product_uom_qty': item.min_quantity,
                                    'display_type': False,
                                    'product_uom': item.product_id.uom_id.id,
                                    'price_unit': item.fixed_price or item.compute_price
                                }))
                        order.order_line = order_line

    @api.onchange('pricelist_id')
    def change_pricelist_id(self):
        for rec in self:
            if rec.pricelist_id and not rec.partner_id:
                if rec.pricelist_id.is_published == False:
                    raise UserError('Pricelist must be Published')
                else:
                    pricelist = self.env['product.pricelist'].browse(rec.pricelist_id.id)
                    order_line = []

                    for item in pricelist.item_ids:
                        if item.product_id:
                            order_line.append((0, 0, {
                                'product_template_id': item.product_tmpl_id.id,
                                'product_id': item.product_id.id,
                                'name': item.product_id.get_product_multiline_description_sale(),
                                'display_type': False,
                                'product_uom': item.product_id.uom_id.id,
                                'product_uom_qty': item.min_quantity,
                                'price_unit': item.fixed_price or item.compute_price
                            }))
                    rec.order_line = order_line

    # @api.model
    # def create_contract_with_pricelist(self, partner_id, pricelist_id):
    #     pricelist = self.env['product.pricelist'].browse(pricelist_id)
    #     order_lines = []
    #
    #     for item in pricelist.item_ids:
    #         if item.product_id:
    #             order_lines.append((0, 0, {
    #                 'product_id': item.product_id.id,
    #                 'product_uom_qty': 1,
    #                 'price_unit': item.fixed_price or item.compute_price,
    #             }))
    #
    #     order = self.create({
    #         'partner_id': partner_id,
    #         'pricelist_id': pricelist_id,
    #         'order_line': order_lines,
    #     })
    #
    #     return order