from django.contrib import messages
from django.shortcuts import get_object_or_404,redirect,render
from django.views.decorators.http import require_http_methods
from pantry.access import household_required
from pantry.forms import ItemForm
from pantry.models import Item,CATEGORIES,LOCATIONS
from django.db.models import Q,F
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta

@household_required
def index(request):
    items=Item.objects.filter(household=request.household,archived=False)
    query=request.GET.get('q','').strip()[:120]
    if query:items=items.filter(Q(name__icontains=query)|Q(notes__icontains=query))
    status=request.GET.get('status','')
    today=timezone.localdate()
    if status=='soon':items=items.filter(expiry_date__range=(today,today+timedelta(days=7)),quantity__gt=0)
    elif status=='past':items=items.filter(expiry_date__lt=today,quantity__gt=0)
    elif status=='undated':items=items.filter(expiry_date__isnull=True)
    category=request.GET.get('category','')
    if category in dict(CATEGORIES):items=items.filter(category=category)
    location=request.GET.get('location','')
    if location in dict(LOCATIONS):items=items.filter(location=location)
    page=Paginator(items.order_by(F('expiry_date').asc(nulls_last=True),'name','pk'),24).get_page(request.GET.get('page'))
    return render(request,'inventory/index.html',{'items':page,'page':page,'query':query,'category':category,'location':location,'categories':CATEGORIES,'locations':LOCATIONS,'status':status})

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
