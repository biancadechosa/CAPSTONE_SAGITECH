from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
import numpy as np
import tensorflow as tf
from PIL import Image  
import io
import json
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import User, UserProfile, CalendarEvent

try:
    model = tf.keras.models.load_model('sagitech/model/banana_ripeness_model.h5')
    classes = ['1.5_months_old', '15_days_old', '3_weeks_before_harvest']
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    classes = ['1.5_months_old', '15_days_old', '3_weeks_before_harvest']

def LandingPage(request):
    return render(request, 'sagitech/index.html')

@ensure_csrf_cookie
def LoginPage(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not email or not password:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Email and password are required'}, status=400)
            else:
                messages.error(request, 'Email and password are required')
                return render(request, 'sagitech/login.html')
            
         # Check if account exists
        if not User.objects.filter(email=email).exists():
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Account does not exist. Please log in first'}, status=404)
            else:
                messages.error(request, 'Account does not exist. Please log in first')
                return render(request, 'sagitech/login.html')
        
        # Authenticate user with email
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'message': 'Login successful',
                    'redirect_url': '/dashboard/'
                })
            else:
                return redirect('dashboard')
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Invalid email or password'}, status=401)
            else:
                messages.error(request, 'Invalid email or password')
                return render(request, 'sagitech/login.html')
    
    return render(request, 'sagitech/login.html')

def SignupPage(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Form validation
        if not fullname or not email or not password or not confirm_password:
            messages.error(request, 'All fields are required')
            return render(request, 'sagitech/signup.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'sagitech/signup.html')
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request, 'sagitech/signup.html')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'sagitech/signup.html')
        
        try:
            # Create user with email
            user = User.objects.create_user(
                email=email,
                password=password
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                full_name=fullname
            )
            
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    return render(request, 'sagitech/signup.html')

@login_required
def DashboardPage(request):
    return render(request, 'sagitech/dashboard.html')

@login_required
def LogoutView(request):
    logout(request)
    return redirect('login')

@login_required
def BananaScan(request):
    # in case the Flask API is not available
    if request.method == 'POST' and request.FILES.get('file'):
        img_file = request.FILES['file']

        # Validate and preprocess the image
        try:
            # Use PIL instead of keras.preprocessing
            img = Image.open(img_file).convert("RGB")
            img = img.resize((224, 224))

            # Convert PIL image to numpy array
            img_array = np.array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            # Check if model is loaded
            if model is None:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Model not loaded. Please use the Flask API.'
                })

            # Predict using the model
            prediction = model.predict(img_array)
            result_index = np.argmax(prediction)
            confidence = float(np.max(prediction)) * 100

            return JsonResponse({
                'status': 'success',
                'prediction': classes[result_index],
                'confidence': f'{confidence:.2f}%',
                'predicted_index': int(result_index),
                'all_probabilities': prediction.tolist()[0]
            })
        except Exception as e:
            import traceback
            return JsonResponse({
                'status': 'error', 
                'message': str(e),
                'traceback': traceback.format_exc()
            })

    return render(request, 'sagitech/scan.html')

@login_required
def Schedule(request):
    return render(request, 'sagitech/schedule.html')

@method_decorator(csrf_exempt, name='dispatch')
class EventsView(View):
    def get(self, request):
        # Get all events for the current user
        events = CalendarEvent.objects.filter(created_by=request.user)
        
        # Format events for FullCalendar
        event_list = []
        for event in events:
            event_data = {
                'id': str(event.id),
                'title': event.title,
                'start': event.start_date.isoformat(),
                'end': event.end_date.isoformat() if event.end_date else event.start_date.isoformat(),
                'extendedProps': {
                    'description': event.description,
                    'location': event.location,
                    'reminder': event.reminder
                }
            }
            event_list.append(event_data)
        
        return JsonResponse(event_list, safe=False)
    
    def post(self, request):
        # Create a new event
        data = json.loads(request.body)
        
        event = CalendarEvent(
            title=data.get('title'),
            start_date=data.get('start'),
            end_date=data.get('end') if data.get('end') else None,
            description=data.get('description', ''),
            location=data.get('location', 'all'),
            reminder=data.get('reminder', 'none'),
            created_by=request.user
        )
        event.save()
        
        # Return the created event
        return JsonResponse({
            'id': str(event.id),
            'title': event.title,
            'start': event.start_date.isoformat(),
            'end': event.end_date.isoformat() if event.end_date else event.start_date.isoformat(),
            'extendedProps': {
                'description': event.description,
                'location': event.location,
                'reminder': event.reminder
            }
        })

@method_decorator(csrf_exempt, name='dispatch')
class EventDetailView(View):
    def get(self, request, event_id):
        try:
            event = CalendarEvent.objects.get(id=event_id, created_by=request.user)
            return JsonResponse({
                'id': str(event.id),
                'title': event.title,
                'start': event.start_date.isoformat(),
                'end': event.end_date.isoformat() if event.end_date else event.start_date.isoformat(),
                'extendedProps': {
                    'description': event.description,
                    'location': event.location,
                    'reminder': event.reminder
                }
            })
        except CalendarEvent.DoesNotExist:
            return JsonResponse({'error': 'Event not found'}, status=404)
    
    def put(self, request, event_id):
        try:
            event = CalendarEvent.objects.get(id=event_id, created_by=request.user)
            data = json.loads(request.body)
            
            event.title = data.get('title', event.title)
            event.start_date = data.get('start', event.start_date)
            event.end_date = data.get('end') if data.get('end') else None
            event.description = data.get('description', event.description)
            event.location = data.get('location', event.location)
            event.reminder = data.get('reminder', event.reminder)
            event.save()
            
            return JsonResponse({
                'id': str(event.id),
                'title': event.title,
                'start': event.start_date.isoformat(),
                'end': event.end_date.isoformat() if event.end_date else event.start_date.isoformat(),
                'extendedProps': {
                    'description': event.description,
                    'location': event.location,
                    'reminder': event.reminder
                }
            })
        except CalendarEvent.DoesNotExist:
            return JsonResponse({'error': 'Event not found'}, status=404)
    
    def delete(self, request, event_id):
        try:
            event = CalendarEvent.objects.get(id=event_id, created_by=request.user)
            event.delete()
            return JsonResponse({'success': True})
        except CalendarEvent.DoesNotExist:
            return JsonResponse({'error': 'Event not found'}, status=404)

class UpcomingEventsView(View):
    def get(self, request):
        # Get upcoming events for the current user
        today = datetime.now().date()
        events = CalendarEvent.objects.filter(
            created_by=request.user,
            start_date__gte=today
        ).order_by('start_date')[:10]  # Limit to 10 upcoming events
        
        # Format events for the frontend
        event_list = []
        for event in events:
            event_data = {
                'id': str(event.id),
                'title': event.title,
                'start': event.start_date.isoformat(),
                'end': event.end_date.isoformat() if event.end_date else event.start_date.isoformat(),
                'location': event.location,
                'description': event.description,
                'reminder': event.reminder
            }
            event_list.append(event_data)
        
        return JsonResponse(event_list, safe=False)

@login_required
def Settings(request):
    return render(request, 'sagitech/settings.html')

