# cars/urls.py
from django.urls import path
from django.conf import settings
from .views import logout_view, login_view, profile_view
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path("login/", login_view, name="login"),
    path("profile/", profile_view, name="profile"),
     path("logout/", logout_view, name="logout"),
     path('', views.home, name='home'),  # Home page URL
    path('list-cars/', views.list_cars, name='list_cars'),
    path('add-car/', views.create_car, name='create_car'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    path('car/<int:car_id>/delete/', views.delete_car, name='delete_car'),
    path('car/<int:car_id>/update/', views.update_car_view, name='update_car'),
]