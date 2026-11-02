from decimal import Decimal
from collections.abc import Mapping
from django import template

register = template.Library()


@register.filter
def quantity(value):
    amount = Decimal(str(value["quantity"] if isinstance(value, Mapping) else value.quantity))
    unit = value["unit"] if isinstance(value, Mapping) else value.unit
    number = format(amount, "f")
    if "." in number:
        number = number.rstrip("0").rstrip(".")
    labels = {"pcs": ("piece", "pieces"), "pack": ("pack", "packs"), "bunch": ("bunch", "bunches")}
    singular, plural = labels.get(unit, (unit, unit))
    label = singular if amount == 1 else plural
    if unit == "l":
        label = "L"
    return f"{number} {label}"
