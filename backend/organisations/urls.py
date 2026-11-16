from django.urls import path
from . import views
from . import admin_corrections

app_name = "organisations"

urlpatterns = [
        path("", views.publisher_list, name="publisher_list"),
        path("register/", views.register_publisher, name="register_publisher"),
        path("<int:pk>/update/", views.update_publisher, name="update_publisher"),
        path("<int:pk>/", views.publisher_detail, name="publisher_detail"),
        path("<int:pk>/members/", views.publisher_members, name="publisher_members"),
        path("<int:pk>/members/promote/<int:membership_id>/", views.promote_member, name="promote_member"),
        path("<int:pk>/members/demote/<int:membership_id>/", views.demmote_member, name="demote_member"),
        path("<int:pk>/members/remove/<int:membership_id>/", views.remove_member, name="remove_member"),
        path("<int:pk>/join/", views.request_to_join, name="request_to_join"),
        path("<int:pk>/join-requests/", views.publisher_membership_request, name="publisher_membership_requests"),
        path("<int:pk>/join-requests/<int:request_id>/review/", views.review_membership_request, name="review_membership_request"),
        path("<int:pk>/leave/", views.request_to_leave, name="request_to_leave"),
        path("<int:pk>/leave-requests/", views.publisher_leave_requests, name="publisher_leave_requests"),
        path("<int:pk>/leave-requests/<int:request_id>/review/", views.review_leave_request, name="review_leave_request"),
        path("my-memberships/", views.my_publisher_memberships, name="my_publisher_memberships"),
        path("my-membership-requests/", views.my_membership_requests, name="my_membership_requests"),
        path("my-membership-requests/<int:request_id>/cancel-join/", views.cancel_join_request, name="cancel_join_request"),
        path("my-membership-requests/<int:request_id>/cancel-leave/", views.cancel_leave_request, name="cancel_leave_request"),
        path("administrative-corrections/", admin_corrections.administrative_correction_history, name="administrative_correction_history"),
        path("administrative-corrections/create/", admin_corrections.create_administrative_correction, name="create_administrative_correction"),
        path("administrative-corrections/<int:pk>/", admin_corrections.administrative_correction_detail, name="administrative_correction_detail"),
        path("administrative-corrections/<int:pk>/reverse/", admin_corrections.reverse_administrative_correction, name="reverse_administrative_correction"),
        path("administrative-corrections/reversals/", admin_corrections.administrative_correction_reversal_history, name="administrative_correction_reversal_history"),
    ]
