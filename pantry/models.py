from django.db import models

from django.conf import settings

class Household(models.Model):
    name=models.CharField(max_length=80)
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
        if days<=7:return 'Use soon'
        return 'In date'
