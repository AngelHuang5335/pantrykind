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

from django.contrib import messages
from django.http import HttpResponseForbidden
from pantry.access import household_required
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError

class PreferencesForm(forms.ModelForm):
    class Meta:model=Household;fields=['name','timezone_name','reminder_days']
    def clean_timezone_name(self):
        name=self.cleaned_data['timezone_name']
        try:ZoneInfo(name)
        except (ZoneInfoNotFoundError,ValueError):raise forms.ValidationError('Use an IANA timezone, such as Asia/Shanghai or Europe/London.')
        return name

@household_required
@require_http_methods(['GET','POST'])
def settings(request):
    form=PreferencesForm(request.POST or None,instance=request.household)
    if request.method=='POST':
        if request.membership.role!='owner':return HttpResponseForbidden('Only the kitchen owner can change these settings.')
        if form.is_valid():form.save();messages.success(request,'Kitchen preferences updated.');return redirect('household_settings')
    return render(request,'households/settings.html',{'form':form,'members':request.household.memberships.select_related('user'),'kitchens':request.user.pantry_memberships.select_related('household')})

from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
@login_required
@require_POST
def switch(request,pk):
    member=get_object_or_404(Membership,user=request.user,household_id=pk)
    request.session['household_id']=member.household_id
    return redirect('dashboard')
