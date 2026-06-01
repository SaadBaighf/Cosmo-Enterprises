from django import forms
from django.core.exceptions import ValidationError
from .models import Client, Order

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'company', 'avatar', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'client@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company Name'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise ValidationError("Name is required.")
        if len(name.strip()) < 2:
            raise ValidationError("Name must be at least 2 characters long.")
        if not name.replace(" ", "").isalpha():
            raise ValidationError("Name can only contain letters and spaces.")
        return name.strip().title()  # Auto-capitalize

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check uniqueness (exclude current instance during edit)
            qs = Client.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("This email is already registered.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove spaces/dashes for validation
            cleaned = ''.join(filter(str.isdigit, phone))
            if len(cleaned) < 10 or len(cleaned) > 15:
                raise ValidationError("Phone number must be 10–15 digits (e.g., +91 98765 43210).")
        return phone

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['fabric_type', 'quantity', 'due_date', 'status', 'payment']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'payment': forms.NumberInput(attrs={'step': '0.01'}),
        }