from pantry.locking import household_write
from pantry.access import household_required
from pantry.models import Item, ShoppingEntry
from pantry.csvio import FIELDS, csv_response


@household_required
@household_write
def export_inventory(request):
    items = Item.objects.filter(household=request.household, archived=False).order_by("pk")
    return csv_response(
        "pantrykind-pantry.csv",
        FIELDS,
        ([getattr(item, field) for field in FIELDS] for item in items.iterator()),
    )


@household_required
@household_write
def export_shopping(request):
    entries = ShoppingEntry.objects.filter(household=request.household, checked=False)
    return csv_response(
        "pantrykind-shopping.csv",
        ["name", "quantity", "unit"],
        entries.values_list("name", "quantity", "unit"),
    )


from django import forms
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods, require_POST
from pantry.csvio import parse_inventory_csv
import secrets, time


class ImportForm(forms.Form):
    file = forms.FileField(
        help_text="UTF-8 CSV, at most 1 MB and 500 batches. Required columns: name, quantity, unit."
    )


@household_required
@household_write
@require_http_methods(["GET", "POST"])
def import_inventory(request):
    form = ImportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        uploaded = form.cleaned_data["file"]
        try:
            if uploaded.size > 1024 * 1024:
                raise ValueError("The CSV must be smaller than 1 MB.")
            rows = parse_inventory_csv(uploaded.read(1024 * 1024 + 1))
        except ValueError as error:
            form.add_error("file", str(error))
        else:
            pending = {
                "household_id": request.household.pk,
                "rows": rows,
                "token": secrets.token_urlsafe(24),
                "created_at": time.time(),
            }
            request.session["pantry_import"] = pending
            return render(request, "transfers/preview.html", {"pending": pending})
    return render(request, "transfers/import.html", {"form": form})


from django.contrib import messages
from django.db import transaction, IntegrityError
from pantry.models import ImportReceipt
import hashlib
from pantry.forms import ItemForm


@household_required
@household_write
@require_POST
def confirm_import(request):
    pending = request.session.get("pantry_import")
    if (
        not pending
        or pending["household_id"] != request.household.pk
        or time.time() - pending["created_at"] > 1200
        or not secrets.compare_digest(pending["token"], request.POST.get("token", ""))
    ):
        messages.error(
            request,
            "This preview expired or belongs to another kitchen. Upload the file again.",
        )
        return redirect("inventory_import")
    digest = hashlib.sha256(pending["token"].encode()).hexdigest()
    try:
        with transaction.atomic():
            ImportReceipt.objects.create(
                household=request.household,
                token_hash=digest,
                row_count=len(pending["rows"]),
            )
            for row in pending["rows"]:
                form = ItemForm(row)
                if not form.is_valid():
                    raise ValueError("Previously validated import changed unexpectedly.")
                item = form.save(commit=False)
                item.household = request.household
                item.save()
    except IntegrityError:
        if ImportReceipt.objects.filter(token_hash=digest, household=request.household).exists():
            request.session.pop("pantry_import", None)
            messages.info(request, "This preview was already imported.")
            return redirect("inventory")
        raise
    del request.session["pantry_import"]
    messages.success(request, f"Imported {len(pending['rows'])} new batches.")
    return redirect("inventory")
