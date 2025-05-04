from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.email

# New model for calendar events
class CalendarEvent(models.Model):
    LOCATION_CHOICES = (
        ('north', 'North Field'),
        ('east', 'East Field'),
        ('south', 'South Field'),
        ('west', 'West Field'),
        ('all', 'All Fields'),
    )
    
    REMINDER_CHOICES = (
        ('none', 'No Reminder'),
        ('same', 'Same Day'),
        ('1day', '1 Day Before'),
        ('3days', '3 Days Before'),
        ('1week', '1 Week Before'),
    )
    
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES, default='all')
    reminder = models.CharField(max_length=10, choices=REMINDER_CHOICES, default='none')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"