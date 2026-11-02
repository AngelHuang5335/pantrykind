"""Leased outbox processing with fenced acknowledgements and bounded retries.

The initial transport is a durable in-app inbox. It needs no email credentials,
does not send externally, and its delivery and acknowledgement commit together.
"""

from datetime import timedelta
from uuid import uuid4

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from pantry.locking import lock_household
from pantry.models import Notification, ReminderJob, ReminderSubscription

MAX_ATTEMPTS = 5
LEASE = timedelta(minutes=2)


def claim_job(now=None):
    now = now or timezone.now()
    eligible = Q(status="pending", available_at__lte=now) | Q(
        status="delivering", lease_until__lte=now
    )
    ReminderJob.objects.filter(eligible, attempts__gte=MAX_ATTEMPTS).update(
        status="dead", lease_token=None, lease_until=None, last_error="Retry limit reached"
    )
    candidates = list(
        ReminderJob.objects.filter(eligible, attempts__lt=MAX_ATTEMPTS)
        .order_by("available_at", "pk")
        .values_list("pk", flat=True)[:100]
    )
    for pk in candidates:
        token = uuid4()
        changed = ReminderJob.objects.filter(eligible, pk=pk, attempts__lt=MAX_ATTEMPTS).update(
            status="delivering",
            lease_token=token,
            lease_until=now + LEASE,
            attempts=F("attempts") + 1,
        )
        if changed:
            return ReminderJob.objects.select_related("membership__household").get(
                pk=pk, lease_token=token
            )
    return None


def deliver_inbox(job):
    """Called inside the fenced transaction; a second delivery cannot duplicate the inbox."""
    Notification.objects.get_or_create(
        job=job, defaults={"membership": job.membership, "payload": job.payload}
    )


@transaction.atomic
def finish_job(claim, now=None):
    now = now or timezone.now()
    lock_household(claim.membership.household)
    job = (
        ReminderJob.objects.select_for_update()
        .filter(
            pk=claim.pk, status="delivering", lease_token=claim.lease_token, lease_until__gt=now
        )
        .first()
    )
    if not job:
        return "stale"
    opted_in = ReminderSubscription.objects.filter(
        membership_id=job.membership_id, enabled=True, membership__user__is_active=True
    ).exists()
    if not opted_in:
        job.status = "cancelled"
    else:
        # Delivery is deliberately in this transaction: an exception rolls back the inbox too.
        deliver_inbox(job)
        job.status = "sent"
        job.completed_at = now
    job.lease_token = None
    job.lease_until = None
    job.last_error = ""
    job.save(update_fields=["status", "completed_at", "lease_token", "lease_until", "last_error"])
    return job.status


def fail_job(claim, error, now=None):
    now = now or timezone.now()
    # Record the exception class only. Exception messages can contain private food/account data.
    dead = claim.attempts >= MAX_ATTEMPTS
    return ReminderJob.objects.filter(
        pk=claim.pk, status="delivering", lease_token=claim.lease_token, lease_until__gt=now
    ).update(
        status="dead" if dead else "pending",
        lease_token=None,
        lease_until=None,
        available_at=now + timedelta(seconds=min(3600, 30 * 2 ** (claim.attempts - 1))),
        last_error=type(error).__name__[:80],
    )


def process_one(now=None):
    claim = claim_job(now)
    if not claim:
        return "empty"
    try:
        return finish_job(claim, now)
    except Exception as error:
        fail_job(claim, error, now)
        return "failed"
