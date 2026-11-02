"""One lock order for household writes: household, then child rows.

SQLite's no-op UPDATE acquires its database write lock before any reads. PostgreSQL
locks only the household row, allowing unrelated kitchens to work independently.
Call this inside transaction.atomic(), before reading mutable business state.
"""

from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.db.models import F
from functools import wraps

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


def household_write(view):
    """Revalidate membership and acquire the parent lock before a POST reads rows."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.method != "POST":
            return view(request, *args, **kwargs)
        with transaction.atomic():
            request.household = lock_household(request.household, request.user)
            request.membership = Membership.objects.get(
                household=request.household, user=request.user
            )
            return view(request, *args, **kwargs)

    return wrapped
