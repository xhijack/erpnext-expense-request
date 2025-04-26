# Copyright (c) 2024, Bantoo and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FundTransfer(Document):
	def validate(self):
		# if self.account_from == self.account_to:
		# 	frappe.throw("Account From and Account To cannot be the same")
		
		if self.amount <= 0:
			frappe.throw("Amount must be greater than zero")
		
	def on_submit(self):
		self.make_journal()

	def on_cancel(self):
		je = frappe.get_doc('Journal Entry', {'bill_no': self.name})
		je.cancel()

	def make_journal(self):
		# check for duplicates
		
		if frappe.db.exists({'doctype': 'Journal Entry', 'bill_no': self.name}):
			frappe.throw(
				title="Error",
				msg="Journal Entry {} already exists.".format(self.name)
			)


		accounts = []

		accounts.append({  
			'credit_in_account_currency': float(self.amount),
			'user_remark': str(self.remarks),
			'account': self.account_from
		})

		accounts.append({  
			'debit_in_account_currency': float(self.amount),
			'user_remark': str(self.remarks),
			'account': self.account_to
		})

		je = frappe.new_doc('Journal Entry')
		je.update({
			'title': self.title,
			'company': self.company,
			'posting_date': self.posting_date,
			'user_remark': self.remarks,
			'voucher_type': 'Journal Entry',
			'bill_no': self.name,
			'posting_date': self.posting_date,
			'accounts': accounts
		})

		je.insert()
		je.submit()