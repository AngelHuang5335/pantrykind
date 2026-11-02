from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

MAX_QUANTITY = Decimal("999999999")


def positive_quantity(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError("Enter a valid quantity.") from None
    if not result.is_finite() or not 0 < result <= MAX_QUANTITY or result.as_tuple().exponent < -3:
        raise ValidationError("Quantity must be positive with at most three decimal places.")
    return result
