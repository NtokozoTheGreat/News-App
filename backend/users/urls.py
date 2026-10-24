from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("users/registration", views.register_user, name='registration'),
    path("users/update/", views.update_profile, name="update_profile"),
    path("users/become_journalist/", views.become_journalist, name="become_journalist"),
    path("users/delete/", views.delete_profile, name="delete_profile")

]
