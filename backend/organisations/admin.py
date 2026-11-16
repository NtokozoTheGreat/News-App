from django.contrib import admin
from .models import Publisher, PublisherMembership, MembershipRequest, AdministrativeCorrection, AdministrativeCorrectionReversal

# Register your models here.
@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "region",
        "email",
        "created_at"
    )

    list_filter = (
        "region",
    )

    search_fields = (
        "name",
        "email"
    )


@admin.register(PublisherMembership)
class PublisherMembershipAdmin(admin.ModelAdmin):

    list_display = (
        "journalist",
        "publisher",
        "role",
        "status"
    )

    list_filter = (
        "role",
        "status",
        "publisher"
    )

    search_fields = (
        "journalist__user__username",
        "publisher__name"
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MembershipRequest)
class MembershipRequestAdmin(admin.ModelAdmin):

    list_display = (
        "membership",
        "request_type",
        "status",
        "requested_at",
        "reviewed_at",
        "reviewed_by"
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


@admin.register(AdministrativeCorrection)
class AdministrativeCorrectionAdmin(admin.ModelAdmin):

    list_display = (
        "membership_reference",
        "field_corrected",
        "previous_value",
        "new_value",
        "corrected_by",
        "created_at"
    )

    list_filter = (
        "field_corrected",
        "created_at"
    )

    search_fields = (
        "membership_reference",
        "publisher_reference",
        "journalist_reference",
        "reason",
        "corrected_by__username"
    )

    readonly_fields = (
        "membership",
        "membership_reference",
        "publisher_reference",
        "journalist_reference",
        "field_corrected",
        "previous_value",
        "new_value",
        "reason",
        "corrected_by",
        "created_at"
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AdministrativeCorrectionReversal)
class AdministrativeCorrectionReversalAdmin(admin.ModelAdmin):

    list_display = (
        "original_correction",
        "membership_reference",
        "field_corrected",
        "previous_value",
        "restored_value",
        "reversed_by",
        "created_at"
    )

    list_filter = (
        "field_corrected",
        "created_at"
    )

    search_fields = (
        "membership_reference",
        "publisher_reference",
        "journalist_reference",
        "reason",
        "reversed_by__username"
    )

    readonly_fields = (
        "original_correction",
        "membership",
        "membership_reference",
        "publisher_reference",
        "journalist_reference",
        "field_corrected",
        "previous_value",
        "restored_value",
        "reason",
        "reversed_by",
        "created_at"
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
