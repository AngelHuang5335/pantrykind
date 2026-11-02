from datetime import date,timedelta
from django.contrib import messages
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from django.views.decorators.http import require_http_methods,require_POST
from pantry.access import household_required
from pantry.forms import MealPlanForm
from pantry.models import MealPlan

@household_required
@require_http_methods(['GET','POST'])
def index(request):
    form=MealPlanForm(request.POST or None,household=request.household,initial={'date':timezone.localdate()})
    if request.method=='POST' and form.is_valid():
        plan=form.save(commit=False);plan.household=request.household;plan.save()
        messages.success(request,'Added to your meal plan.');return redirect('planner')
    try:day=date.fromisoformat(request.GET.get('week',''))
    except ValueError:day=timezone.localdate()
    monday=day-timedelta(days=day.weekday())
    plans=list(MealPlan.objects.filter(household=request.household,date__range=(monday,monday+timedelta(days=6))).select_related('recipe','cooked'))
    days=[{'date':monday+timedelta(days=n),'plans':[p for p in plans if p.date==monday+timedelta(days=n)]} for n in range(7)]
    return render(request,'planner/index.html',{'form':form,'days':days,'monday':monday,'previous':monday-timedelta(days=7),'next':monday+timedelta(days=7)})
