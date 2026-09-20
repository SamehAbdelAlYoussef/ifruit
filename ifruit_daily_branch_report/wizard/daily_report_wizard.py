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

    def _get_configs_data(self):
        tz_name = self.env.user.tz or 'UTC'
        user_tz = pytz.timezone(tz_name)
        date_start_local = datetime.combine(self.report_date, time.min)
        date_end_local = datetime.combine(self.report_date, time.max)
        date_start_utc = user_tz.localize(date_start_local).astimezone(pytz.utc).replace(tzinfo=None)
        date_end_utc = user_tz.localize(date_end_local).astimezone(pytz.utc).replace(tzinfo=None)

        all_configs = self.env['pos.config'].search([], order='name asc')
        active_sessions = self.env['pos.session'].search([
            ('start_at', '<=', date_end_utc),
            '|',
            ('stop_at', '=', False),
            ('stop_at', '>=', date_start_utc),
        ])
        session_by_config = {s.config_id.id: s for s in active_sessions}

        configs_data = []
        for cfg in all_configs:
            session = session_by_config.get(cfg.id)
            configs_data.append({
                'config_id': cfg.id,
                'config_name': cfg.name,
                'session_id': session.id if session else False,
            })
        return configs_data

    def action_compute(self):
        self.ensure_one()
        self.line_ids.unlink()

        configs_data = self._get_configs_data()
        lines = []
        for idx, item in enumerate(configs_data, 1):
            name = item['config_name']
            if item['session_id']:
                session = self.env['pos.session'].sudo().browse(item['session_id'])
                opening = session.cash_register_balance_start
                valid_orders = session.order_ids.filtered(lambda o: o.state != 'cancel')
                sales = sum(o.amount_total for o in valid_orders)
                stmt_lines = session.statement_line_ids
                expense_lines = stmt_lines.filtered(lambda l: l.amount < 0)
                expenses = abs(sum(expense_lines.mapped('amount')))
                no_session = False
            else:
                opening = sales = expenses = 0.0
                no_session = True

            net_daily = sales - expenses
            closing = opening + net_daily
            lines.append({
                'wizard_id': self.id,
                'seq': idx,
                'name': name,
                'opening': opening,
                'sales': sales,
                'expenses': expenses,
                'net_daily': net_daily,
                'closing': closing,
                'no_session': no_session,
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
        configs_data = self._get_configs_data()
        return self.env.ref('ifruit_daily_branch_report.action_report_daily_branch').report_action(
            None,
            data={
                'configs_data': configs_data,
                'date': str(self.report_date),
            },
        )
