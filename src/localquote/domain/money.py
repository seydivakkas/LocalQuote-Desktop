"""All stored amounts are integer kuruş; floating point is forbidden."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

ONE_CENT = Decimal("0.01")

class InputError(ValueError):
    pass


def decimal_value(value: str | int | Decimal, *, positive=False, max_value=Decimal("1000000000")) -> Decimal:
    if isinstance(value, (bool, float)):
        raise InputError("Kayan noktalı para/miktar değeri kabul edilmez")
    if isinstance(value, str):
        value = value.strip().replace(",", ".")
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        raise InputError("Geçersiz sayı") from None
    if not result.is_finite() or result < 0 or (positive and result <= 0) or result > max_value:
        raise InputError("Sayı aralık dışında")
    return result


def cents(value: str | int | Decimal) -> int:
    number = decimal_value(value)
    if number.as_tuple().exponent < -2:
        raise InputError("Para en fazla iki ondalık hane içerebilir")
    return int((number * 100).to_integral_exact())


def percent(value: str | int | Decimal) -> Decimal:
    return decimal_value(value, max_value=Decimal("100"))


def money(cents_value: int) -> str:
    return f"{(Decimal(cents_value)/100):.2f}"


def to_cents(value: Decimal) -> int:
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
