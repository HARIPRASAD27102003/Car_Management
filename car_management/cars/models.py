# cars/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import models
from django.conf import settings
import random
from django.utils.html import format_html
import base64

class User(AbstractUser):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)  # OTP for verification

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    

class Car(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CarImage(models.Model):
    car = models.ForeignKey(Car, related_name='car_images', on_delete=models.CASCADE)
    image_data = models.BinaryField(null=True, blank=True)  # Add null=True and blank=True for safety
    content_type = models.CharField(max_length=255, default="image/jpeg")

    def image_tag(self):
        """Render the image in the admin."""
        if self.image_data:
            encoded_image = base64.b64encode(self.image_data).decode('utf-8')
            return format_html('<img src="data:{};base64,{}" width="100" height="100" />', self.content_type, encoded_image)
        return "(No image)"
    
    image_tag.short_description = "Image Preview"

    def __str__(self):
        return f"Image for {self.car.title}"


