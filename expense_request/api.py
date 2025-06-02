import frappe
from frappe import _
from frappe import utils
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions

"""
TODO

Permissions 
- Settings Checbox - Employee can create Expenses
- Add Employee User Permission
Report

More Features - v2
- Alert Approvers - manual - for pending / draft
- Tax Templates
- Separate Request Document
   - Add approved amount on expense entry - auto filled from requested amount but changeable
- Rename App. Expense Voucher vs Expense Entry
- Tests

- Fix
    - Prevent Making JE's before submission / non-approvers

- Add dependant fields
    - Workflow entries
    - JV type: Expense Entry
    - JV Account Reference Type: Expense Entry
    - Mode of Payment: Petty Cash


DONE
  - Issues Fixed
    - Wire Transfer requires reference date, and minor improvements
    - Approver field vanishing
  
  - Print Format improvements - (Not done: Add signatures)
  - Prevent duplicate entry - done
  - Workflow: Pending Approval, Approved (set-approved by)
  - Creation of JV
  - expense refs
  - Roles:
    - Expense Approver
  - Set authorising party

  Add sections to EE and EE Items
    Section: Accounting Dimensions
    - Project
    - Cost Center

  - Add settings fields to Accounts Settings
    Section: Expense Settings
    - Link: Default Payment Account (Link: Mode of Payment) 
      - Desc: Create a Mode of Payment for expenses and link it to your usual expenditure account like Petty Cash
    - Checkbox: Notify all Approvers
      - Desc: when a expense request is made
    - Checkbox: Create Journals Automatically

Add all the fixtures to the app so that it is fully portable
a. Workflows
b. Accounts Settings Fields
c. Fix minor issues
   - Cant set custom print format as default - without customisation

Enhancements
- Added Cost Center Filters
"""


def setup(expense_entry, method):
    # add expenses up and set the total field
    # add default project and cost center to expense items

    total = 0
    count = 0
    expense_items = []

    
    for detail in expense_entry.expenses:
        total += float(detail.amount)        
        count += 1
        
        if not detail.project and expense_entry.default_project:
            detail.project = expense_entry.default_project
        
        if not detail.cost_center and expense_entry.default_cost_center:
            detail.cost_center = expense_entry.default_cost_center

        dimensions = get_accounting_dimensions()
        for dimension in dimensions:
            if hasattr(detail, dimension):
                setattr(detail, dimension, getattr(detail, dimension))

        expense_items.append(detail)

    expense_entry.expenses = expense_items

    expense_entry.total = total
    expense_entry.quantity = count

    make_journal_entry(expense_entry)

    


@frappe.whitelist()
def initialise_journal_entry(expense_entry_name):
    # make JE from javascript form Make JE button

    make_journal_entry(
        frappe.get_doc('Expense Entry', expense_entry_name)
    )

def make_journal_entry(expense_entry):
    if expense_entry.status == "Approved":         

        # check for duplicates
        
        if frappe.db.exists({'doctype': 'Journal Entry', 'bill_no': expense_entry.name}):
            frappe.throw(
                title="Error",
                msg="Journal Entry {} already exists.".format(expense_entry.name)
            )


        # Preparing the JE: convert expense_entry details into je account details

        accounts = []

        dimensions = get_accounting_dimensions()  # Ambil sekali saja!

        for detail in expense_entry.expenses:
            account_data = {  
                'debit_in_account_currency': float(detail.amount),
                'user_remark': str(detail.description),
                'account': detail.expense_account,
                'project': detail.project,
                'cost_center': detail.cost_center
            }

            # Tambahkan dimension field satu-satu
            for dimension in dimensions:
                if hasattr(detail, dimension):
                    account_data[dimension] = getattr(detail, dimension)

            accounts.append(account_data)

        # finally add the payment account detail

        pay_account = ""

        if (expense_entry.mode_of_payment != "Cash" and (not 
            expense_entry.payment_reference or not expense_entry.clearance_date)):
            frappe.throw(
                title="Enter Payment Reference",
                msg="Payment Reference and Date are Required for all non-cash payments."
            )
        else:
            expense_entry.clearance_date = ""
            expense_entry.payment_reference = ""

        if expense_entry.account_paid_from:
            pay_account = expense_entry.account_paid_from
        else:
            pay_account = frappe.db.get_value('Mode of Payment Account', {'parent' : expense_entry.mode_of_payment, 'company' : expense_entry.company}, 'default_account')


        pay_account = frappe.db.get_value('Mode of Payment Account', {'parent' : expense_entry.mode_of_payment, 'company' : expense_entry.company}, 'default_account')
        if not pay_account or pay_account == "":
            frappe.throw(
                title="Error",
                msg="The selected Mode of Payment has no linked account."
            )

        # buat payment account data dulu
        account_temp = {
            'credit_in_account_currency': float(expense_entry.total),
            'user_remark': str(detail.description),
            'account': pay_account,
            'cost_center': expense_entry.default_cost_center
        }

        # tambahkan dimension fields ke account_temp
        for dimension in dimensions:
            if hasattr(expense_entry, dimension):
                value = getattr(expense_entry, dimension)
                if value:
                    account_temp[dimension] = value

        # setelah lengkap, baru append ke accounts
        accounts.append(account_temp)


        # create the journal entry
        je = frappe.get_doc({
            'title': expense_entry.name,
            'doctype': 'Journal Entry',
            'voucher_type': 'Journal Entry',
            'posting_date': expense_entry.posting_date,
            'company': expense_entry.company,
            'accounts': accounts,
            'user_remark': expense_entry.remarks,
            'mode_of_payment': expense_entry.mode_of_payment,
            'cheque_date': expense_entry.clearance_date,
            'reference_date': expense_entry.clearance_date,
            'cheque_no': expense_entry.payment_reference,
            'pay_to_recd_from': expense_entry.payment_to,
            'bill_no': expense_entry.name
        })

        user = frappe.get_doc("User", frappe.session.user)

        full_name = str(user.first_name) + ' ' + str(user.last_name)
        expense_entry.db_set('approved_by', full_name)
        

        je.insert()
        je.submit()

def create_accounting_dimension(doc, method):
    create_accounting_dimension_for_expense_entry(doc, method)
    create_accounting_dimension_for_fund_transfer(doc, method)

def delete_accounting_dimension(doc, method):
    if method == "on_trash":
        cf = frappe.db.exists("Custom Field", {"dt": "Expense Entry Item", "fieldname": doc.get("fieldname")})
        if cf:
            frappe.delete_doc("Custom Field", cf)
        
        cf = frappe.db.exists("Custom Field", {"dt": "Expense Entry", "fieldname": doc.get("fieldname")})
        if cf:
            frappe.delete_doc("Custom Field", cf)

        frappe.clear_cache(doctype="Expense Entry")
        frappe.clear_cache(doctype="Expense Entry Item")


def create_accounting_dimension_for_expense_entry(doc, method):
    if method == "on_update":
        cf = frappe.db.exists("Custom Field", {"dt": "Expense Entry Item", "fieldname": doc.get("fieldname")})
        if not cf:
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Expense Entry Item"
            custom_field.fieldname = doc.get("fieldname")
            custom_field.label = doc.get("label")
            custom_field.fieldtype = "Link"
            custom_field.options = doc.get("name")
            custom_field.insert_after = "cost_center"
            custom_field.allow_on_submit = 1
            custom_field.in_list_view = 1
            custom_field.reqd = 1
            custom_field.insert()
        
        cf = frappe.db.exists("Custom Field", {"dt": "Expense Entry", "fieldname": doc.get("fieldname")})
        if not cf:
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Expense Entry"
            custom_field.fieldname = doc.get("fieldname")
            custom_field.label = doc.get("label")
            custom_field.fieldtype = "Link"
            custom_field.options = doc.get("name")
            custom_field.insert_after = "mode_of_payment"
            custom_field.allow_on_submit = 1
            custom_field.in_list_view = 1
            custom_field.reqd = 1
            custom_field.insert()

        frappe.clear_cache(doctype="Expense Entry")

def create_accounting_dimension_for_fund_transfer(doc, method):
    if method == "on_update":
        cf = frappe.db.exists("Custom Field", {"dt": "Fund Transfer", "fieldname": doc.get("fieldname") + "_from"})
        if not cf:
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Fund Transfer"
            custom_field.fieldname = doc.get("fieldname") + "_from"
            custom_field.label = doc.get("label") + " From"
            custom_field.fieldtype = "Link"
            custom_field.options = doc.get("name")
            custom_field.insert_after = "account_from"
            custom_field.reqd = 1
            custom_field.insert()
        
        cf = frappe.db.exists("Custom Field", {"dt": "Fund Transfer", "fieldname": doc.get("fieldname") + "_to"})
        if not cf:
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Fund Transfer"
            custom_field.fieldname = doc.get("fieldname") + "_to"
            custom_field.label = doc.get("label") + " To"
            custom_field.fieldtype = "Link"
            custom_field.options = doc.get("name")
            custom_field.insert_after = "account_to"
            custom_field.reqd = 1
            custom_field.insert()
        frappe.clear_cache(doctype="Fund Transfer")