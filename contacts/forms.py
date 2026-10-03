from django import forms
from django.core.exceptions import ValidationError

from .models import Contact


class ContactImportForm(forms.Form):
    """Upload a .CSV file with contacts."""

    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )

    def clean_file(self):
        uploaded = self.cleaned_data['file']
        if not uploaded.name.lower().endswith('.csv'):
            raise ValidationError('Only .CSV files are allowed.')
        if uploaded.size > 2 * 1024 * 1024:
            raise ValidationError('File is too large (max 2 MB).')
        return uploaded


class ContactForm(forms.ModelForm):
    """Create/edit form. Server-side validation mirrors validation.js."""

    class Meta:
        model = Contact
        fields = [
            'first_name',
            'last_name',
            'phone',
            'email',
            'city',
            'status',
            'is_shared',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '+48 123 456 789'}
            ),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_shared': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
