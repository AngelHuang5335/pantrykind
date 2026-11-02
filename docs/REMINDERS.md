# Reliable inbox reminders

Users opt in at `/inbox/`. The scheduler checks the kitchen's IANA timezone,
preferred hour and reminder window. There is at most one snapshot per membership
and local date. Empty, archived and past-date stock is excluded. Up to 50 batches
are included, with the full count shown. The snapshot does not track later edits.

Run both commands every minute, with the same environment and working directory
as the web application (cron, systemd timers or Windows Task Scheduler):

```sh
python manage.py enqueue_reminders
python manage.py reminder_worker --limit 100
```

Delivery currently means a persistent **in-app inbox**, with no SMTP service or
external messages. This preserves a simple offline deployment. It does not push
browser notifications: users see reminders when they open the inbox.

Workers atomically claim jobs using a unique two-minute lease token. A crashed
worker's job becomes claimable after lease expiry. A stale token cannot deliver,
acknowledge or fail somebody else's claim. Inbox creation and acknowledgement
share a transaction, and a unique job reference prevents duplicate notifications.
Failures use 30, 60, 120 and 240 second delays, then stop after five attempts.
An expired fifth claim also becomes dead. Disabling reminders invalidates active
leases and cancels unsent jobs. Removing a member deletes their private queue
and inbox. No reminder payload or exception message is written to worker output.

```sh
python manage.py reminder_status
python manage.py retry_reminder 123
```

Monitor `dead` counts and oldest pending age; a growing age usually means the
scheduler or worker is not running. Inspect jobs through a trusted database
session to find an ID. Retry a specific dead job only after fixing the fault.
It retains its original dated snapshot. The public `/healthz/` endpoint checks
database readiness only and intentionally does not expose queue or account data.

If the database itself is unavailable, let the process fail and alert through your
scheduler. The lease recovers unfinished work once the database returns. Future
external transports would need their own delivery contracts; this inbox's atomic
delivery guarantee must not be assumed to apply to email or webhooks.
