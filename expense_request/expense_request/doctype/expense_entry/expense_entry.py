# -*- coding: utf-8 -*-
# Copyright (c) 2020, Bantoo and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
import frappe
from frappe.model.document import Document

class ExpenseEntry(Document):
	def before_cancel(self):
		journal_entry = frappe.db.get_value("Journal Entry", {"bill_no": self.name})
		if journal_entry:
			journal_entry_doc = frappe.get_doc("Journal Entry", journal_entry)
			if journal_entry_doc.docstatus == 1:
				journal_entry_doc.cancel()
		self.status = "cancelled"
		frappe.db.commit()