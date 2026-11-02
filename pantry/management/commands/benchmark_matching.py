import json
import platform
import statistics
from decimal import Decimal
from time import perf_counter
from types import SimpleNamespace

from django.core.management.base import BaseCommand, CommandError

from pantry.matching import index_stock, match_recipe


class Command(BaseCommand):
    help = "Measure synthetic in-memory recipe matching; never inserts or changes pantry data."

    def add_arguments(self, parser):
        parser.add_argument("--recipes", type=int, default=500)
        parser.add_argument("--items", type=int, default=2000)
        parser.add_argument("--runs", type=int, default=5)

    def handle(self, *args, **options):
        recipes, batches, runs = (options[key] for key in ("recipes", "items", "runs"))
        if not (1 <= recipes <= 5000 and 1 <= batches <= 10000 and 3 <= runs <= 20):
            raise CommandError("Use 1–5000 recipes, 1–10000 items and 3–20 runs.")
        items = [
            SimpleNamespace(name=f"Food {number % 100}", quantity=Decimal(1), unit="kg")
            for number in range(batches)
        ]
        catalogue = []
        for number in range(recipes):
            ingredients = [
                SimpleNamespace(
                    name=f"Food {(number + offset) % 100}", quantity=Decimal(100), unit="g"
                )
                for offset in range(5)
            ]
            catalogue.append(
                SimpleNamespace(
                    servings=2, ingredients=SimpleNamespace(all=lambda rows=ingredients: rows)
                )
            )
        timings = {"rebuild_per_recipe_ms": [], "shared_index_ms": []}
        expected = None
        for _ in range(runs):
            for label, shared in (("rebuild_per_recipe_ms", False), ("shared_index_ms", True)):
                start = perf_counter()
                stock = index_stock(items) if shared else None
                ready = sum(
                    all(
                        row["ready"] for row in match_recipe(recipe, items=items, stock_index=stock)
                    )
                    for recipe in catalogue
                )
                timings[label].append(round((perf_counter() - start) * 1000, 3))
                if expected is not None and ready != expected:
                    raise CommandError("The indexed and non-shared results disagree.")
                expected = ready
        self.stdout.write(
            json.dumps(
                {
                    "scope": "synthetic in-memory matching, not HTTP throughput or database concurrency",
                    "python": platform.python_version(),
                    "platform": platform.platform(),
                    "recipes": recipes,
                    "items": batches,
                    "ingredients_per_recipe": 5,
                    "runs": runs,
                    "ready_recipes": expected,
                    "timings": {
                        label: {
                            "samples_ms": values,
                            "median_ms": statistics.median(values),
                            "worst_ms": max(values),
                        }
                        for label, values in timings.items()
                    },
                },
                indent=2,
            )
        )
