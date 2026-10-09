"""Per-line rounding: quantity*unit -> discount -> taxable -> VAT."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from .money import InputError, decimal_value, percent, to_cents

@dataclass(frozen=True)
class PriceLine:
    description: str
    quantity: str
    unit_price_cents: int
    discount_percent: str
    vat_percent: str

@dataclass(frozen=True)
class LineTotal:
    gross_cents: int
    discount_cents: int
    net_cents: int
    vat_cents: int
    total_cents: int


def calculate_line(line: PriceLine) -> LineTotal:
    if not line.description or not line.description.strip():
        raise InputError("Açıklama zorunlu")
    if not isinstance(line.unit_price_cents, int) or isinstance(line.unit_price_cents, bool) or line.unit_price_cents < 0:
        raise InputError("Geçersiz birim fiyat")
    quantity = decimal_value(line.quantity, positive=True, max_value=Decimal("1000000"))
    discount = percent(line.discount_percent)
    vat = percent(line.vat_percent)
    gross = to_cents(quantity * Decimal(line.unit_price_cents) / 100)
    reduction = to_cents(Decimal(gross) / 100 * discount / 100)
    net = gross - reduction
    tax = to_cents(Decimal(net) / 100 * vat / 100)
    return LineTotal(gross, reduction, net, tax, net + tax)


def calculate_quote(lines: list[PriceLine]) -> dict[str,int]:
    results = [calculate_line(x) for x in lines]
    return {key: sum(getattr(row, key) for row in results) for key in (
        "gross_cents", "discount_cents", "net_cents", "vat_cents", "total_cents"
    )}
