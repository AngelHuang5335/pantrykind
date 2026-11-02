"""One lock order for household writes: household, then child rows.

SQLite's no-op UPDATE acquires its database write lock before any reads. PostgreSQL
locks only the household row, allowing unrelated kitchens to work independently.
Call this inside transaction.atomic(), before reading mutable business state.
"""

from django.core.exceptions import PermissionDenied
from django.db import connection
from django.db.models import F

from pantry.models import Household, Membership


def lock_household(household, actor=None):
    if connection.vendor == "sqlite":
        Household.objects.filter(pk=household.pk).update(reminder_days=F("reminder_days"))
    home = Household.objects.select_for_update().get(pk=household.pk)
    if (
        actor is not None
        and not Membership.objects.filter(household=home, user=actor, user__is_active=True).exists()
    ):
        raise PermissionDenied("You are no longer a member of this kitchen.")
    return home
