from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from pantry.models import Membership

class HouseholdMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        request.household=None
        request.membership=None
        if request.user.is_authenticated:
            memberships=Membership.objects.filter(user=request.user).select_related('household')
            member=memberships.filter(household_id=request.session.get('household_id')).first() or memberships.order_by('pk').first()
            if member:request.household,request.membership=member.household,member
        from django.utils import timezone
        with timezone.override(request.household.timezone_name if request.household else 'UTC'):
            return self.get_response(request)

def household_required(view):
    @login_required
    @wraps(view)
    def wrapped(request,*args,**kwargs):
        if request.household is None:return redirect('household_create')
        return view(request,*args,**kwargs)
    return wrapped
