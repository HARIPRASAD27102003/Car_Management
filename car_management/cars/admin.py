# cars/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

from .models import Car, CarImage

# Define a custom UserAdmin class
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    # Add the OTP field and email verification fields if needed
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('otp',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('otp',)}),
    )

# Register the custom User model with the custom UserAdmin class
admin.site.register(User, CustomUserAdmin)

class CarImageInline(admin.TabularInline):  # or use StackedInline
    model = CarImage  # Define the model for the inline
    extra = 1  # Number of empty forms to display

class CarImageAdmin(admin.ModelAdmin):
    list_display = ('car', 'image_tag')  # Use the `image_tag` method for the image preview

class CarAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'tags', 'created_at')

admin.site.register(Car, CarAdmin)
admin.site.register(CarImage, CarImageAdmin)
