from types import SimpleNamespace
from decimal import Decimal
from django.test import SimpleTestCase
from pantry.templatetags.pantry_tags import quantity


class QuantityDisplayTests(SimpleTestCase):
    def test_human_units_and_decimal_precision(self):
        for amount, unit, expected in [
            ("1.000", "bunch", "1 bunch"),
            ("2", "pack", "2 packs"),
            ("500", "g", "500 g"),
            ("0.125", "kg", "0.125 kg"),
            ("1", "l", "1 L"),
        ]:
            self.assertEqual(
                quantity(SimpleNamespace(quantity=Decimal(amount), unit=unit)), expected
            )
