// Copyright (c) 2024, Bantoo and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fund Transfer", {
    onload(frm) {
        frm.set_query("account_from", () => {
            return{
				filters: {
					"account_type": [
                        "in", ["Bank", "Cash"],
                        
                    ],
                    "root_type": "Asset",
                    "is_group": "0",
                    "company": frm.doc.company
                    
				}
			}

		});
        frm.set_query("account_to", () => {
            return{
				filters: {
                    "account_type": [
                        "in", ["Bank", "Cash"],
                        
                    ],
                    "root_type": "Asset",
                    "is_group": "0",
                    "company": frm.doc.company
				}
			}

		});
	},
    company: function(frm) {
        frm.set_value("account_from", "");
        frm.set_value("account_to", "");
    }
});
