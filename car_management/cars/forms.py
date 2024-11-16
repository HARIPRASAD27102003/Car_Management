# cars/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Car, CarImage, User
from django.core.exceptions import ValidationError
import re

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, label="Enter OTP")

class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        
        # Check minimum length
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        # Check for uppercase letter
        if not any(char.isupper() for char in password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        # Check for lowercase letter
        if not any(char.islower() for char in password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        
        # Check for a digit
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit.")
        
        # Check for a special character
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValidationError("Password must contain at least one special character.")
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")


class CarForm(forms.ModelForm):
    images = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)

    class Meta:
        model = Car
        fields = ['title', 'description', 'tags']
        
    def save(self, user, *args, **kwargs):
        # Save the car object
        car = super().save(commit=False)
        car.user = user  # Assign the logged-in user to the car
        car.save()

        # Handle images
        for image_file in self.files.getlist('images'):
            CarImage.objects.create(
                car=car,
                image_data=image_file.read()  # Save raw binary data
            )
        return car