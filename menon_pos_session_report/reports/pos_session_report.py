# -*- coding: utf-8 -*-
from odoo import models


class PosSessionSalesReport(models.AbstractModel):
    _name = 'report.menon_pos_session_report.report_pos_session_sales'
    _description = 'POS Session Sales Report'

    def _get_report_values(self, docids, data=None):
        sessions = self.env['pos.session'].browse(docids)
        sessions_data = []

        for session in sessions:
            valid_orders = session.order_ids.filtered(lambda o: o.state not in ['cancel'])

            # --- Products grouped by POS category ---
            cat_map = {}
            for order in valid_orders:
                for line in order.lines:
                    cat = line.product_id.pos_categ_ids[:1]
                    cat_key = cat.id if cat else 0
                    cat_name = cat.name if cat else 'بدون فئة'
                    prod_name = line.product_id.name

                    if cat_key not in cat_map:
                        cat_map[cat_key] = {
                            'name': cat_name,
                            'qty': 0.0,
                            'total': 0.0,
                            'products': {},
                        }
                    cat = cat_map[cat_key]
                    if prod_name not in cat['products']:
                        cat['products'][prod_name] = {'qty': 0.0, 'total': 0.0}
                    cat['products'][prod_name]['qty'] += line.qty
                    cat['products'][prod_name]['total'] += line.price_subtotal_incl
                    cat['qty'] += line.qty
                    cat['total'] += line.price_subtotal_incl

            categories = []
            for cat in cat_map.values():
                cat['product_list'] = [
                    {'name': k, 'qty': v['qty'], 'total': v['total']}
                    for k, v in cat['products'].items()
                ]
                categories.append(cat)

            # --- Tax groups ---
            tax_groups = {}
            for order in valid_orders:
                for line in order.lines:
                    tax_names = ', '.join(line.tax_ids.mapped('name')) or 'دون ضرائب'
                    if tax_names not in tax_groups:
                        tax_groups[tax_names] = {'tax': 0.0, 'total': 0.0}
                    tax_groups[tax_names]['tax'] += line.price_subtotal_incl - line.price_subtotal
                    tax_groups[tax_names]['total'] += line.price_subtotal_incl
            tax_list = [{'name': k, 'tax': v['tax'], 'total': v['total']} for k, v in tax_groups.items()]

            # --- Payments ---
            payment_map = {}
            for order in valid_orders:
                for payment in order.payment_ids:
                    pm = payment.payment_method_id.name
                    payment_map[pm] = payment_map.get(pm, 0.0) + payment.amount
            payment_list = [{'name': k, 'amount': v} for k, v in payment_map.items()]

            # --- Discounts ---
            discount_lines = [
                line for order in valid_orders for line in order.lines if line.discount
            ]
            discount_count = len(set(line.order_id.id for line in discount_lines))
            total_discount = sum(
                line.price_unit * line.qty * line.discount / 100 for line in discount_lines
            )

            # --- Totals ---
            total_sales = sum(o.amount_total for o in valid_orders)
            total_qty = sum(
                line.qty for order in valid_orders for line in order.lines
            )
            transaction_count = len(valid_orders)

            # --- Expected cash balance ---
            cash_pm = session.payment_method_ids.filtered('is_cash_count')[:1]
            cash_in = sum(
                p.amount for o in valid_orders for p in o.payment_ids
                if p.payment_method_id in cash_pm
            )
            expected = session.cash_register_balance_start + cash_in

            sessions_data.append({
                'session': session,
                'categories': categories,
                'total_qty': total_qty,
                'total_sales': total_sales,
                'tax_list': tax_list,
                'payment_list': payment_list,
                'payment_total': sum(p['amount'] for p in payment_list),
                'discount_count': discount_count,
                'total_discount': total_discount,
                'transaction_count': transaction_count,
                'expected': expected,
                'currency': session.currency_id,
            })

        return {
            'doc_ids': docids,
            'doc_model': 'pos.session',
            'docs': sessions,
            'sessions_data': sessions_data,
        }
