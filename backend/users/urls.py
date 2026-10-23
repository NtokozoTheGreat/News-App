from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("users/registration", views.register_user, name='registration'),
    path("user/update/", views.update_profile, name="update_profile"),
    path("user/become_journalist/", views.become_journalist, name="registration"),
    path("user/delete/", views.delete_profile, name="delete_profile")
    
]