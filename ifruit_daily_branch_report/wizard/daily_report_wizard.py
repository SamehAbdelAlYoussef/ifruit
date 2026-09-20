# -*- coding: utf-8 -*-
from datetime import datetime, time
import pytz
from odoo import models, fields


class DailyBranchReportWizard(models.TransientModel):
    _name = 'daily.branch.report.wizard'
    _description = 'Daily Branch Report Wizard'

    report_date = fields.Date(string='التاريخ', required=True, default=fields.Date.today)

    def action_print(self):
        self.ensure_one()
        tz_name = self.env.user.tz or 'UTC'
        user_tz = pytz.timezone(tz_name)
        date_start_local = datetime.combine(self.report_date, time.min)
        date_end_local = datetime.combine(self.report_date, time.max)
        date_start_utc = user_tz.localize(date_start_local).astimezone(pytz.utc).replace(tzinfo=None)
        date_end_utc = user_tz.localize(date_end_local).astimezone(pytz.utc).replace(tzinfo=None)

        # All active POS configs
        all_configs = self.env['pos.config'].search([], order='name asc')

        # Sessions active on the selected date per config
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

        return self.env.ref('ifruit_daily_branch_report.action_report_daily_branch').report_action(
            None,
            data={
                'configs_data': configs_data,
                'date': str(self.report_date),
            },
        )
