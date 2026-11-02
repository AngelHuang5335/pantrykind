from django.contrib import messages
from django.shortcuts import get_object_or_404,redirect,render
from django.views.decorators.http import require_http_methods
from pantry.access import household_required
from pantry.forms import ItemForm
from pantry.models import Item

@household_required
def index(request):
    items=Item.objects.filter(household=request.household,archived=False)
    return render(request,'inventory/index.html',{'items':items})

@household_required
@require_http_methods(['GET','POST'])
def create(request):
    form=ItemForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        item=form.save(commit=False);item.household=request.household;item.save()
        messages.success(request,'Added to your pantry.')
        return redirect('inventory')
    return render(request,'inventory/form.html',{'form':form,'heading':'Add something good'})

@household_required
@require_http_methods(['GET','POST'])
def edit(request,pk):
    item=get_object_or_404(Item,pk=pk,household=request.household)
    form=ItemForm(request.POST or None,instance=item)
    if request.method=='POST' and form.is_valid():
        form.save();messages.success(request,'Item updated.');return redirect('inventory')
    return render(request,'inventory/form.html',{'form':form,'heading':'Edit '+item.name})
