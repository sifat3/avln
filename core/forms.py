# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *


class VendorRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class SingleProductOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['product', 'quantity']
    
    product = forms.ModelChoiceField(queryset=Product.objects.filter(available__gt=0), required=True)
    quantity = forms.IntegerField(min_value=1, required=True)

