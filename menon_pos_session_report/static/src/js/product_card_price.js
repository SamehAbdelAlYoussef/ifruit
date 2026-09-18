/** @odoo-module */

import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";

patch(ProductCard.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
    },

    get formattedPrice() {
        const product = this.props.product;
        if (!product) {
            return "";
        }
        const pricelist =
            this.pos.getOrder()?.pricelist_id || this.pos.config?.pricelist_id || null;
        try {
            const price = product.getPrice(pricelist, 1);
            return this.env.utils.formatCurrency(price);
        } catch {
            return "";
        }
    },
});
