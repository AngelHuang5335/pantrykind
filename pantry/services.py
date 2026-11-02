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
