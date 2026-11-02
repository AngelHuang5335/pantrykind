from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404,redirect,render
from django.views.decorators.http import require_http_methods,require_POST
from pantry.access import household_required
from pantry.forms import RecipeForm,Ingredients
from pantry.models import Recipe

@household_required
def index(request):
    recipes=Recipe.objects.filter(household=request.household)
    return render(request,'recipes/index.html',{'recipes':recipes})

@household_required
@require_http_methods(['GET','POST'])
def edit(request,pk=None):
    recipe=get_object_or_404(Recipe,pk=pk,household=request.household) if pk else Recipe(household=request.household)
    form=RecipeForm(request.POST or None,instance=recipe)
    ingredients=Ingredients(request.POST or None,instance=recipe,prefix='ingredients')
    if request.method=='POST' and form.is_valid() and ingredients.is_valid():
        with transaction.atomic():form.save();ingredients.save()
        messages.success(request,'Recipe saved.');return redirect('recipe_detail',pk=recipe.pk)
    return render(request,'recipes/form.html',{'form':form,'ingredients':ingredients,'recipe':recipe})

@household_required
def detail(request,pk):
    recipe=get_object_or_404(Recipe,pk=pk,household=request.household)
    return render(request,'recipes/detail.html',{'recipe':recipe})
