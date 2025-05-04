# Copyright (c) 2024, Bantoo and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions


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
		dimensions = get_accounting_dimensions()
		
		# check for duplicates
		
		if frappe.db.exists({'doctype': 'Journal Entry', 'bill_no': self.name}):
			frappe.throw(
				title="Error",
				msg="Journal Entry {} already exists.".format(self.name)
			)


		accounts = []

		account_credit_temp = {  
			'credit_in_account_currency': float(self.amount),
			'user_remark': str(self.remarks),
			'account': self.account_from
		}

		for dimension in dimensions:
			if hasattr(self, dimension + "_from"):
				value = getattr(self, dimension + "_from")
				if value:
					account_credit_temp[dimension] = value


		accounts.append(account_credit_temp)

		account_debit_temp = {  
			'debit_in_account_currency': float(self.amount),
			'user_remark': str(self.remarks),
			'account': self.account_to
		}

		for dimension in dimensions:
			if hasattr(self, dimension + "_to"):
				value = getattr(self, dimension + "_to")
				if value:
					account_debit_temp[dimension] = value


		accounts.append(account_debit_temp)

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