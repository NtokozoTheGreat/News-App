from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from .forms import PublisherRegistrationForm, PublisherUpdateForm
from .models import PublisherMembership, Publisher, MembershipRequest
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from users.models import JournalistProfile
from .utils.validators import membership_request_cooldown

# Create your views here.

def get_publisher_admin(request, publisher):
    
    journalist_profile = getattr(request.user, journalist_profile, None)
    
    if journalist_profile is None:
        return None
    
    return publisher.memberships.filter(
        journalist=journalist_profile,
        role="admin",
        status="active" 
        ).first()


@login_required
def register_publisher(request):
    
    if request.method == "POST":
        
        form = PublisherRegistrationForm(request.POST, request.FILES)

        if form.is_valid():
            journalist_profile = getattr(request.user, "journalist_profile", None)

            if journalist_profile is None:
                form.add_error(None, "You need a journalist profile before registering a publisher.")
            
            else:
                try:
                    with transaction.atomic():
                        
                        publisher = form.save(commit=False)
                        publisher. verifivation_status = "unverified"
                        publisher.save()
                        
                        PublisherMembership.objects.create(
                            journalist=journalist_profile,
                            publisher=publisher,
                            role="admin",
                            status="active"
                        )
                
                except IntegrityError:
                    form.add_error("name",
                                   "A publisher with these details could not be registered. Please check the publisher name and try again.")
                    
                else: 
                    messages.success(request, "Your publisher has been registered successfully.")
                    return redirect("organisation:publisher_detail", pk=publisher.pk)
                
    else:
        form = PublisherRegistrationForm()
        
    return render(request, "register_publisher.html", {"form": form})


def publisher_list(request):

    publishers = Publisher.objects.order_by("name")

    return render(request, "publisher_list.html", {"publishers": publishers})


def publisher_detail(request, pk):

    publisher = get_object_or_404(Publisher, pk=pk)

    return render(request, "publisher_detail.html", {"publisher": publisher})



@login_required
def update_publisher(request, pk):
    
    publisher = get_object_or_404(Publisher, pk=pk)
    
    journalist_profile = getattr(request.user, "journalist_profile", None)
    
    if journalist_profile is None:
        messages.error(request, "You do not have permission to update this publisher.")
        
        return redirect("pubisher_detail", pk=publisher.pk)
    
    is_admin = publisher.memberships.filter(
        journalist=journalist_porfile,
        role="admin",
        status="active"
    ).exists()
    
    if not is_admin:
        messages.error(request,"Only an admin can update publisher details.")
        
        return redirect("publisher_details", pk =publisher.pk)
    
    if request.method == "POST":
        form = PublisherRegistrationForm(request.POST, request.FILES, instance=publisher)
        
        if form.is_valid():
            form.save()
            
            messages.success(request, "Publisher details updated successfully")
            return redirect("publisher_detail", pk=publisher.pk,)
            
    else:
        form = PublisherRegistrationForm(instance=publisher)
        
    return render(request, "update_publisher", {"form":form, "publisher": publisher})


@login_required
def publisher_members(request, pk):
    
    publisher = get_object_or_404(Publisher, pk=pk)
    
    admin_membership = get_publisher_admin(request, publisher)
    
    if not admin_membership:
        messages.error(request, "you don't have permission to manage this publisher's mebmers .")
        
        return redirect("publisher_detail", pk=publisher.pk)
    
    active_count = publisher.memberships.filter(status="active").count()
    
    pending_count = publisher.memberships.filter(status="pending").count()
    
    inactive_count = publisher.memberships.filter(status="inactive").count()
    
    rejected_count = publisher.memberships.filter(status="rejected").count()
    
    pending_leave_count = publisher.memberships.filter(requests__request_type="leave", requests__status="pending").count()
    
    total_count = publisher.memberships.count()
    
    membership_status = request.GET.get("status", "active")
    
    valid_statuses = ["active", "pending", "inactive", "leave_requests", "rejected" ,"all"]
    
    if membership_status not in valid_statuses:
        membership_status = "active"
      
    memberships = publisher.memberships.select_related("journalist", "journalist__user")
    
    if membership_status == "leave_requests":
        memberships = memberships.filter(request__request_type="leave", requests__status="pending").distinct()
    
    elif membership_status != "all":
        memberships = memberships.select_related(status= membership_status)
        
    memberships = memberships.order_by("role", "journalist__user__username")
    
    context = {
        "publisher": publisher,
        "memberships": memberships,
        "membership_status": membership_status,
        "active_count": active_count,
        "pending_count": pending_count,
        "pending_leave_count": pending_leave_count,
        "inactive_count": inactive_count,
        "rejected_count": rejected_count,
        "total_count": total_count,
            }
    
    return render(request, "publisher_members.html", context)
    
    
@login_required
@require_POST
def request_to_join(request, pk):
    
    publisher = get_object_or_404(Publisher, pk=pk)
    
    try:
        journalist_profile = request.user.journalist_profile
        
    except JournalistProfile.DoesNotExist:
        messages.error(request, "you need a journalist profile before requesting to join a publisher.")
        
        return redirect("publisher_detail", pk=publisher.pk)

    try:
        with transaction.atomic():
            
            publisher = Publisher.objects.select_for_update().get(pk=publisher.pk)
            
            is_cooling_down, cooldown_expires = membership_request_cooldown(journalist_profile, publisher)
            
            if is_cooling_down:
                messages.error(request, f"You cannot submit another membership request yet. You can try again after {timezone.localtime(cooldown_expires):%d %B %Y at %H:%M}.")
                
                return redirect("publisher_detail", pk=publisher.pk)
            
            membership, created = publisher.memberships.get_or_create(
                journalist=journalist_profile,
                defaults={
                    "role": "journalist",
                    "status": "pending",
                    "pending_request": "join"
                    }
            )
            
            if membership.status == "active":
                messages.info(request, "you are already a member of this publisher. ")
                
                return redirect("publisher_detail", pk=publisher.pk)
            
            existing_request = membership.requests.filter(status="pending").first()
            
            if existing_request:
                messages.info(request, "you already have a pending membership request.")
                
                return redirect("publisher_detail, pk=publisher.pk")
            
            membership.role = "journalist" 
            membership.status = "pending"
            membership.pending_request = "join"
            membership.left_at = None
            membership.save(update_feilds=[
                "status",
                "pending_request",
                "left_at"
                ]
            )
            
            MembershipRequest.objects.create(
                membership=membership,
                request_type="join",
                publisher=publisher,
                status="pending"
                )
            
        messages.success(request, "your request to join this publisher has been submitted.")
    
    except Publisher.DoesNotExist:
        messages.error(request, "publisher not found.")
    
    except IntegrityError:
        messages.error(request, "You already have a pending membership request.")

    return redirect("publisher_detail", pk=publisher.pk)


@login_required
def publisher_membership_request(request, pk):
    
    publisher = get_object_or_404(Publisher, pk=pk)
    
    admin_membership = get_publisher_admin(request, publisher)
    
    if not admin_membership:
        messages.error(request, "you do not have permission to review membership reequests.")
        
        return redirect("publisher_detail", pk=publisher.pk)
    
    membership_requests = MembershipRequest.objects.filter(
        membership__publisher=publisher,
        request_type="join",
        status="pending",
        membership__isnull=False).select_related(
            "membership",
            "membership__journalist",
            "membership__journal__user"
        )
        
    context = {"publisher": publisher,
               "membership_requests": membership_requests}
    
    return render(request, "publisher_membership_requests.html", context)


@login_required
@require_POST
def review_membership_request(request, pk , request_id):
    
    publisher = get_object_or_404(Publisher, pk=pk)
    
    admin_membership = get_publisher_admin(request, publisher)
    
    if not admin_membership:
        messages.error(request, "you do not have permission to review membership requests.")
        
        return redirect("publisher_detail", pk=publisher.pk)
    
    decision = request.POST.get("decision")
    
    if decision not in ["approve", "reject"]:
        messages.error(request, "invalid membership decision.")
        
        return redirect("publisher_membership_requests", pk=publisher.pk)
    
    try:
        with transaction.atomic():
            
            membership_request = MembershipRequest.objects.select_for_update().get(
                pk=request_id,
                membershup__publisher=publisher,
                request_type="join",
                status="pending",
                membership_isnull=False
            )
            
            membership = PublisherMembership.objects.select_for_update().get(
                pk=membership_request.membership_id,
                publisher=publisher,
            )
            
            if membership.status != "pending":
                messages.error(request, "this membership request is no longer pending.")
                
                return redirect("publisher_membership_requests", pk=publisher.pk)
            
            if decision == "approve":
                
                membership.status = "active"
                membership.role = "journalist"
                membership.left_at = None
                
                membership_request.status = "approved"
                
                messages.success(request, "Your request has been approved. ")
                
            else:
                
                membership.status == "rejected"
                
                membership_request.status = "rejected"
                
                messages.success(request, "Your request has been rejected")
                
            membership.pending_request = "join"
            membership.save()
            
            membership_request.reviewed_at = timezone.now()
            membership_request.reviewed_by = admin_membership.journalist
            membership_request.save()
            
    except MembershipRequest.DoesNotExist:
        messages.error(request, "this membership request could not be found or has already been reviewed.")
        
    except PublisherMembership.DoesNotExist:
        messages.error(request, "this associated membership could not be found")
            
    return redirect("publisher_membership_requests", pk=publisher.pk)


@login_required
@require_POST
def promote_member(request, pk, membership_id):
    
    publisher = get_object_or_404(Publisher, pk=pk)
    
    try:
        
        journalist_profile = request.user.journalist_profile
    
    except JournalistProfile.DoesNotExist:
        messages.error(request, "you need a admin profile to manage publisher membership. ")
        
        return redirect("publisher_detail", pk=publisher.pk)
    
    with transaction.atomic():
        
        publisher = Publisher.objects.select_for_update().get(pk=publisher.pk)
        
        admin_membership = PublisherMembership.objects.select_for_update().filter(
            publisher=publisher, 
            journalist=journalist_profile,
            role="admin",
            status="active"
        ).first()
        
        if not admin_membership:
            messages.error(request, "only a publisher admin can promotee members")
            
            return redirect("publisher_detail", pk=publisher.pk)
        
        membership = PublisherMembership.objects.select_for_update().filter(
            pk=membership_id,
            publisher=publisher,
            status="active"
        ).first()
        
        if not membership:
            messages.error(request, "the selected member could not be found")
            
            return redirect("publisher_members", pk=publisher.pk)
        
        if membership.role == "admin":
            messages.info(request, "this member is already an admin")
            
            return redirect("publisher_membership", pk=publisher.pk)
        
        if membership.pending_request == "leave":
            messages.error(request, "a member with a pending leave request cannot be promoted")
            
            return redirect("publisher_membership", pk=publisher.pk)
        
        membership.role = "admin"
        
        membership.save(update_fields=["role"])
        
        messages.success(request, f"{membership.journalist} has been promoted to admin")
        
    return redirect("publisher_members", pk=publisher.pk)


@login_required
@require_POST
def demmote_member(request, pk, membership_id):
    
    publisher = get_object_or_404(Publisher, pk=pk)
    
    new_role = request.POST.get("new_role")
    
    if new_role not in ["journal", "editor"]:
        messages.error(request, "invalid membership role selected.")
        
        return redirect("publisher_members", pk=publisher.pk)
    
    try:
        
        journalist_profile = request.user.journal_profile
        
    except JournalistProfile.DoesNotExist:
        messages.error(request, "you to be an admin to manage publisher membership")

        return redirect("publisher_detail", pk=publisher.pk)
    
    with transaction.atomic():
        
        publisher = Publisher.objects.select_for_update().get(pk=publisher.pk)
        
        admin_membership = PublisherMembership.objects.select_for_update().filter(
            publisher=publisher,
            journalist=journalist_profile,
            role="admin",
            status="active"
        ).first()
        
        if not admin_membership:
            messages.error(request, "omly a publisher admin can demote members")
            
            return redirect("publisher_detail", pk=publisher.pk)
        
        membership = PublisherMembership.objects.select_for_update().filter(
            pk=membership_id,
            publisher=publisher,
            status="active"
        ).first()
        
        if not membership:
            messages.error(request, "the selected member could not be found ")
            
            return redirect("publisher_members", pk=publisher.pk)
        
        if membership.pending_request == "leave":
            messages.error(request, "an admin with a pending leave request cannot change thier role")
            
            return redirect("publisher_members", pk=publisher.pk)
        
        other_admin_exists = PublisherMembership.objects.filter(
           publisher=publisher,
           role="admin",
           status="active"
        ).exclude(pk=membership.pk).exists()
        
        if not other_admin_exists:
            messages.error(request, 
                           "This admin cannot be demoted because they are the last active publisher admin. Promote another active member first.")
            
            return redirect("publisher_members", pk=publisher.pk)
        
        membership.role = new_role
        
        membership.save(update_fields=["role"])
        
        messages.success(request, f"{membership.journalist} has been demoted to {new_role}")
        
    return redirect("publisher_members", pk=publisher.pk)


@login_required
@require_POST
def request_to_leave(request, pk):
    
    publisher = get_object_or_404(Publisher, pk=pk)
    
    try:
        
        journalist_profile = request.user.journalist_profile
        
    except JournalistProfile.DoesNotExist:
        messages.error(request, "You need a membership to request to leave.")
        
        return redirect("publisher_detail", pk=publisher.pk)
    
    try:
        with transaction.atomic():
            
            publisher = Publisher.objects.select_for_update().get(pk=publisher.pk)
            
            is_cooling_down, cooldown_expires = membership_request_cooldown(journalist_profile, publisher)

            if is_cooling_down:
                messages.error(request,
                               f"You cannot submit another membership request yet. You can try again after {timezone.localtime(cooldown_expires):%d %B %Y at %H:%M}.")

                return redirect("organisations:publisher_detail", pk=publisher.pk)

            
            membership = PublisherMembership.objects.select_for_update().filter(
                publisher=publisher,
                journalist=journalist_profile,
                status="active"
            ).first()
            
            if membership is None:
                messages.error(request, "You are not an active member of this publisher.")
                
                return redirect("organisations:publisher_detail", pk=pk)
            
            if membership.role == "admin":
                messages.error(request, "You must be demoted from publisher admin before requesting to leave.")
                
                return redirect("publisher_detail", pk=pk)
            
            member_requests = MembershipRequest.objects.filter(
                membership=membership,
                status="pending").exists()
            
            if member_requests:
                messages.error(request, "you already have a pending membership request.")
                
                return redirect("publisher_detail", pk=pk)
            
            membership.pending_request = "leave"
            membership.save(update_fields=["pending_request"])
            
            MembershipRequest.objects.create(
                membership=membership,
                journalist=journalist_profile,
                publisher=publisher,
                request_type="leave",
                status="pending"
            )
            
        messages.success(request, f"Your request to leave {publisher.name} has been submitted.")
        
    except Publisher.DoesNotExist:
        messages.error(request, "Publisher not found")
        
    except IntegrityError:
        messages.error(request, "Your already have a pending membership request.")
        
    return redirect("publisher_detail", pk=pk)


@login_required
def publisher_leave_requests(request, pk):
    
    publisher = get_object_or_404(Publisher, pk=pk)
    
    admin_membership = get_publisher_admin(request, publisher)
    
    if not admin_membership:
        messages.error(request, "you do not have permission to review leave requests.")
        
        return redirect("publisher_detail", pk=publisher.pk)
    
    leave_requests = MembershipRequest.objects.filter(
        membership__publisher=publisher,
        request_type="leave",
        status="pending",
        membership__isnull=False
    ).select_related("membership",
                     "membership__journalist",
                     "membership__journalist__user")
    
    context = {"publisher":publisher, "leave_requests": leave_requests}
    
    return render(request, "publisher_leave_requests", context)


@login_required
@require_POST
def review_leave_request(request, pk, request_id):
    
    publisher = get_object_or_404(Publisher, pk=pk)
    
    decision = request.POST.get("decision")
    
    if decision not in ["approve", "reject"]:
        messages.error(request, "invaild leave request decision.")
        
        return redirect("publisher_leave_requests", pk=publisher.pk)
    
    try:
        
        journalist_profile = request.user.journalist_profile
        
    except JournalistProfile.DoesNotExist:
        messages.error(request, "you need a journalist profile")
        
        return redirect("publisher_detail", pk=publisher.pk)
    
    try:
        with transaction.atomic():
            
            publisher = Publisher.objects.select_for_update().get(pk=publisher.pk)
            
            admin_membership = PublisherMembership.objects.select_for_update().filter(
                publisher=publisher,
                journalist=journalist_profile,
                role="admin",
                status="active"
            ).first()
            
            if not admin_membership:
                messages.error(request, "only a publisher member can review leave requests.")
                
                return redirect("publisher_detail", pk=publisher.pk)
            
            membership_request = MembershipRequest.objects.select_for_update().get(
                pk=request_id,
                membership__publisher=publisher,
                request_type="leave",
                staus="pending",
                membership__isnull=False
                )
            
            membership = PublisherMembership.objects.select_for_update().get(
                pk=membership_request.membership_id,
                publisher=publisher
            )
            
            if (membership.status != "active" or membership.pending_request != "leave" or membership.role == "admin"):
                messages.error(request, "this leave request is no longer valid.")
                
                return redirect("publisher_leave_requests", pk=publisher.pk)
            
            if decision == "approve":
                
                membership.status = "inactive"
                membership.left_at = timezone.now()
                
                membership_request.status = "approved"
                
                messages.success(request, "the leave request has been approved.")
            
            else:
                
                membership_request.status = "rejected"
                messages.success(request, "the leave request has been rejected.")
                
                membership.pending_request = "join"
                membership.save(update_fields=["status", "left_at", "pending_request"])
                
                membership_request.reviewed_at = timezone.now()
                membership_request.reviews_by = admin_membership.journalist
                
                membership_request.save(update_fields=["status", "reviewed_at", "reviewed_by"])

    except MembershipRequest.DoesNotExist:
        messages.error(request, "the associated membership could not be found.")
        
    except PublisherMembership.DoesNotExist:
        messages.error(request, "this associated mebership could not be found.")
        
    return redirect("publisher_leave requests", pk=publisher.pk)


@login_required
@require_POST
def remove_member(request, pk, membership_id):
    
    journalist_profile = getattr(request.user, "journalist_profile", None)
    
    if journalist_profile is None:
        messages.error(request, "you must have a journalist profile.")
        
        return redirect("publisher_detail", pk=pk)
    
    try:
        with transaction.atomic():
            
            publisher = Publisher.objects.select_for_update().get(pk=pk)
            
            admin_membership = PublisherMembership.objects.select_for_update.filter(
                journalist=journalist_profile,
                publisher=publisher,
                role="admin",
                status="active"
            ).first()
            
            if admin_membership is None:
                messages.error(request, "only publisher admins can remove members.")
                
                return redirect("publisher_members", pk=pk)
            
            membership = PublisherMembership.objects.select_for_update().filter(
                pk=membership_id,
                publisher=publisher,
                status="active"
            ).first()
            
            if membership is None:
                messages.error(request, "membership not found")
                
                return redirect("publisher_members", pk=pk)
            
            if membership.role == "admin":
                
                other_admin_exists = PublisherMembership.objects.filter(
                    publisher=publisher,
                    role="admin",
                    status="active"
            ).exclude(pk=membership.pk).exists()
                
                if not other_admin_exists:
                    messages.error(request, "last active admin cannot be removed", pk=pk)
                    
                    return redirect("publisher_members", pk=pk)
                
            membership.status = "inactive"
            membership.left_at = timezone.now()
            membership.pending_request = "join"
            
            membership.save(update_fields=["status", "left_at", "pending_request"])
            
        messages.success(request, f"{membership.journalist} has been removed from {publisher.name}")
        
    except Publisher.DoesNotExist:
        messages.error(request, "publisher not found.")
        
    return redirect("publisher_members", pk=pk)


@login_required
def my_publisher_memberships(request):
    
    journalist_profile = getattr(request.user,"journalist_profile", None)
        
    if journalist_profile is None:
        messages.error(request, "you must have  journalist profile to view your publisher memberships")
        
        return redirect("home")
    
    memberships = PublisherMembership.objects.filter(
        journalist=journalist_profile).select_related("publiszher").order_by(-joined_at)

    return render(request,"my_publisher_membership.html", {"membership": membership})


@login_required
def my_membership_requests(request):
    
    journalist_profile = getattr(request.user, "journalist_profile", None)
    
    if journalist_profile is None:
        messages.error(request, "you must have a journalist profile to view your publisher memberships")
        
        return redirect("home")
    
    membership_requests = MembershipRequest.objects.filter(
        membership__journalist=journalist_profile
    ).select_related(
        "membership",
        "membership__publisher",
        "reviewed_by",
        "reviewed_by__user",
    ).order_by("-requested_at")

    return render(request, "my_membership_requests", {"membership_requests": membership_requests})


@login_required
@require_POST
def cancel_join_request(request, request_id):
    
    journalist_profile = getattr(request.user, "journalist_profile", None)
    
    if journalist_profile is None:
        messages.error(request, "you must have a journalist profile")
        
        return redirect("my_membership_requests")
    
    membership_request = MembershipRequest.objects.filter(
        pk=request_id,
        journalist= journalist_profile,
        request_type="join",
        status="pending"
    ).first()
    
    if membership_request is None:
        messages.error(request, "pending join request not found.")
        
        return redirect(my_membership_requests)
    
    try:
        with transaction.atomic():
            
            publisher = Publisher.objects.select_for_update().get(
                pk=membership_request.publisher_id
            )
            
            membership_request = MembershipRequest.objects.select_for_update().filter(
                pk=request_id,
                journalist=journalist_profile,
                publisher=publisher,
                request_type="join",
                status="pending"
            ).select_related("membership").first()
            
            if membership_request is None:
                messages.error(request, "this join request is No longer pending. ")
                
                return redirect("my_membership_requests")
            
            membership = membership_request.membership
            
            if membership is None or membership.status != "pending":
                messages.error(request, "the associated pending membership could not be found.")
                
                return redirect("my_membership_requests")
            
            if membership.pending_request != "join":
                messages.error(request, "this membership is not awaiting a join request.")
                
                return redirect("my_membership_requests")
            
            membership_request.status = "cancelled"
            membership_request.reviewd_at = timezone.now()
            
            membership_request.save(update_fields=["status", "reviewed_at"])
            
            membership.delete()
        
        messages.success(request, f"your request to join {publisher.name} has been cancelled.")
        
    except Publisher.DoesNotExist:
        messages.error(request, "publisher not found.")
        
    return redirect("my_mebership_requests")


@login_required
@require_POST
def cancel_leave_request(request, request_id):
    
    journalist_profile = getattr(request.user, "journalist_profile", None)
    
    if journalist_profile is None:
        messages.error(request, "you must have a journalist profile")
        
        return redirect("my_membership_requests")
    
    membership_request = MembershipRequest.objects.filter(
        pk=request_id,
        journalist=journalist_profile,
        request_type="leave",
        status="pendind"
    ).first()
    
    if membership_request is None:
        messages.error(request, "pending leave request not found.")
        
        return redirect("my_membership_requests")
    
    try:
        with transaction.atomic():
            
            publisher = Publisher.objects.select_for_update().get(pk=membership_request.publisher_id)
            
            membership_request = MembershipRequest.objects.select_for_update().filter(
                pk=request_id,
                journalist=journalist_profile,
                publisher=publisher,
                request_type="leave",
                status="pending"
            ).select_related("membership").first()
            
            if membership_request is None:
                messages.error(request, "this leave request is no longer pending.")
                
                return redirect("my_membership_requests")
            
            membership = membership_request.membership
            
            if membership is None or membership.status != "active":
                messages.error(request, "you must have an active membership to cancel a leave request.")
                
                return redirect("my_membership_requests")
            
            if membership.pending_request != "leave":
                messages.error(request, "this membership is not awaiting a leave request.")
                
                return redirect("my_membership_requests")
            
            membership.pending_request = "join"
            membership.save(update_fields=["pending_request"])
            
            membership_request.status = "cancelled"
            membership_request.reviewed_at = timezone.now()
            
            membership_request.save(update_fields=["status", "reviewed_at"])
            
        messages.success(request, f"Your request to leave {publisher.name} has been cancelled. Your membership remains active")
            
    except Publisher.DoesNotExist:
        messages.error(request, "Publisher not found.")
        
    return redirect("my_membership_requests")

