from app.schemas.invoice_schema import Invoice
from app.validation.business_rule_validator import validate_business_rules
from fakes import invoice_data


def test_consistent_invoice_has_no_issues():
    inv = Invoice.model_validate(invoice_data())
    assert validate_business_rules("invoice", inv) == []


def test_total_mismatch_is_flagged():
    inv = Invoice.model_validate(invoice_data(total=999.00))
    issues = validate_business_rules("invoice", inv)
    assert any("total" in i for i in issues)


def test_due_date_before_invoice_date_is_flagged():
    data = invoice_data()
    data["due_date"] = "2025-01-01"
    issues = validate_business_rules("invoice", Invoice.model_validate(data))
    assert any("due_date" in i for i in issues)