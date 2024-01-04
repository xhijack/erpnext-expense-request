// Copyright (c) 2024, Bantoo and contributors
// For license information, please see license.txt

frappe.ui.form.on("Income Entry", {
	onload(frm) {
        frm.set_query("income_account", 'incomes', () => {
			return {
				filters: [
					["Account", "root_type", "=", "Income"],
                    ["Account", "is_group", "=", "0"]
				]
			}
		});
		frm.set_query("cost_center", 'incomes', () => {
			return {
				filters: [
					["Cost Center", "is_group", "=", "0"]
				]
			}
		});
		frm.set_query("default_cost_center", () => {
			return {
				filters: [
					["Cost Center", "is_group", "=", "0"]
				]
			}
		});
        frm.set_query("account_deposit_to", () => {
            return{
				filters: {
					"account_type": ["in", ["Bank", "Cash"]],
				}
			}

		});
	},
    mode_of_payment(frm){
        erpnext.accounts.pos.get_payment_mode_account(frm, frm.doc.mode_of_payment, function(account){
			// let payment_account_field = frm.doc.payment_type == "Receive" ? "paid_to" : "paid_from";
			frm.set_value('account_deposit_to', account);
		})
    }
    
});
