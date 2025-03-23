from django.contrib import admin
from .models import User, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(admin.ModelAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'is_active', 'date_joined')
    search_fields = ('email',)

admin.site.register(User, UserAdmin)

