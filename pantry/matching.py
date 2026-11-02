from decimal import Decimal
from django.db.models import Q, F
from django.utils import timezone
from pantry.models import Item
from pantry.normalization import food_key
from zoneinfo import ZoneInfo

UNIT_BASE = {
    "g": ("mass", Decimal("1")),
    "kg": ("mass", Decimal("1000")),
    "ml": ("volume", Decimal("1")),
    "l": ("volume", Decimal("1000")),
}


def measure(unit):
    return UNIT_BASE.get(unit, (unit, Decimal("1")))


def index_stock(items):
    """Build once for a recipe catalogue; preserve FEFO order within each food/unit family."""
    index = {}
    for item in items:
        family, multiplier = measure(item.unit)
        key = (food_key(item.name), family)
        group = index.setdefault(key, {"have_base": Decimal(0), "batches": []})
        group["have_base"] += item.quantity * multiplier
        group["batches"].append((item, multiplier))
    return index


def match_recipe(recipe, servings=None, items=None, stock_index=None):
    factor = Decimal(str(servings or recipe.servings)) / recipe.servings
    if items is None and stock_index is None:
        today = timezone.localdate(timezone=ZoneInfo(recipe.household.timezone_name))
        items = list(
            Item.objects.filter(household=recipe.household, archived=False, quantity__gt=0)
            .filter(Q(expiry_date__isnull=True) | Q(expiry_date__gte=today))
            .order_by(F("expiry_date").asc(nulls_last=True), "pk")
        )
    if stock_index is None:
        stock_index = index_stock(items)
    required = {}
    for ingredient in recipe.ingredients.all():
        family, multiplier = measure(ingredient.unit)
        key = (food_key(ingredient.name), family)
        if key not in required:
            required[key] = {
                "name": ingredient.name,
                "unit": ingredient.unit,
                "factor": multiplier,
                "need_base": Decimal(0),
                "batches": [],
                "have_base": Decimal(0),
            }
        required[key]["need_base"] += ingredient.quantity * multiplier * factor
    for key, value in required.items():
        if key in stock_index:
            value["have_base"] = stock_index[key]["have_base"]
            value["batches"] = list(stock_index[key]["batches"])
    result = []
    for value in required.values():
        value["needed"] = value["need_base"] / value["factor"]
        value["available"] = value["have_base"] / value["factor"]
        value["missing"] = (
            max(value["need_base"] - value["have_base"], Decimal(0)) / value["factor"]
        )
        value["ready"] = value["missing"] == 0
        result.append(value)
    return result
