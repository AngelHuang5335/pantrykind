from django.contrib import messages
from django.shortcuts import get_object_or_404,redirect,render
from django.views.decorators.http import require_http_methods,require_POST
from pantry.access import household_required
from pantry.forms import ShoppingForm
from pantry.models import ShoppingEntry

@household_required
@require_http_methods(['GET','POST'])
def index(request):
    form=ShoppingForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        entry=form.save(commit=False);entry.household=request.household;entry.save()
        messages.success(request,'Added to your shopping list.');return redirect('shopping')
    entries=ShoppingEntry.objects.filter(household=request.household)
    return render(request,'shopping/index.html',{'form':form,'entries':entries})
