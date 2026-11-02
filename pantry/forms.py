from django import forms
from pantry.models import Item
class ItemForm(forms.ModelForm):
    class Meta:
        model=Item
        fields=['name','category','location','quantity','unit','expiry_date','low_stock_at','notes']
        widgets={'expiry_date':forms.DateInput(attrs={'type':'date'}),'notes':forms.Textarea(attrs={'rows':3})}
        labels={'expiry_date':'Date on the label'}
        help_texts={'expiry_date':'An organisation aid, not a food-safety assessment. Follow the packaging instructions.'}
    def clean_name(self):
        name=self.cleaned_data['name'].strip()
        if not name:raise forms.ValidationError('Enter an item name.')
        return name

import uuid
from decimal import Decimal
class StockActionForm(forms.Form):
    amount=forms.DecimalField(min_value=Decimal('0.001'),max_value=Decimal('999999999'),max_digits=12,decimal_places=3)
    note=forms.CharField(max_length=200,required=False,widget=forms.Textarea(attrs={'rows':2}))
    request_id=forms.UUIDField(widget=forms.HiddenInput)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['request_id'].initial=uuid.uuid4()

from pantry.models import ShoppingEntry
class ShoppingForm(forms.ModelForm):
    class Meta:model=ShoppingEntry;fields=['name','quantity','unit']
    def clean_name(self):
        name=self.cleaned_data['name'].strip()
        if not name:raise forms.ValidationError('Enter a shopping item.')
        return name
