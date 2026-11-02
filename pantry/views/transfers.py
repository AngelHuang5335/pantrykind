from pantry.access import household_required
from pantry.models import Item,ShoppingEntry
from pantry.csvio import FIELDS,csv_response
@household_required
def export_inventory(request):
    items=Item.objects.filter(household=request.household,archived=False).order_by('pk')
    return csv_response('pantrykind-pantry.csv',FIELDS,([getattr(item,field) for field in FIELDS] for item in items.iterator()))
@household_required
def export_shopping(request):
    entries=ShoppingEntry.objects.filter(household=request.household,checked=False)
    return csv_response('pantrykind-shopping.csv',['name','quantity','unit'],entries.values_list('name','quantity','unit'))
