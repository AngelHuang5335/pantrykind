from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from pantry.locking import lock_household
from pantry.models import ReminderJob, ReminderSubscription


class Command(BaseCommand):
    help = "Explicitly retry one dead job after resolving its failure. Opted-out jobs stay stopped."

    def add_arguments(self, parser):
        parser.add_argument("job_id", type=int)

    def handle(self, *args, **options):
        candidate = (
            ReminderJob.objects.select_related("membership__household")
            .filter(pk=options["job_id"])
            .first()
        )
        if not candidate:
            raise CommandError("Job not found.")
        with transaction.atomic():
            lock_household(candidate.membership.household)
            job = (
                ReminderJob.objects.select_for_update()
                .filter(pk=candidate.pk, status="dead")
                .first()
            )
            if (
                not job
                or not ReminderSubscription.objects.filter(
                    membership_id=job.membership_id, enabled=True, membership__user__is_active=True
                ).exists()
            ):
                raise CommandError(
                    "Only dead jobs belonging to an active opted-in member can be retried."
                )
            job.status = "pending"
            job.attempts = 0
            job.available_at = timezone.now()
            job.lease_token = None
            job.lease_until = None
            job.last_error = ""
            job.save()
        self.stdout.write(f"Requeued job {candidate.pk}.")
