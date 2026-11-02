from django.http import JsonResponse
from django.views.decorators.http import require_GET
from pantry.access import household_required
from pantry.models import Item,ShoppingEntry
@household_required
@require_GET
def inventory(request):
    items=Item.objects.filter(household=request.household,archived=False).order_by('pk')
    try:after=max(int(request.GET.get('after',0)),0)
    except ValueError:return JsonResponse({'error':'after must be a nonnegative integer'},status=400)
    batch=list(items.filter(pk__gt=after)[:101]);more=len(batch)>100;batch=batch[:100]
    response=JsonResponse({'items':[{'id':i.pk,'name':i.name,'quantity':str(i.quantity),'unit':i.unit,'location':i.location,'category':i.category,'expiry_date':i.expiry_date.isoformat() if i.expiry_date else None} for i in batch],'next_after':batch[-1].pk if more else None})
    response['Cache-Control']='private, no-store';return response
@household_required
@require_GET
def shopping(request):
    entries=ShoppingEntry.objects.filter(household=request.household,checked=False).order_by('pk')[:500]
    response=JsonResponse({'items':[{'id':e.pk,'name':e.name,'quantity':str(e.quantity),'unit':e.unit} for e in entries]})
    response['Cache-Control']='private, no-store';return response
