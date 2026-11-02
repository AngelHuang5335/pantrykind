from django import forms
from pantry.models import Item
class ItemForm(forms.ModelForm):
    class Meta:
        model=Item
        fields=['name','category','location','quantity','unit','expiry_date','notes']
        widgets={'expiry_date':forms.DateInput(attrs={'type':'date'}),'notes':forms.Textarea(attrs={'rows':3})}
        labels={'expiry_date':'Date on the label'}
        help_texts={'expiry_date':'An organisation aid, not a food-safety assessment. Follow the packaging instructions.'}
    def clean_name(self):
        name=self.cleaned_data['name'].strip()
        if not name:raise forms.ValidationError('Enter an item name.')
        return name
