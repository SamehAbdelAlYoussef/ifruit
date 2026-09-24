# -*- coding: utf-8 -*-
import math
from datetime import datetime
from odoo import models


class DailyBranchReport(models.AbstractModel):
    _name = 'report.ifruit_daily_branch_report.report_daily_branch'
    _description = 'Daily Branch Report'

    def _get_report_values(self, docids, data=None):
        data = data or {}
        configs_data = data.get('configs_data', [])
        report_date = data.get('date', '')

        # Parse date range (passed from wizard, already in UTC)
        date_start_utc = datetime.strptime(data['date_start_utc'], '%Y-%m-%d %H:%M:%S') \
            if data.get('date_start_utc') else None
        date_end_utc = datetime.strptime(data['date_end_utc'], '%Y-%m-%d %H:%M:%S') \
            if data.get('date_end_utc') else None

        branches = []
        for idx, item in enumerate(configs_data, 1):
            name = item['config_name']
            if item['session_id']:
                session = self.env['pos.session'].sudo().browse(item['session_id'])
                opening = session.cash_register_balance_start

                # Filter orders to the selected date range only
                valid_orders = session.order_ids.filtered(
                    lambda o: o.state != 'cancel'
                    and (date_start_utc is None or o.date_order >= date_start_utc)
                    and (date_end_utc is None or o.date_order <= date_end_utc)
                )
                sales = sum(o.amount_total for o in valid_orders)

                # Filter expense lines to the selected date only
                stmt_lines = session.statement_line_ids
                expense_lines = stmt_lines.filtered(
                    lambda l: l.amount < 0
                    and (date_start_utc is None or l.date >= date_start_utc.date())
                    and (date_end_utc is None or l.date <= date_end_utc.date())
                )
                expenses = abs(sum(expense_lines.mapped('amount')))
            else:
                opening = sales = expenses = 0.0

            net_daily = sales - expenses
            closing = opening + net_daily

            branches.append({
                'seq': idx,
                'name': name,
                'opening': opening,
                'sales': sales,
                'expenses': expenses,
                'net_daily': net_daily,
                'closing': closing,
                'no_session': not item['session_id'],
            })

        total = {
            'opening': sum(b['opening'] for b in branches),
            'sales': sum(b['sales'] for b in branches),
            'expenses': sum(b['expenses'] for b in branches),
            'net_daily': sum(b['net_daily'] for b in branches),
            'closing': sum(b['closing'] for b in branches),
        }

        pie_svg = self._build_pie_svg(branches)
        currency = self.env['res.currency'].search([('name', '=', 'EGP')], limit=1)
        return {
            'date': report_date,
            'branches': branches,
            'total': total,
            'pie_svg': pie_svg,
            'currency': currency,
        }

    def _build_pie_svg(self, branches):
        positive = [(b['name'], b['closing']) for b in branches if b['closing'] > 0]
        if not positive:
            return ''
        total = sum(v for _, v in positive)
        if total == 0:
            return ''

        COLORS = [
            '#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f',
            '#edc948', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac',
            '#d4a6c8', '#86bcb6', '#f1ce63', '#499894', '#e8a6a1',
            '#79706e', '#d37295', '#fabfd2', '#b6992d', '#6b6ecf',
            '#8ca252', '#b5cf6b', '#cedb9c', '#8c6d31', '#bd9e39',
        ]

        cx, cy, r = 200, 200, 160
        svg_parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">']
        angle = -math.pi / 2

        for i, (name, val) in enumerate(positive):
            sweep = 2 * math.pi * val / total
            x1 = cx + r * math.cos(angle)
            y1 = cy + r * math.sin(angle)
            x2 = cx + r * math.cos(angle + sweep)
            y2 = cy + r * math.sin(angle + sweep)
            large = 1 if sweep > math.pi else 0
            color = COLORS[i % len(COLORS)]
            svg_parts.append(
                f'<path d="M {cx},{cy} L {x1:.2f},{y1:.2f} A {r},{r} 0 {large},1 {x2:.2f},{y2:.2f} Z" '
                f'fill="{color}" stroke="white" stroke-width="1"/>'
            )
            angle += sweep

        svg_parts.append('</svg>')
        return ''.join(svg_parts)
