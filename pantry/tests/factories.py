from django.contrib.auth.models import User
from pantry.models import Household,Membership
def kitchen(username='cook'):
    user=User.objects.create_user(username,password='kitchen-test-pass-234')
    home=Household.objects.create(name=username+"'s kitchen")
    Membership.objects.create(household=home,user=user,role='owner')
    return user,home
