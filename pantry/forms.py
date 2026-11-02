from django import forms
from pantry.models import Item
class ItemForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['low_stock_at'].required=False
    def clean_low_stock_at(self):
        from decimal import Decimal
        return self.cleaned_data.get('low_stock_at') or Decimal('0')
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

from django.forms import inlineformset_factory,BaseInlineFormSet
from pantry.models import Recipe,Ingredient
from pantry.normalization import food_key
class RecipeForm(forms.ModelForm):
    class Meta:
        model=Recipe;fields=['title','description','servings','minutes','instructions']
        widgets={'instructions':forms.Textarea(attrs={'rows':7})}
class IngredientFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):return
        active=[f.cleaned_data for f in self.forms if f.cleaned_data and not f.cleaned_data.get('DELETE')]
        if not active:raise forms.ValidationError('Add at least one ingredient.')
        seen=set()
        for entry in active:
            key=(food_key(entry['name']),entry['unit'])
            if not key[0]:raise forms.ValidationError('Ingredient names cannot be blank.')
            if key in seen:raise forms.ValidationError('Combine duplicate ingredients with the same unit into one line.')
            seen.add(key)
Ingredients=inlineformset_factory(Recipe,Ingredient,fields=['name','quantity','unit'],formset=IngredientFormSet,extra=3,max_num=30,validate_max=True,can_delete=True)

class ServingsForm(forms.Form):
    servings=forms.IntegerField(min_value=1,max_value=50)

from pantry.models import MealPlan
class MealPlanForm(forms.ModelForm):
    class Meta:
        model=MealPlan;fields=['recipe','date','slot','servings']
        widgets={'date':forms.DateInput(attrs={'type':'date'})}
    def __init__(self,*args,household,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['recipe'].queryset=Recipe.objects.filter(household=household)
