from datetime import timedelta
from django.db.models import Sum,Count
from django.shortcuts import render
from django.utils import timezone
from pantry.access import household_required
from pantry.models import StockEvent,CookLog
@household_required
def index(request):
    since=timezone.localdate()-timedelta(days=29)
    events=StockEvent.objects.filter(item__household=request.household,created_at__date__gte=since)
    summary=list(events.values('kind','item__unit').annotate(amount=Sum('amount'),movements=Count('pk')).order_by('kind','item__unit'))
    waste=list(events.filter(kind='wasted').values('item__name','item__unit').annotate(amount=Sum('amount'),movements=Count('pk')).order_by('-movements','item__name')[:10])
    return render(request,'insights.html',{'since':since,'summary':summary,'waste':waste,'meals':CookLog.objects.filter(household=request.household,created_at__date__gte=since).count()})
