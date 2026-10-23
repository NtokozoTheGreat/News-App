from django.contrib import admin
from .models import UserProfile, JournalistProfile
from django.contrib.auth.models import User

# Register your models here.

admin.site.register(UserProfile)
admin.site.register(JournalistProfile)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0

  
class JournalistProfileInline(admin.StackedInline):
    model = JournalistProfile
    extra = 0

    
class CustomUserAdmin(admin.ModelAdmin):
    
    fields = [
        'username',
        'first_name',
        'last_name',
        'email'
        ]
    
    inlines = [
        UserProfileInline,
        JournalistProfileInline,
    ]

  
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
