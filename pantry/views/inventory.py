from pantry.locking import household_write
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from pantry.access import household_required
from pantry.forms import ItemForm
from pantry.models import Item, CATEGORIES, LOCATIONS
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta


@household_required
@household_write
def index(request):
    items = Item.objects.filter(
        household=request.household, archived=request.GET.get("status") == "archived"
    )
    query = request.GET.get("q", "").strip()[:120]
    if query:
        items = items.filter(Q(name__icontains=query) | Q(notes__icontains=query))
    status = request.GET.get("status", "")
    today = timezone.localdate()
    if status == "soon":
        items = items.filter(
            expiry_date__range=(
                today,
                today + timedelta(days=request.household.reminder_days),
            ),
            quantity__gt=0,
        )
    elif status == "past":
        items = items.filter(expiry_date__lt=today, quantity__gt=0)
    elif status == "undated":
        items = items.filter(expiry_date__isnull=True)
    elif status == "low":
        items = items.filter(low_stock_at__gt=0, quantity__lte=F("low_stock_at"))
    category = request.GET.get("category", "")
    if category in dict(CATEGORIES):
        items = items.filter(category=category)
    location = request.GET.get("location", "")
    if location in dict(LOCATIONS):
        items = items.filter(location=location)
    page = Paginator(
        items.order_by(F("expiry_date").asc(nulls_last=True), "name", "pk"), 24
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "inventory/index.html",
        {
            "items": page,
            "page": page,
            "query": query,
            "category": category,
            "location": location,
            "categories": CATEGORIES,
            "locations": LOCATIONS,
            "status": status,
        },
    )


@household_required
@household_write
@require_http_methods(["GET", "POST"])
def create(request):
    form = ItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.household = request.household
        item.save()
        messages.success(request, "Added to your pantry.")
        return redirect("inventory")
    return render(request, "inventory/form.html", {"form": form, "heading": "Add something good"})


@household_required
@household_write
@require_http_methods(["GET", "POST"])
def edit(request, pk):
    item = get_object_or_404(Item, pk=pk, household=request.household)
    form = ItemForm(request.POST or None, instance=item)
    from django import forms

    form.fields["revision"] = forms.DateTimeField(
        widget=forms.HiddenInput, initial=item.updated_at.isoformat()
    )
    form.fields.pop("quantity")
    if item.events.exists():
        form.fields.pop("unit")
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data["revision"] != item.updated_at:
            form.add_error(None, "This batch changed while you were editing. Reload before saving.")
            return render(
                request, "inventory/form.html", {"form": form, "heading": "Edit " + item.name}
            )
        form.save()
        messages.success(request, "Item updated.")
        return redirect("inventory")
    return render(request, "inventory/form.html", {"form": form, "heading": "Edit " + item.name})


@household_required
@household_write
def detail(request, pk):
    item = get_object_or_404(Item, pk=pk, household=request.household)
    events = item.events.select_related("actor")[:50]
    return render(request, "inventory/detail.html", {"item": item, "events": events})


from django.core.exceptions import ValidationError
from django.http import Http404
from pantry.forms import StockActionForm
from pantry.services import record_stock

STOCK_ACTIONS = {
    "used": "Use some",
    "restocked": "Top up this batch",
    "wasted": "Record discarded food",
}


@household_required
@household_write
@require_http_methods(["GET", "POST"])
def stock_action(request, pk, kind):
    if kind not in STOCK_ACTIONS:
        raise Http404
    item = get_object_or_404(Item, pk=pk, household=request.household, archived=False)
    form = StockActionForm(request.POST or None, initial={"amount": item.quantity})
    if kind == "wasted":
        form.fields["note"].required = True
        form.fields[
            "note"
        ].help_text = (
            "What happened? For example: forgotten in the fridge, spoiled, or cooked too much."
        )
    if request.method == "POST" and form.is_valid():
        try:
            record_stock(
                household=request.household,
                item_id=item.pk,
                actor=request.user,
                kind=kind,
                **form.cleaned_data,
            )
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Stock movement recorded.")
            return redirect("item_detail", pk=item.pk)
    return render(
        request,
        "inventory/action.html",
        {"form": form, "item": item, "heading": STOCK_ACTIONS[kind]},
    )


from django.views.decorators.http import require_POST


@household_required
@household_write
@require_POST
def archive(request, pk):
    item = get_object_or_404(Item, pk=pk, household=request.household)
    item.archived = not item.archived
    item.save(update_fields=["archived", "updated_at"])
    messages.success(request, "Item archived." if item.archived else "Item restored.")
    return redirect("item_detail", pk=pk)


@household_required
@household_write
@require_http_methods(["GET", "POST"])
def duplicate(request, pk):
    source = get_object_or_404(Item, pk=pk, household=request.household)
    initial = {
        field: getattr(source, field)
        for field in ["name", "category", "location", "unit", "low_stock_at"]
    }
    form = ItemForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.household = request.household
        item.save()
        messages.success(request, "New batch added with its own date.")
        return redirect("item_detail", pk=item.pk)
    return render(request, "inventory/form.html", {"form": form, "heading": "Add another batch"})
