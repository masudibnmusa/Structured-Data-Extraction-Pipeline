from app.schemas.invoice_schema import Invoice
from app.validation.schema_validator import validate_schema
from fakes import invoice_data


def test_valid_invoice_passes_and_currency_is_uppercased():
    inst, errors = validate_schema(Invoice, invoice_data())
    assert errors == []
    assert inst.currency == "USD"


def test_missing_required_field_reports_error():
    data = invoice_data()
    del data["vendor_name"]
    inst, errors = validate_schema(Invoice, data)
    assert inst is None
    assert any("vendor_name" in e for e in errors)


def test_bad_date_reports_error():
    data = invoice_data()
    data["invoice_date"] = "not-a-date"
    _, errors = validate_schema(Invoice, data)
    assert any("invoice_date" in e for e in errors)