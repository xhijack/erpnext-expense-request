// Copyright (c) 2020, Bantoo and contributors
// For license information, please see license.txt

frappe.provide("expense_entry.expense_entry");

function update_totals(frm, cdt, cdn){
	var items = locals[cdt][cdn];
    var total = 0;
    var quantity = 0;
    frm.doc.expenses.forEach(
        function(items) { 
            total += items.amount;
            quantity +=1;
        });
    frm.set_value("total", total);
    refresh_field("total");
    frm.set_value("quantity", quantity);
    refresh_field("quantity");
}

frappe.ui.form.on('Expense Entry Item', {
	amount: function(frm, cdt, cdn) {
        update_totals(frm, cdt, cdn);
	},
	expenses_remove: function(frm, cdt, cdn){
        update_totals(frm, cdt, cdn);
	},
    expenses_add: function(frm, cdt, cdn){
        var d = locals[cdt][cdn];
        
        if((d.cost_center === "" || typeof d.cost_center == 'undefined')) { 

            if (cur_frm.doc.default_cost_center != "" || typeof cur_frm.doc.default_cost_center != 'undefined') {
                
                d.cost_center = cur_frm.doc.default_cost_center; 
                cur_frm.refresh_field("expenses");
            }
        }
	}
	
});


frappe.ui.form.on('Expense Entry', {
    before_save: function(frm) { 

        // $.each(frm.doc.expenses, function(i, d) { 
        //     let label = "";
            
        //     if((d.cost_center === "" || typeof d.cost_center == 'undefined')) { 
                
        //         if (cur_frm.doc.default_cost_center === "" || typeof cur_frm.doc.default_cost_center == 'undefined') {
        //             frappe.validated = false;
        //             frappe.msgprint("Set a Default Cost Center or specify the Cost Center for expense <strong>number " 
        //                             + (i + 1) + "</strong>.");
        //             return false;
        //         }
        //         else {
        //             d.cost_center = cur_frm.doc.default_cost_center; 
        //         }
        //     }
        // }); 
        
    },
    refresh(frm) {
        //update total and qty when an item is added
	},
	onload(frm) {
	    //console.log("hello");

		frm.set_query("expense_account", 'expenses', () => {
			return {
				filters: [
					["Account", "root_type", "=", "Expense"],
                    ["Account", "is_group", "=", "0"]
				]
			}
		});
		frm.set_query("cost_center", 'expenses', () => {
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
        frm.set_query("account_paid_from", () => {
            return{
				filters: {
					"account_type": ["in", ["Bank", "Cash"]],
                    "company": frm.doc.company,
				}
			}

		});
	},
    mode_of_payment(frm){
        erpnext.accounts.pos.get_payment_mode_account(frm, frm.doc.mode_of_payment, function(account){
			// let payment_account_field = frm.doc.payment_type == "Receive" ? "paid_to" : "paid_from";
			frm.set_value('account_paid_from', account);
		})
    },

});
