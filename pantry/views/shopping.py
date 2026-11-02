from django.contrib import messages
from django.shortcuts import get_object_or_404,redirect,render
from django.views.decorators.http import require_http_methods,require_POST
from pantry.access import household_required
from pantry.forms import ShoppingForm
from pantry.models import ShoppingEntry
from pantry.services import add_to_shopping

@household_required
@require_http_methods(['GET','POST'])
def index(request):
    form=ShoppingForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        add_to_shopping(request.household,**form.cleaned_data)
        messages.success(request,'Added to your shopping list.');return redirect('shopping')
    entries=ShoppingEntry.objects.filter(household=request.household)
    return render(request,'shopping/index.html',{'form':form,'entries':entries})

@household_required
@require_POST
def toggle(request,pk):
    entry=get_object_or_404(ShoppingEntry,pk=pk,household=request.household)
    if entry.checked:
        from django.db import transaction
        with transaction.atomic():
            add_to_shopping(request.household,entry.name,entry.quantity,entry.unit)
            entry.delete()
    else:
        entry.checked=True;entry.save(update_fields=['checked'])
    return redirect('shopping')
