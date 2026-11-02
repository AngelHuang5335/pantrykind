from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator

from django.conf import settings

class Household(models.Model):
    name=models.CharField(max_length=80)
    timezone_name=models.CharField(max_length=64,default='UTC')
    reminder_days=models.PositiveSmallIntegerField(default=7,validators=[MinValueValidator(1),MaxValueValidator(30)])
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):return self.name

class Membership(models.Model):
    household=models.ForeignKey(Household,on_delete=models.CASCADE,related_name='memberships')
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='pantry_memberships')
    role=models.CharField(max_length=10,choices=[('owner','Owner'),('member','Member')],default='member')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['household','user'],name='unique_household_member')]

from decimal import Decimal
from django.core.validators import MinValueValidator,MaxValueValidator
from django.utils import timezone

UNITS=[('pcs','pieces'),('g','g'),('kg','kg'),('ml','ml'),('l','L'),('pack','packs'),('bunch','bunches')]
CATEGORIES=[('produce','Fruit & vegetables'),('dairy','Dairy & eggs'),('protein','Meat & alternatives'),('grains','Grains & staples'),('frozen','Frozen'),('other','Other')]
LOCATIONS=[('pantry','Pantry'),('fridge','Fridge'),('freezer','Freezer'),('other','Other')]

class Item(models.Model):
    household=models.ForeignKey(Household,on_delete=models.CASCADE,related_name='items')
    name=models.CharField(max_length=120)
    category=models.CharField(max_length=12,choices=CATEGORIES,default='other')
    location=models.CharField(max_length=12,choices=LOCATIONS,default='pantry')
    quantity=models.DecimalField(max_digits=12,decimal_places=3,default=1,validators=[MinValueValidator(Decimal('0')),MaxValueValidator(Decimal('999999999'))])
    unit=models.CharField(max_length=8,choices=UNITS,default='pcs')
    expiry_date=models.DateField(null=True,blank=True)
    notes=models.TextField(blank=True,max_length=1000)
    low_stock_at=models.DecimalField(max_digits=12,decimal_places=3,default=0,validators=[MinValueValidator(Decimal('0'))])
    archived=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=['expiry_date','name','pk']
        constraints=[models.CheckConstraint(condition=models.Q(quantity__gte=0),name='nonnegative_item_quantity')]
        indexes=[models.Index(fields=['household','archived','expiry_date'])]
    def __str__(self):return self.name
    @property
    def days_left(self):return (self.expiry_date-timezone.localdate()).days if self.expiry_date else None
    @property
    def expiry_status(self):
        days=self.days_left
        if days is None:return 'No date'
        if days<0:return 'Past date'
        if days==0:return 'Today'
        if days<=self.household.reminder_days:return 'Use soon'
        return 'In date'

import uuid
class StockEvent(models.Model):
    item=models.ForeignKey(Item,on_delete=models.CASCADE,related_name='events')
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True)
    kind=models.CharField(max_length=12,choices=[('used','Used'),('wasted','Discarded'),('restocked','Restocked')])
    amount=models.DecimalField(max_digits=12,decimal_places=3)
    note=models.CharField(max_length=200,blank=True)
    request_id=models.UUIDField(default=uuid.uuid4,unique=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-created_at','-pk']
        constraints=[models.CheckConstraint(condition=models.Q(amount__gt=0),name='positive_stock_event')]

class ShoppingEntry(models.Model):
    normalized_name=models.CharField(max_length=120,default='')
    household=models.ForeignKey(Household,on_delete=models.CASCADE,related_name='shopping_entries')
    name=models.CharField(max_length=120)
    quantity=models.DecimalField(max_digits=12,decimal_places=3,default=1,validators=[MinValueValidator(Decimal('.001'))])
    unit=models.CharField(max_length=8,choices=UNITS,default='pcs')
    checked=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['checked','name','pk']
        constraints=[models.CheckConstraint(condition=models.Q(quantity__gt=0),name='positive_shopping_quantity'),models.UniqueConstraint(fields=['household','normalized_name','unit'],condition=models.Q(checked=False),name='unique_open_shopping_item')]
    def save(self,*args,**kwargs):
        from pantry.normalization import food_key
        self.normalized_name=food_key(self.name)
        super().save(*args,**kwargs)

class Recipe(models.Model):
    household=models.ForeignKey(Household,on_delete=models.CASCADE,related_name='recipes')
    title=models.CharField(max_length=120)
    description=models.CharField(max_length=240,blank=True)
    instructions=models.TextField(max_length=12000)
    servings=models.PositiveSmallIntegerField(default=2,validators=[MinValueValidator(1),MaxValueValidator(50)])
    minutes=models.PositiveSmallIntegerField(default=20,validators=[MinValueValidator(1),MaxValueValidator(1440)])
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:ordering=['title','pk']
    def __str__(self):return self.title

class Ingredient(models.Model):
    recipe=models.ForeignKey(Recipe,on_delete=models.CASCADE,related_name='ingredients')
    name=models.CharField(max_length=120)
    quantity=models.DecimalField(max_digits=12,decimal_places=3,validators=[MinValueValidator(Decimal('.001'))])
    unit=models.CharField(max_length=8,choices=UNITS,default='pcs')
    class Meta:
        ordering=['pk']
        constraints=[models.CheckConstraint(condition=models.Q(quantity__gt=0),name='positive_ingredient_quantity')]

class CookLog(models.Model):
    household=models.ForeignKey(Household,on_delete=models.CASCADE,related_name='cook_logs')
    recipe=models.ForeignKey(Recipe,on_delete=models.SET_NULL,null=True)
    title=models.CharField(max_length=120)
    servings=models.PositiveSmallIntegerField()
    request_id=models.UUIDField(default=uuid.uuid4,unique=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:ordering=['-created_at','-pk']
