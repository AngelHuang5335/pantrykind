from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from pantry.models import Household, Membership

class HouseholdForm(forms.ModelForm):
    class Meta:model=Household;fields=['name']

@login_required
@require_http_methods(['GET','POST'])
def create(request):
    form=HouseholdForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            household=form.save()
            Membership.objects.create(household=household,user=request.user,role='owner')
            request.session['household_id']=household.pk
        return redirect('dashboard')
    return render(request,'households/create.html',{'form':form})
