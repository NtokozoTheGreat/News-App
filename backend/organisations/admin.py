from django.contrib import admin
from .models import MembershipRequest

# Register your models here.

admin.register(MembershipRequest)

class MembershipRequestAdmin(admin.ModelAdmin):
    
    list_display = (
        "membership",
        "request_type",
        "status",
        "requested_at",
        "reviewed_at",
        "reviewed_by",
    )
    
    list_filter = (
        "request_type",
        "status",
        "requested_at"
    )
    
    search_feilds = (
        "membership__journalist__user__username",
        "membership__publisher__name"
    )
    
    readonly_fields = (
        "membership",
        "request_type",
        "status",
        "requested_at",
        "reviewed_at",
        "reviewed_by"
    )

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False