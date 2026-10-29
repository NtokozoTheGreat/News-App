from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from .forms import PublisherRegistrationForm
from .models import PublisherMembership, Publisher
from django.contrib import messages


# Create your views here.


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

