from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from .models import  User
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, get_object_or_404
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import logout
from django.contrib import messages
import base64
import random
from .forms import CarForm, UserForm, UserLoginForm
import os
import certifi
import ssl
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Car, CarImage
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
import json
from dotenv import load_dotenv

load_dotenv()

def generate_otp():
    # Generate a 6-digit OTP
    return random.randint(100000, 999999)

def home(request):
    return render(request, 'cars/home.html')

# Temporarily bypass SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

def send_otp_email(email, otp):
    try:
        message = Mail(
            from_email="27102003hari@gmail.com",
            to_emails=email,
            subject="Your OTP Code",
            plain_text_content=f"Your OTP is {otp}. Please use this to verify your account."
        )
        sg = SendGridAPIClient(api_key=os.getenv('API_KEY'))
        response = sg.send(message)
        print(f"Email sent successfully. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")

def register(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # Extract cleaned data from the form
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Create and save the user directly
            otp = generate_otp()  # Generate a 6-digit OTP
            hashed_password = make_password(password)  # Hash the password for security
            
            # Create user with necessary fields
            user = User.objects.create(
                username=username,
                email=email,
                password=hashed_password,
                is_active=False,  # Deactivate until email is verified
                otp=otp,  # Store the OTP
            )

            # Send OTP to the user's email
            send_otp_email(email, otp)

            # Store email in session and redirect to OTP verification page
            request.session['email'] = email
            return redirect('verify_otp')  # Redirect to OTP verification page
    else:
        form = UserForm()
    return render(request, 'cars/register.html', {'form': form})

def verify_otp(request):
    email = request.session.get('email')
    if not email:
        return redirect('register')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        try:
            user = User.objects.get(email=email, otp=otp)
            user.is_active = True  # Activate account
            user.otp = ''  # Clear OTP after successful verification
            user.save()
            messages.success(request, 'Your account has been activated!')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'cars/verify_otp.html')

def login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile')
            else:
                form.add_error(None, "Invalid credentials")
    else:
        form = UserLoginForm()
    return render(request, "cars/login.html", {"form": form})

def profile_view(request):
    return render(request, "cars/profile.html")

def logout_view(request):
    logout(request)
    return redirect('login') 

@login_required
def create_car(request):
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(request.user)  # Call the custom save method in the form
            return redirect('list_cars')
    else:
        form = CarForm()
    return render(request, 'cars/create_car.html', {'form': form})

@login_required
def list_cars(request):
    # Get the list of cars for the logged-in user
    cars = Car.objects.filter(user=request.user)

    # Handle search query if it exists
    search_query = request.GET.get('q', '')  # Get the search query (empty string if not provided)

    if search_query:
        # Filter cars based on title, description, or tags
        cars = cars.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) | 
            Q(tags__icontains=search_query)
        )

    # Prepare a list to include cars with their single image
    cars_with_images = []

    for car in cars:
        car_data = {
            'id': car.id,
            'title': car.title,
            'description': car.description,
            'tags': car.tags,
            'created_at': car.created_at,
            'image': None  # Placeholder for the single image
        }

        # Process only the first image of the car
        first_image = car.car_images.first()  # Get the first related image
        if first_image:
            # Convert binary data to Base64
            car_data['image'] = base64.b64encode(first_image.image_data).decode('utf-8')

        cars_with_images.append(car_data)

    # Pass the structured data and the search query to the template
    return render(request, 'cars/list_cars.html', {'cars': cars_with_images, 'search_query': search_query})

@api_view(['GET'])
def search_cars(request):
    keyword = request.GET.get('q', '')
    cars = Car.objects.filter(
        models.Q(title__icontains=keyword) |
        models.Q(description__icontains=keyword) |
        models.Q(tags__icontains=keyword)
    )
    car_list = [{"id": car.id, "title": car.title, "description": car.description} for car in cars]
    return JsonResponse({"cars": car_list}, status=200)


@login_required
def update_car_view(request, car_id):
    # Get the car object for the logged-in user
    car = get_object_or_404(Car, id=car_id, user=request.user)
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)  # Pass instance of the car for updates
        
        if form.is_valid():
            # Save the updated car details
            # updated_car = form.save(commit=False)
            # updated_car.user = request.user  # Ensure that the user is assigned correctly
            form.save(request.user)  # Save the car object

            # Handle image deletions
            delete_images = request.POST.getlist('delete_images')  # Get the list of image IDs to delete
            if delete_images:
                CarImage.objects.filter(id__in=delete_images, car=car).delete()

            # Redirect to the updated car details page
            return redirect('car_detail', car_id=car.id)
    else:
        # Pre-populate the form with the existing car data
        form = CarForm(instance=car)    
    # print(car.car_image)
    car_data = {
        'id': car.id,
        'title': car.title,
        'description': car.description,
        'tags': car.tags,
        'created_at': car.created_at,
        'images': []
    }

    # Process all images related to the car
    for image in car.car_images.all():
        encoded_image = base64.b64encode(image.image_data).decode('utf-8')
        car_data['images'].append({
            'id': image.id,
            'encoded_image': encoded_image
        })

    return render(request, 'cars/update_car.html', {'form': form, 'car': car_data})




@login_required
def delete_car(request, car_id):
    # Get the car object and ensure it belongs to the logged-in user
    car = get_object_or_404(Car, id=car_id, user=request.user)

    if request.method == 'POST':
        # Delete the car and all associated images
        car.delete()
        return redirect('list_cars')  # Redirect to the car list page

    # If the request method is not POST, redirect to the car detail page
    return redirect('car_detail', car_id=car_id)

@login_required
def car_detail(request, car_id):
    # Fetch the car object belonging to the logged-in user
    car = get_object_or_404(Car, id=car_id, user=request.user)

    # Prepare car data with images
    car_data = {
        'id': car.id,
        'title': car.title,
        'description': car.description,
        'tags': car.tags,
        'created_at': car.created_at,
        'images': []
    }

    # Process all images related to the car
    for image in car.car_images.all():
        encoded_image = base64.b64encode(image.image_data).decode('utf-8')
        car_data['images'].append({
            'id': image.id,
            'encoded_image': encoded_image
        })

    # Pass car data to the template
    return render(request, 'cars/car_detail.html', {'car': car_data})


def api_docs(request):
    api_data = [
        {
            "endpoint": "/register/",
            "method": "POST",
            "description": "Register a new user.",
            "authentication": "No authentication required.",
            "request_params": {
                "body": {
                    "email": "string, required",
                    "password": "string, required"
                }
            },
            "response": {
                "201": {
                    "message": "User registered successfully",
                    "data": {"user_id": "int"}
                },
                "400": {"error": "Validation failed"}
            }
        },
        {
            "endpoint": "/verify_otp/",
            "method": "POST",
            "description": "Verify OTP for user registration.",
            "authentication": "No authentication required.",
            "request_params": {
                "body": {
                    "email": "string, required",
                    "otp": "string, required"
                }
            },
            "response": {
                "200": {"message": "OTP verified successfully"},
                "400": {"error": "Invalid OTP"}
            }
        },
        {
            "endpoint": "/login/",
            "method": "POST",
            "description": "Login an existing user.",
            "authentication": "No authentication required.",
            "request_params": {
                "body": {
                    "email": "string, required",
                    "password": "string, required"
                }
            },
            "response": {
                "200": {"message": "Login successful", "token": "JWT token"},
                "401": {"error": "Invalid credentials"}
            }
        },
        {
            "endpoint": "/profile/",
            "method": "GET",
            "description": "Retrieve the logged-in user's profile.",
            "authentication": "Required (JWT token in Authorization header).",
            "request_params": {
                "header": {"Authorization": "Bearer <JWT token>"}
            },
            "response": {
                "200": {"data": {"email": "string", "joined_at": "datetime"}},
                "401": {"error": "Unauthorized"}
            }
        },
        {
            "endpoint": "/logout/",
            "method": "POST",
            "description": "Logout the logged-in user.",
            "authentication": "Required (JWT token in Authorization header).",
            "request_params": {
                "header": {"Authorization": "Bearer <JWT token>"}
            },
            "response": {
                "200": {"message": "Logout successful"},
                "401": {"error": "Unauthorized"}
            }
        },
        {
            "endpoint": "/list-cars/",
            "method": "GET",
            "description": "Retrieve a list of all cars belonging to the logged-in user.",
            "authentication": "Required (JWT token in Authorization header).",
            "request_params": {
                "header": {"Authorization": "Bearer <JWT token>"}
            },
            "response": {
                "200": {
                    "data": [
                        {"id": "int", "title": "string", "description": "string", "tags": "string"}
                    ]
                },
                "401": {"error": "Unauthorized"}
            }
        },
        {
            "endpoint": "/add-car/",
            "method": "POST",
            "description": "Add a new car.",
            "authentication": "Required (JWT token in Authorization header).",
            "request_params": {
                "header": {"Authorization": "Bearer <JWT token>"},
                "body": {
                    "title": "string, required",
                    "description": "string, required",
                    "tags": "string, optional",
                    "images": "list of files, optional"
                }
            },
            "response": {
                "201": {"message": "Car created successfully", "car_id": "int"},
                "400": {"error": "Validation error"},
                "401": {"error": "Unauthorized"}
            }
        },
        {
            "endpoint": "/car/<int:car_id>/",
            "method": "GET",
            "description": "Retrieve details of a specific car.",
            "authentication": "Required (JWT token in Authorization header).",
            "request_params": {
                "header": {"Authorization": "Bearer <JWT token>"},
                "path_params": {"car_id": "int, required"}
            },
            "response": {
                "200": {
                    "data": {
                        "id": "int",
                        "title": "string",
                        "description": "string",
                        "tags": "string",
                        "images": ["base64-encoded images"]
                    }
                },
                "404": {"error": "Car not found"},
                "401": {"error": "Unauthorized"}
            }
        },
        {
            "endpoint": "/car/<int:car_id>/update/",
            "method": "PUT",
            "description": "Update details of a specific car.",
            "authentication": "Required (JWT token in Authorization header).",
            "request_params": {
                "header": {"Authorization": "Bearer <JWT token>"},
                "path_params": {"car_id": "int, required"},
                "body": {
                    "title": "string, optional",
                    "description": "string, optional",
                    "tags": "string, optional",
                    "images": "list of files, optional"
                }
            },
            "response": {
                "200": {"message": "Car updated successfully"},
                "404": {"error": "Car not found"},
                "401": {"error": "Unauthorized"}
            }
        },
        {
            "endpoint": "/car/<int:car_id>/delete/",
            "method": "DELETE",
            "description": "Delete a specific car.",
            "authentication": "Required (JWT token in Authorization header).",
            "request_params": {
                "header": {"Authorization": "Bearer <JWT token>"},
                "path_params": {"car_id": "int, required"}
            },
            "response": {
                "200": {"message": "Car deleted successfully"},
                "404": {"error": "Car not found"},
                "401": {"error": "Unauthorized"}
            }
        }
    ]

    # Serialize API data to pretty JSON for the template
    for api in api_data:
        api['request_params_pretty'] = json.dumps(api.get('request_params', {}), indent=4)
        api['response_pretty'] = json.dumps(api.get('response', {}), indent=4)

    return render(request, 'cars/api_docs.html', {'api_data': api_data})