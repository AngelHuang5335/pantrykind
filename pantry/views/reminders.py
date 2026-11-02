from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from pantry.access import household_required
from pantry.locking import household_write
from pantry.models import Notification, ReminderJob, ReminderSubscription


class ReminderPreferencesForm(forms.ModelForm):
    class Meta:
        model = ReminderSubscription
        fields = ["enabled", "local_hour"]
        labels = {"enabled": "Remind me in my inbox", "local_hour": "Hour of the day (0–23)"}
        help_texts = {"local_hour": "Uses your kitchen's timezone. No email is sent."}


@household_required
@household_write
@require_http_methods(["GET", "POST"])
def inbox(request):
    subscription = ReminderSubscription.objects.filter(membership=request.membership).first()
    form = ReminderPreferencesForm(
        request.POST or None,
        instance=subscription or ReminderSubscription(membership=request.membership),
    )
    if request.method == "POST" and form.is_valid():
        subscription = form.save()
        if not subscription.enabled:
            ReminderJob.objects.filter(
                membership=request.membership, status__in=["pending", "delivering"]
            ).update(
                status="cancelled",
                lease_token=None,
                lease_until=None,
            )
        messages.success(request, "Your reminder preferences are saved.")
        return redirect("reminder_inbox")
    notifications = Notification.objects.filter(membership=request.membership)
    page = Paginator(notifications, 20).get_page(request.GET.get("page"))
    return render(request, "reminders/inbox.html", {"form": form, "page": page})


@household_required
@household_write
@require_POST
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, membership=request.membership)
    if not notification.read_at:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return redirect("reminder_inbox")
