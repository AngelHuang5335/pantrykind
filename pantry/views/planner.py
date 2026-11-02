from datetime import date, timedelta
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from pantry.access import household_required
from pantry.forms import MealPlanForm
from pantry.models import MealPlan


@household_required
@require_http_methods(["GET", "POST"])
def index(request):
    form = MealPlanForm(
        request.POST or None,
        household=request.household,
        initial={"date": timezone.localdate()},
    )
    if request.method == "POST" and form.is_valid():
        plan = form.save(commit=False)
        plan.household = request.household
        plan.save()
        messages.success(request, "Added to your meal plan.")
        return redirect("planner")
    try:
        day = date.fromisoformat(request.GET.get("week", ""))
    except ValueError:
        day = timezone.localdate()
    monday = day - timedelta(days=day.weekday())
    plans = list(
        MealPlan.objects.filter(
            household=request.household,
            date__range=(monday, monday + timedelta(days=6)),
        ).select_related("recipe", "cooked")
    )
    days = [
        {
            "date": monday + timedelta(days=n),
            "plans": [p for p in plans if p.date == monday + timedelta(days=n)],
        }
        for n in range(7)
    ]
    return render(
        request,
        "planner/index.html",
        {
            "form": form,
            "days": days,
            "monday": monday,
            "previous": monday - timedelta(days=7),
            "next": monday + timedelta(days=7),
        },
    )


@household_required
@require_http_methods(["GET", "POST"])
def edit(request, pk):
    plan = get_object_or_404(MealPlan, pk=pk, household=request.household)
    if plan.cooked:
        messages.error(request, "Cooked meals cannot be edited.")
        return redirect("planner")
    form = MealPlanForm(request.POST or None, instance=plan, household=request.household)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("planner")
    return render(request, "planner/edit.html", {"form": form, "plan": plan})


@household_required
@require_POST
def delete(request, pk):
    get_object_or_404(MealPlan, pk=pk, household=request.household).delete()
    messages.success(request, "Meal removed from the calendar.")
    return redirect("planner")


@household_required
@require_POST
def cook(request, pk):
    import uuid
    from django.db import transaction
    from django.core.exceptions import ValidationError
    from pantry.services import cook_recipe

    try:
        with transaction.atomic():
            plan = get_object_or_404(
                MealPlan.objects.select_for_update(), pk=pk, household=request.household
            )
            if not plan.cooked:
                plan.cooked = cook_recipe(
                    household=request.household,
                    recipe_id=plan.recipe_id,
                    actor=request.user,
                    servings=plan.servings,
                    request_id=uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"pantrykind:plan:{plan.pk}:{plan.household_id}",
                    ),
                )
                plan.save(update_fields=["cooked"])
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, "Meal recorded. Your pantry is up to date.")
    return redirect("planner")


@household_required
def export_calendar(request):
    from django.http import HttpResponse
    from pantry.calendar import calendar

    plans = MealPlan.objects.filter(
        household=request.household, date__gte=timezone.localdate(), cooked__isnull=True
    ).select_related("recipe")[:366]
    response = HttpResponse(calendar(plans), content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="pantrykind-meals.ics"'
    return response
