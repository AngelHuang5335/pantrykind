from django.shortcuts import render
def landing(request):
    return render(request,'landing.html')

from django.contrib.auth.decorators import login_required
@login_required
def dashboard(request):
    return render(request,'dashboard.html')
