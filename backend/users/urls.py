from django.urls import path
from . import views

urlpatterns = [
    path("users/", views.register_user, name='registration'),
    path("profile/update/", views.update_profile, name="update_profile"),
    path("user/become_journalist/", views.become_journalist, name="registration"),
]