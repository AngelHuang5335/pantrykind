from pantry.locking import household_write
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from pantry.access import household_required
from pantry.forms import ShoppingForm
from pantry.models import ShoppingEntry
from pantry.services import add_to_shopping


@household_required
@household_write
@require_http_methods(["GET", "POST"])
def index(request):
    form = ShoppingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        add_to_shopping(request.household, **form.cleaned_data)
        messages.success(request, "Added to your shopping list.")
        return redirect("shopping")
    entries = ShoppingEntry.objects.filter(household=request.household)
    return render(request, "shopping/index.html", {"form": form, "entries": entries})


@household_required
@household_write
@require_POST
def toggle(request, pk):
    entry = get_object_or_404(ShoppingEntry, pk=pk, household=request.household)
    if entry.checked:
        from django.db import transaction

        with transaction.atomic():
            add_to_shopping(request.household, entry.name, entry.quantity, entry.unit)
            entry.delete()
    else:
        entry.checked = True
        entry.save(update_fields=["checked"])
    return redirect("shopping")


@household_required
@household_write
@require_http_methods(["GET", "POST"])
def edit(request, pk):
    entry = get_object_or_404(ShoppingEntry, pk=pk, household=request.household)
    form = ShoppingForm(request.POST or None, instance=entry)
    if request.method == "POST" and form.is_valid():
        from django.db import transaction

        with transaction.atomic():
            if entry.checked:
                form.save()
            else:
                entry.delete()
                add_to_shopping(request.household, **form.cleaned_data)
        return redirect("shopping")
    return render(request, "shopping/edit.html", {"form": form, "entry": entry})


@household_required
@household_write
@require_POST
def delete(request, pk):
    get_object_or_404(ShoppingEntry, pk=pk, household=request.household).delete()
    messages.success(request, "Removed from your list.")
    return redirect("shopping")


@household_required
@household_write
@require_POST
def clear_checked(request):
    count, _ = ShoppingEntry.objects.filter(household=request.household, checked=True).delete()
    messages.success(request, f"Cleared {count} checked entries.")
    return redirect("shopping")


@household_required
@household_write
@require_POST
def add_low_stock(request):
    from pantry.models import Item
    from decimal import Decimal
    from django.db import transaction
    from pantry.normalization import food_key

    with transaction.atomic():
        items = Item.objects.filter(household=request.household, archived=False)
        totals = {}
        for item in items:
            key = (food_key(item.name), item.unit)
            group = totals.setdefault(
                key,
                {"name": item.name, "quantity": Decimal("0"), "target": Decimal("0")},
            )
            group["quantity"] += item.quantity
            group["target"] = max(group["target"], item.low_stock_at)
        count = 0
        for (name_key, unit), group in totals.items():
            needed = max(group["target"] - group["quantity"], Decimal("0"))
            current = ShoppingEntry.objects.filter(
                household=request.household,
                normalized_name=name_key,
                unit=unit,
                checked=False,
            ).first()
            missing = needed - (current.quantity if current else 0)
            if missing > 0:
                add_to_shopping(request.household, group["name"], missing, unit)
                count += 1
    messages.success(request, f"Updated {count} shopping entries from low stock.")
    return redirect("shopping")


@household_required
@household_write
@require_http_methods(["GET", "POST"])
def purchase(request, pk):
    from django.core.exceptions import ValidationError
    from django.http import Http404
    from pantry.forms import PurchaseForm
    from pantry.services import purchase_shopping

    entry = ShoppingEntry.objects.filter(pk=pk, household=request.household).first()
    form = PurchaseForm(request.POST or None, initial={"amount": entry.quantity if entry else None})
    if request.method == "POST" and form.is_valid():
        try:
            receipt = purchase_shopping(
                household=request.household, entry_id=pk, actor=request.user, **form.cleaned_data
            )
        except ValidationError as error:
            form.add_error(None, error)
        except ShoppingEntry.DoesNotExist:
            raise Http404 from None
        else:
            messages.success(request, "Purchase saved. A new batch is now in your pantry.")
            if receipt.item_id:
                return redirect("item_detail", pk=receipt.item_id)
            return redirect("shopping_purchases")
    if not entry:
        raise Http404
    return render(request, "shopping/purchase.html", {"entry": entry, "form": form})


@household_required
def purchases(request):
    from django.core.paginator import Paginator
    from pantry.models import PurchaseReceipt

    receipts = PurchaseReceipt.objects.filter(household=request.household).select_related("actor")
    page = Paginator(receipts, 30).get_page(request.GET.get("page"))
    return render(request, "shopping/purchases.html", {"page": page})
