from django.urls import path
from . import views

urlpatterns = [
        path("", views.publisher_list, name="publisher_list"),
        path("register/", views.register_publisher, name="register_publisher"),
        path(
            "<int:pk>/update/",
            views.update_publisher,
            name="update_publisher",
        ),
        path("<int:pk>/", views.publisher_detail, name="publisher_detail"),
    ]
