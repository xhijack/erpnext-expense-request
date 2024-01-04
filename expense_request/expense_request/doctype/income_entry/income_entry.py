# Copyright (c) 2024, Bantoo and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IncomeEntry(Document):
	
	def validate(self):
		self.validate_income_entry()
	
	def on_submit(self):
		self.make_journal()

	def on_cancel(self):
		je = frappe.get_doc('Journal Entry', {'bill_no': self.name})
		je.cancel()

	def validate_income_entry(self):
		total = 0
		qty = 0
		income_items = []
		for income in self.incomes:
			total += float(income.amount)        
			qty += 1
			
			if not income.project and self.default_project:
				income.project = self.default_project
			
			if not income.cost_center and self.default_cost_center:
				income.cost_center = self.default_cost_center

			income_items.append(income)

		self.incomes = income_items

		self.total = total
		self.qty = qty
	
	def make_journal(self):
		# check for duplicates
		
		if frappe.db.exists({'doctype': 'Journal Entry', 'bill_no': self.name}):
			frappe.throw(
				title="Error",
				msg="Journal Entry {} already exists.".format(self.name)
			)


		# Preparing the JE: convert expense_entry details into je account details

		accounts = []

		for detail in self.incomes:            

			accounts.append({  
				'credit_in_account_currency': float(detail.amount),
				'user_remark': str(detail.description),
				'account': detail.income_account,
				'project': detail.project,
				'cost_center': detail.cost_center
			})

		# finally add the payment account detail

		paid_account = ""

		# if (self.mode_of_payment != "Cash" and (not 
		# 	expense_entry.payment_reference or not expense_entry.clearance_date)):
		# 	frappe.throw(
		# 		title="Enter Payment Reference",
		# 		msg="Payment Reference and Date are Required for all non-cash payments."
		# 	)
		# else:
		# 	expense_entry.clearance_date = ""
		# 	expense_entry.payment_reference = ""


		paid_account = frappe.db.get_value('Mode of Payment Account', {'parent' : self.mode_of_payment, 'company' : self.company}, 'default_account')
		if not paid_account or paid_account == "":
			frappe.throw(
				title="Error",
				msg="The selected Mode of Payment has no linked account."
			)

		accounts.append({  
			'debit_in_account_currency': float(self.total),
			'user_remark': str(self.remarks),
			'account': paid_account,
			'cost_center': self.default_cost_center
		})

		# create the journal entry
		je = frappe.get_doc({
			'title': self.title,
			'doctype': 'Journal Entry',
			'voucher_type': 'Journal Entry',
			'posting_date': self.posting_date,
			'company': self.company,
			'accounts': accounts,
			'user_remark': self.remarks,
			'mode_of_payment': self.mode_of_payment,
			# 'cheque_date': expense_entry.clearance_date,
			# 'reference_date': expense_entry.clearance_date,
			# 'cheque_no': expense_entry.payment_reference,
			# 'pay_to_recd_from': expense_entry.payment_to,
			'bill_no': self.name
		})

		user = frappe.get_doc("User", frappe.session.user)

		# full_name = str(user.first_name) + ' ' + str(user.last_name)
		# expense_entry.db_set('approved_by', full_name)
		

		je.insert()
		je.submit()