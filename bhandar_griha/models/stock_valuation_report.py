from odoo import api, fields, models, tools


class StockValuationReport(models.Model):
    _name = 'bhandar.griha.stock.valuation'
    _description = 'Stock Valuation Report'
    _auto = False
    _order = 'product_id, warehouse_id'

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_categ_id = fields.Many2one(
        'product.category', string='Product Category', readonly=True,
    )
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=True)
    quantity = fields.Float(string='Quantity On Hand', readonly=True)
    standard_price = fields.Float(string='Unit Cost', readonly=True)
    total_value = fields.Float(string='Total Value', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    sq.product_id,
                    pt.categ_id AS product_categ_id,
                    sw.id AS warehouse_id,
                    SUM(sq.quantity) AS quantity,
                    pt.standard_price AS standard_price,
                    SUM(sq.quantity) * COALESCE(pt.standard_price, 0) AS total_value,
                    sq.company_id
                FROM stock_quant sq
                JOIN stock_location sl ON sl.id = sq.location_id
                JOIN stock_warehouse sw ON sl.parent_path LIKE CONCAT('%%/', sw.lot_stock_id::text, '/%%')
                    OR sl.id = sw.lot_stock_id
                JOIN product_product pp ON pp.id = sq.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE sl.usage = 'internal'
                GROUP BY
                    sq.product_id, pt.categ_id, sw.id,
                    pt.standard_price, sq.company_id
            )
        """ % self._table)
