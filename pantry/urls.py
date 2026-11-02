from django.urls import path
from pantry.views import home
urlpatterns=[path('',home.landing,name='landing')]
