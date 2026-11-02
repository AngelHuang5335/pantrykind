from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404,redirect,render
from django.views.decorators.http import require_http_methods,require_POST
from pantry.access import household_required
from pantry.forms import RecipeForm,Ingredients
from pantry.models import Recipe

@household_required
def index(request):
    from pantry.matching import match_recipe
    from pantry.models import Item
    from django.db.models import Q,F
    from django.utils import timezone
    query=request.GET.get('q','').strip()[:120]
    recipes=Recipe.objects.filter(household=request.household).prefetch_related('ingredients')
    if query:recipes=recipes.filter(title__icontains=query)
    items=list(Item.objects.filter(household=request.household,archived=False,quantity__gt=0).filter(Q(expiry_date__isnull=True)|Q(expiry_date__gte=timezone.localdate())).order_by(F('expiry_date').asc(nulls_last=True),'pk'))
    cards=[]
    for recipe in recipes:
        matches=match_recipe(recipe,items=items)
        recipe.matched_count=sum(m['ready'] for m in matches);recipe.total_count=len(matches)
        recipe.is_ready=bool(matches) and recipe.matched_count==recipe.total_count
        cards.append(recipe)
    cards.sort(key=lambda r:(not r.is_ready,-r.matched_count,r.title))
    if request.GET.get('ready')=='1':cards=[r for r in cards if r.is_ready]
    return render(request,'recipes/index.html',{'recipes':cards,'query':query,'ready_only':request.GET.get('ready')=='1'})

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
    from pantry.matching import match_recipe
    from pantry.forms import ServingsForm
    serving_form=ServingsForm(request.GET or {'servings':recipe.servings})
    servings=serving_form.cleaned_data['servings'] if serving_form.is_valid() else recipe.servings
    matches=match_recipe(recipe,servings)
    return render(request,'recipes/detail.html',{'recipe':recipe,'matches':matches,'serving_form':serving_form,'servings':servings,'ready':bool(matches) and all(m['ready'] for m in matches)})

@household_required
@require_POST
def shop_missing(request,pk):
    from pantry.matching import match_recipe
    from pantry.services import add_to_shopping
    from pantry.models import ShoppingEntry
    from pantry.normalization import food_key
    from decimal import Decimal,ROUND_UP
    recipe=get_object_or_404(Recipe,pk=pk,household=request.household)
    from pantry.forms import ServingsForm
    serving_form=ServingsForm(request.POST)
    servings=serving_form.cleaned_data['servings'] if serving_form.is_valid() else recipe.servings
    with transaction.atomic():
        for match in match_recipe(recipe,servings):
            missing=match['missing'].quantize(Decimal('.001'),rounding=ROUND_UP)
            current=ShoppingEntry.objects.filter(household=request.household,normalized_name=food_key(match['name']),unit=match['unit'],checked=False).first()
            gap=missing-(current.quantity if current else 0)
            if gap>0:add_to_shopping(request.household,match['name'],gap,match['unit'])
    messages.success(request,'Added only the missing quantities to your list.');return redirect('shopping')
