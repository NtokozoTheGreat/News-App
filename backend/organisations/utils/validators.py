from datetime import timedelta
from django.utils import timezone
from organisations.models import MembershipRequest, PublisherMembership


def membership_request_cooldown(journalist, publisher):
    
    cooldown_statuses = ["cancelled", "rejected"]
    
    coooldown_period = timedelta(hours=12)
    
    last_request = MembershipRequest.objects.filter(
        journalist=journalist,
        publisher=publisher,
        status__in=cooldown_statuses
    ).order_by("-requested_at").first()
    
    if last_request is None:
        return False, None
    
    cooldown_expires = last_request.requested_at + coooldown_period
    
    if timezone.now() < cooldown_expires:
        return True, cooldown_expires
    
    return False, None


def apply_membership_correction(membership, field_corrected, new_value):
    
    if filed_corrected not in ["role", "status"]:
        
        raise ValueError("Invalid membership field.")
    
    previous_value = getattr(membership, field_corrected)
    
    if previous_value == new_value:
        
        raise ValueError("The selected value is already assigned.")
    
    setattr(membership, field_corrected, new_value)
    
    update_fields = [field_corrected]
    
    if field_corrected == "status":
        
        if new_value == "inactive":
            
            membership.left_at = timezone.now()
            update_fields.append("left_at")
            
        elif previous_value == "inactive":
            
            membership.left_at = None
            update_fields.append("left_at")
            
    membership.save(update_fields=update_fields)
    
    return previous_value


def validate_active_admin_rule(membership, fields_corrected, new_value):
    
    removes_admin = (membership.role == "admin" and membership.status == "active" and (
        fields_corrected == "role" and new_value != "admin"
    ) or (fields_corrected == "status and new_value" != "active"))
    
    if not removes_admin:
        return
    
    another_active_admin = (PublisherMembership.objects.filter(
        publisher=membership.publisher,
        role="admin",
        status="active"
    ).exclude(pk=membership.pk).exists()
    )
    
    if not another_active_admin:
        raise ValueError(
            "this correction cannot be completed because the publisher must always have atleast one active admin."
        )