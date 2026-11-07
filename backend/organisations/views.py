from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from .forms import PublisherRegistrationForm, PublisherUpdateForm
from .models import PublisherMembership, Publisher, MembershipRequest
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from users.models import JournalistProfile

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
        journalist=journalis_porfile,
        role="admin",
        status="active"
    ).exists()
    
    if not is_admin:
        messages.error(request,"Only an admin can update publisher details.")
        
        return redirect("publisher_details" pk =publisher.pk)
    
    if request.method == "POST":
        form = PublisherRegistrationForm(request.POST, request.FILES, instance=publisher)
        
        if form.is_valid():
            form.save()
            
            messages.success(request, "Publisher details updated successfully")
            return redirect("publisher_detail", pk=publisher.pk,)
            
    else:
        form = PublisherRegistrationForm(instance=publisher)
        
    return render(request, "update_publisher"{"form":form, "publisher": publisher})


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

    with transaction.atomic():
        
        membership, created = publisher.memberships.get_or_create(
            journalist=journalist_profile,
            defaults={
                "role": "journalist"
                "status": "pending"
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
        
        membership.status = "pending"
        membership.pending_request = "join"
        membership.save(update_feilds=["status", "pending_requests"])
        
        MembershipRequest.objects.create(membership=membership, request_type="join")
        
    messages.success(request, "your request to join this publisher has been submitted.")
    
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

def review_membership_request(request,pk , request_id):
    
    publisher = get_object_or_404(Publisher,pk=pk)
    
    admin_membership = get_publisher_admin(request, publisher)
    
    if not admin_membership:
        messages.error(request, "you do not have permission to review membrship requests.")
        
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
            messages.error(request,"only a publisher admin can promotee members")
            
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
    
    pass

