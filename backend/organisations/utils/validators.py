from datetime import timedelta
from django.utils import timezone
from organisations.models import MembershipRequest


def membership_request_coooldown(journalist, publisher):
    
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