import getpass, secrets
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from pantry.models import (
    Household,
    Membership,
    Item,
    ShoppingEntry,
    Recipe,
    Ingredient,
    MealPlan,
)


class Command(BaseCommand):
    help = (
        "Create a separate demo household with original sample recipes; never clears existing data."
    )

    def add_arguments(self, p):
        p.add_argument("--username", default="demo")
        p.add_argument("--password")
        p.add_argument("--noinput", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]
        if User.objects.filter(username=username).exists():
            raise CommandError(
                "That username already exists; choose another. Existing data was not changed."
            )
        password = options["password"] or (
            secrets.token_urlsafe(18)
            if options["noinput"]
            else getpass.getpass("Choose a demo password: ")
        )
        from django.contrib.auth.password_validation import validate_password

        try:
            validate_password(password)
        except Exception as error:
            raise CommandError(str(error))
        user = User.objects.create_user(username, password=password)
        home = Household.objects.create(name="The Sunday Kitchen")
        Membership.objects.create(household=home, user=user, role="owner")
        today = timezone.localdate()
        samples = [
            ("Fresh spinach", "produce", "fridge", "1", "bunch", 2),
            ("Cherry tomatoes", "produce", "fridge", "400", "g", 3),
            ("Brown rice", "grains", "pantry", "1.2", "kg", 90),
            ("Chickpeas", "protein", "pantry", "2", "pack", 120),
            ("Rolled oats", "grains", "pantry", "500", "g", 60),
            ("Milk", "dairy", "fridge", "1", "l", 4),
            ("Sweet potatoes", "produce", "pantry", "4", "pcs", 12),
            ("Eggs", "dairy", "fridge", "6", "pcs", 9),
            ("Olive oil", "other", "pantry", "250", "ml", 180),
        ]
        for name, category, location, quantity, unit, days in samples:
            Item.objects.create(
                household=home,
                name=name,
                category=category,
                location=location,
                quantity=Decimal(quantity),
                unit=unit,
                expiry_date=today + timedelta(days=days),
                low_stock_at=Decimal("100") if unit == "g" else 0,
            )
        recipes = [
            (
                "Sunshine rice bowl",
                "A bright, simple bowl for a quieter evening.",
                25,
                2,
                [
                    ("Brown rice", 200, "g"),
                    ("Cherry tomatoes", 200, "g"),
                    ("Fresh spinach", 1, "bunch"),
                    ("Olive oil", 15, "ml"),
                ],
                "Cook the rice according to its packaging. Warm the oil in a pan, soften the tomatoes, and fold in the spinach until wilted. Serve over the rice.",
            ),
            (
                "Everyday oat porridge",
                "A warm start with two pantry staples.",
                10,
                2,
                [("Rolled oats", 100, "g"), ("Milk", 300, "ml")],
                "Combine oats and milk in a saucepan. Simmer gently, stirring until thickened. Add a little water if needed. Serve warm.",
            ),
            (
                "Roasted sweet potato & chickpeas",
                "A flexible tray for using a few good things.",
                40,
                2,
                [
                    ("Sweet potatoes", 2, "pcs"),
                    ("Chickpeas", 1, "pack"),
                    ("Olive oil", 20, "ml"),
                ],
                "Heat the oven to 200°C. Rinse and drain the chickpeas. Cut the sweet potatoes into bite-size pieces. Toss everything with oil and roast until the sweet potato is tender, turning halfway through.",
            ),
        ]
        saved = []
        for title, description, minutes, servings, ingredients, instructions in recipes:
            recipe = Recipe.objects.create(
                household=home,
                title=title,
                description=description,
                minutes=minutes,
                servings=servings,
                instructions=instructions,
            )
            for name, quantity, unit in ingredients:
                Ingredient.objects.create(recipe=recipe, name=name, quantity=quantity, unit=unit)
            saved.append(recipe)
        for n, recipe in enumerate(saved):
            MealPlan.objects.create(
                household=home,
                recipe=recipe,
                date=today + timedelta(days=n),
                servings=2,
            )
        ShoppingEntry.objects.create(household=home, name="Lemons", quantity=2)
        ShoppingEntry.objects.create(
            household=home, name="Wholegrain bread", quantity=1, unit="pack"
        )
        self.stdout.write(self.style.SUCCESS(f"Demo created. Username: {username}"))
        if options["noinput"] and not options["password"]:
            self.stdout.write(f"Generated password (save it now): {password}")
