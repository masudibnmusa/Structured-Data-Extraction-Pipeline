"""Cross-field checks that schema validation alone can't catch."""
from decimal import Decimal

from app.schemas.contract_schema import Contract
from app.schemas.invoice_schema import Invoice

TOLERANCE = Decimal("0.02")


def _close(a: Decimal, b: Decimal) -> bool:
    return abs(a - b) <= TOLERANCE


def check_invoice(inv: Invoice) -> list[str]:
    issues: list[str] = []
    for i, li in enumerate(inv.line_items):
        if not _close(li.quantity * li.unit_price, li.amount):
            issues.append(f"line_items[{i}]: quantity x unit_price does not equal amount")
    line_sum = sum((li.amount for li in inv.line_items), Decimal("0"))
    if not _close(line_sum, inv.subtotal):
        issues.append(f"line items sum to {line_sum}, but subtotal is {inv.subtotal}")
    if not _close(inv.subtotal + inv.tax, inv.total):
        issues.append(f"subtotal + tax = {inv.subtotal + inv.tax}, but total is {inv.total}")
    if inv.due_date and inv.due_date < inv.invoice_date:
        issues.append("due_date is before invoice_date")
    return issues


def check_contract(c: Contract) -> list[str]:
    issues: list[str] = []
    if c.effective_date and c.end_date and c.end_date < c.effective_date:
        issues.append("end_date is before effective_date")
    if c.contract_value is not None and c.contract_value < 0:
        issues.append("contract_value is negative")
    return issues


RULES = {
    "invoice": check_invoice,
    "contract": check_contract,
    "email": lambda _: [],
}


def validate_business_rules(doc_type: str, instance) -> list[str]:
    return RULES[doc_type](instance)