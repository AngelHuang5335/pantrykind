from datetime import timedelta
from django.db.models import F
from django.shortcuts import render
from django.utils import timezone
from pantry.access import household_required
from pantry.models import Item,MealPlan,CookLog
def landing(request):return render(request,'landing.html')

@household_required
def dashboard(request):
    today=timezone.localdate()
    stock=Item.objects.filter(household=request.household,archived=False,quantity__gt=0)
    soon=stock.filter(expiry_date__range=(today,today+timedelta(days=request.household.reminder_days))).order_by('expiry_date','name')
    past=stock.filter(expiry_date__lt=today)
    plans=MealPlan.objects.filter(household=request.household,date__range=(today,today+timedelta(days=6)),cooked__isnull=True).select_related('recipe')[:5]
    return render(request,'dashboard.html',{'today':today,'stock_count':stock.count(),'soon_count':soon.count(),'past_count':past.count(),'soon':soon[:6],'plans':plans,'cooked_count':CookLog.objects.filter(household=request.household,created_at__date__gte=today-timedelta(days=6)).count()})
