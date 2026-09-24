# -*- coding: utf-8 -*-
from datetime import datetime, time
import pytz
from odoo import models, fields, api


class DailyBranchSummaryLine(models.TransientModel):
    _name = 'daily.branch.summary.line'
    _description = 'Daily Branch Summary Line'
    _order = 'seq asc'

    wizard_id = fields.Many2one('daily.branch.report.wizard', ondelete='cascade')
    seq = fields.Integer(string='#')
    name = fields.Char(string='الفرع')
    opening = fields.Float(string='الرصيد الافتتاحي', digits=(16, 2))
    sales = fields.Float(string='المبيعات', digits=(16, 2))
    expenses = fields.Float(string='المصروفات', digits=(16, 2))
    net_daily = fields.Float(string='صافي رصيد اليوم', digits=(16, 2))
    closing = fields.Float(string='الرصيد الختامي', digits=(16, 2))
    no_session = fields.Boolean()


class DailyBranchReportWizard(models.TransientModel):
    _name = 'daily.branch.report.wizard'
    _description = 'Daily Branch Report Wizard'

    report_date = fields.Date(string='التاريخ', required=True, default=fields.Date.today)
    line_ids = fields.One2many('daily.branch.summary.line', 'wizard_id', string='الفروع')
    total_opening = fields.Float(compute='_compute_totals', digits=(16, 2))
    total_sales = fields.Float(compute='_compute_totals', digits=(16, 2))
    total_expenses = fields.Float(compute='_compute_totals', digits=(16, 2))
    total_net = fields.Float(compute='_compute_totals', digits=(16, 2))
    total_closing = fields.Float(compute='_compute_totals', digits=(16, 2))

    @api.depends('line_ids')
    def _compute_totals(self):
        for rec in self:
            rec.total_opening = sum(rec.line_ids.mapped('opening'))
            rec.total_sales = sum(rec.line_ids.mapped('sales'))
            rec.total_expenses = sum(rec.line_ids.mapped('expenses'))
            rec.total_net = sum(rec.line_ids.mapped('net_daily'))
            rec.total_closing = sum(rec.line_ids.mapped('closing'))

    def _get_date_range_utc(self):
        """Return (date_start_utc, date_end_utc) for the selected report_date."""
        tz_name = self.env.user.tz or 'UTC'
        user_tz = pytz.timezone(tz_name)
        date_start_local = datetime.combine(self.report_date, time.min)
        date_end_local = datetime.combine(self.report_date, time.max)
        date_start_utc = user_tz.localize(date_start_local).astimezone(pytz.utc).replace(tzinfo=None)
        date_end_utc = user_tz.localize(date_end_local).astimezone(pytz.utc).replace(tzinfo=None)
        return date_start_utc, date_end_utc

    def _get_configs_data(self):
        """
        Build configs_data list.

        Session matching logic:
        - Find sessions whose start_at falls within the selected date (local time → UTC).
        - If a config has multiple sessions that day, take the one that started latest.
        - Passes date_start_utc / date_end_utc so the report can filter orders/expenses
          to only those that occurred on the selected day.
        """
        date_start_utc, date_end_utc = self._get_date_range_utc()

        all_configs = self.env['pos.config'].search([], order='name asc')

        # Sessions overlapping with the selected date
        # (started before end of day AND still open or closed after start of day)
        overlapping = self.env['pos.session'].search([
            ('start_at', '<=', date_end_utc),
            '|',
            ('stop_at', '=', False),
            ('stop_at', '>=', date_start_utc),
        ])

        # For each config pick the session whose start_at is CLOSEST to (but not after)
        # the end of the selected date → i.e. the latest-starting session that was active
        # on that day.  Sorting ascending then overwriting means the latest wins.
        session_by_config = {}
        for s in overlapping.sorted('start_at'):
            session_by_config[s.config_id.id] = s

        configs_data = []
        for cfg in all_configs:
            session = session_by_config.get(cfg.id)
            configs_data.append({
                'config_id': cfg.id,
                'config_name': cfg.name,
                'session_id': session.id if session else False,
            })
        return configs_data, date_start_utc, date_end_utc

    def _compute_branch_rows(self, configs_data, date_start_utc, date_end_utc):
        """Compute branch rows, filtering orders and expense lines to the selected date."""
        branches = []
        for idx, item in enumerate(configs_data, 1):
            name = item['config_name']
            if item['session_id']:
                session = self.env['pos.session'].sudo().browse(item['session_id'])
                opening = session.cash_register_balance_start

                # Filter orders to those placed on the selected date
                valid_orders = session.order_ids.filtered(
                    lambda o: o.state != 'cancel'
                    and o.date_order >= date_start_utc
                    and o.date_order <= date_end_utc
                )
                sales = sum(o.amount_total for o in valid_orders)

                # Filter expense lines to those dated on the selected date
                stmt_lines = session.statement_line_ids
                expense_lines = stmt_lines.filtered(
                    lambda l: l.amount < 0
                    and l.date >= date_start_utc.date()
                    and l.date <= date_end_utc.date()
                )
                expenses = abs(sum(expense_lines.mapped('amount')))
                no_session = False
            else:
                opening = sales = expenses = 0.0
                no_session = True

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
                'no_session': no_session,
            })
        return branches

    def action_compute(self):
        self.ensure_one()
        self.line_ids.unlink()

        configs_data, date_start_utc, date_end_utc = self._get_configs_data()
        branches = self._compute_branch_rows(configs_data, date_start_utc, date_end_utc)

        lines = []
        for b in branches:
            lines.append({
                'wizard_id': self.id,
                'seq': b['seq'],
                'name': b['name'],
                'opening': b['opening'],
                'sales': b['sales'],
                'expenses': b['expenses'],
                'net_daily': b['net_daily'],
                'closing': b['closing'],
                'no_session': b['no_session'],
            })
        self.env['daily.branch.summary.line'].create(lines)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'daily.branch.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_print(self):
        self.ensure_one()
        configs_data, date_start_utc, date_end_utc = self._get_configs_data()
        return self.env.ref('ifruit_daily_branch_report.action_report_daily_branch').report_action(
            None,
            data={
                'configs_data': configs_data,
                'date': str(self.report_date),
                'date_start_utc': str(date_start_utc),
                'date_end_utc': str(date_end_utc),
            },
        )
