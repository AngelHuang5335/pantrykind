"""Opt-in daily reminders. Enqueuing is safe to repeat; delivery is a separate job."""

from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from pantry.locking import lock_household
from pantry.models import Item, Membership, ReminderJob, ReminderSubscription


def enqueue_reminders(now=None):
    now = now or timezone.now()
    created = 0
    members = Membership.objects.filter(
        reminders__enabled=True, user__is_active=True
    ).select_related("household", "user")
    for member in members.iterator(chunk_size=100):
        with transaction.atomic():
            home = lock_household(member.household)
            subscription = ReminderSubscription.objects.filter(
                membership=member, enabled=True, membership__user__is_active=True
            ).first()
            if not subscription:
                continue
            local = now.astimezone(ZoneInfo(home.timezone_name))
            if local.hour < subscription.local_hour:
                continue
            due = Item.objects.filter(
                household=home,
                archived=False,
                quantity__gt=0,
                expiry_date__range=(
                    local.date(),
                    local.date() + timedelta(days=home.reminder_days),
                ),
            ).order_by("expiry_date", "pk")
            total = due.count()
            if not total:
                continue
            payload = {
                "total": total,
                "date": local.date().isoformat(),
                "items": [
                    {
                        "name": item.name,
                        "quantity": str(item.quantity),
                        "unit": item.unit,
                        "expiry_date": item.expiry_date.isoformat(),
                    }
                    for item in due[:50]
                ],
            }
            _, new = ReminderJob.objects.get_or_create(
                membership=member,
                local_date=local.date(),
                defaults={"payload": payload, "available_at": now},
            )
            created += int(new)
    return created
