from django import forms
from .models import Lead

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['full_name', 'email', 'mobile_number', 'through', 'comments']


