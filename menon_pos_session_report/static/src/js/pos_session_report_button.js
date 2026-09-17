/** @odoo-module */

import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { patch } from "@web/core/utils/patch";

patch(Navbar.prototype, {
    async printSessionReport() {
        const sessionId = this.pos.session.id;
        const url = `/report/pdf/menon_pos_session_report.report_pos_session_sales/${sessionId}`;
        window.open(url, "_blank");
    },
});
