from decimal import Decimal,InvalidOperation
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from pantry.models import Item,StockEvent

@transaction.atomic
def record_stock(*,household,item_id,actor,kind,amount,request_id,note=''):
    try:amount=Decimal(str(amount))
    except (InvalidOperation,TypeError,ValueError):raise ValidationError('Enter a valid quantity.')
    if not amount.is_finite() or amount<=0 or amount>Decimal('999999999') or amount.as_tuple().exponent < -3:
        raise ValidationError('Quantity must be positive with at most three decimal places.')
    if kind not in dict(StockEvent._meta.get_field('kind').choices):raise ValidationError('Unknown stock action.')
    item=Item.objects.select_for_update().get(pk=item_id,household=household,archived=False)
    existing=StockEvent.objects.filter(request_id=request_id).first()
    if existing:
        if existing.item_id!=item.pk or existing.kind!=kind or existing.amount!=amount:
            raise ValidationError('This action ID has already been used.')
        return existing
    delta=amount if kind=='restocked' else -amount
    available=Item.objects.filter(pk=item.pk)
    if delta<0:available=available.filter(quantity__gte=amount)
    if not available.update(quantity=F('quantity')+delta,updated_at=timezone.now()):
        raise ValidationError('There is not enough of this batch left.')
    return StockEvent.objects.create(item=item,actor=actor,kind=kind,amount=amount,request_id=request_id,note=note[:200])

from pantry.models import ShoppingEntry
from pantry.normalization import food_key
@transaction.atomic
def add_to_shopping(household,name,quantity,unit):
    quantity=Decimal(str(quantity))
    if not quantity.is_finite() or quantity<=0:raise ValidationError('Enter a positive shopping quantity.')
    name=name.strip()
    if not name or len(name)>120 or unit not in dict(ShoppingEntry._meta.get_field('unit').choices):raise ValidationError('Invalid shopping item.')
    entry,created=ShoppingEntry.objects.get_or_create(household=household,normalized_name=food_key(name),unit=unit,checked=False,defaults={'name':name,'quantity':quantity})
    if not created:
        if not ShoppingEntry.objects.filter(pk=entry.pk,quantity__lte=Decimal('999999999')-quantity).update(quantity=F('quantity')+quantity):raise ValidationError('Shopping quantity is too large.')
        entry.refresh_from_db()
    return entry

import uuid
from pantry.models import Recipe,CookLog
from pantry.matching import match_recipe
from decimal import ROUND_UP
@transaction.atomic
def cook_recipe(*,household,recipe_id,actor,servings,request_id):
    recipe=Recipe.objects.get(pk=recipe_id,household=household)
    if not 1<=servings<=50:raise ValidationError('Choose between 1 and 50 servings.')
    existing=CookLog.objects.filter(request_id=request_id).first()
    if existing:
        if existing.household_id!=household.pk or existing.recipe_id!=recipe_id or existing.servings!=servings:raise ValidationError('This action ID has already been used.')
        return existing
    list(Item.objects.select_for_update().filter(household=household,archived=False).values_list('pk',flat=True))
    matches=match_recipe(recipe,servings)
    if not matches or any(not m['ready'] for m in matches):raise ValidationError('Some ingredients are missing. Update your pantry or shopping list first.')
    for match in matches:
        remaining=match['need_base']
        for item,multiplier in match['batches']:
            if remaining<=0:break
            amount=min(item.quantity,(remaining/multiplier).quantize(Decimal('.001'),rounding=ROUND_UP))
            record_stock(household=household,item_id=item.pk,actor=actor,kind='used',amount=amount,request_id=uuid.uuid5(request_id,str(item.pk)),note='Cooked: '+recipe.title)
            remaining-=amount*multiplier
    return CookLog.objects.create(household=household,recipe=recipe,title=recipe.title,servings=servings,request_id=request_id)
