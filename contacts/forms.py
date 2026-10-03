from django import forms

from .models import Contact


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
