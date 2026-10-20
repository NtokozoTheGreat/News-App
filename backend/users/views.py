from django.shortcuts import render, redirect
from . import RegisterForm
from .models import UserProfile, JournalistProfile
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db import transaction, IntegrityError
from .forms import UpdateJournalistProfileForm, UpdateUserDetailsForm, UpdateUserProfileForm
from django.contrib.auth.decorators import login_required


# Create your views here.


def register_user(request):

    if request.user.is_authenticated:

            messages.info(request,"You are already logged in.")

            return redirect("home")

    if request.method=="POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            
            try:
                
                with transaction.atomic():
                    
                    user = form.save()
                    
                    UserProfile.objects.create(
                        user=user,
                        date_of_birth=form.cleaned_data['date_of_birth'],
                        region=form.cleaned_data['region']
                    )
            
            except IntegrityError:
                messages.error(request, "there was a problem creating your account. please try again")
                
            else: 
                login(request, user)
                   
                messages.success(request,"Your account has been created successfully.")
                
                return redirect('home')
            
        else:
            
            form = RegisterForm()
        
        return render(request, "user/register.html")


def login_user(request):
    
    if request.user.is_authenticated:
        
        messages.info(request,"You are already logged in.")
        
        return redirect("home")
    
    if request.method=="POST":
        
        username= request.POST.get('username')
        password= request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            
            login(request, user)
            
            messages.success(request,"You have successsfully logged in.")
            
            return redirect("home")
        
        else:
            messages.error(request,"invaild username or password.")
            
    return render(request, 'user_login.html')


def logout_user(request):
    
    if not request.user.is_authenticated:
        
        messages.info(request,"Your already logged out.")
        
    logout(request)
    messages.success(request,"you have successfully logged out")
    
    return redirect("home")


@login_required
def update_profile(request):

    user = request.user

    try:
        profile = user.profile

    except UserProfile.DoesNotExist:
        messages.error(request, "Your user profile could not be found.")

        return redirect("home")
    
    try:
        journalist = user.journalist_profile
        
    except JournalistProfile.DoesNotExist:
        journalist_profile = None
        
    if request.method == "POST":
        
        user_form = UpdateUserDetailsForm(request.POST, instance=user,)
        profile_form = UpdateUserProfileForm(request.POST, request.FILES, instance=profile,)
        journalist_form = UpdateJournalistProfileForm(request.POST, instance=journalist_profile)
        
        journalist_form = None
        
        if JournalistProfile is not None:
            
            journalist_form = UpdateJournalistProfileForm(
                request.POST, instance=journalist_profile,
            )
             
        forms_to_validate = [user_form, profile_form]
        
        if journalist_form is not None:
            forms_to_validate.append(journalist_form)    
            
        if all(form.is_valid() for form in forms_to_validate):
            with transaction.atomic():
                user_form.save()
                profile_form.save()
                
                if journalist_form is not None:
                    journalist_form.save()
                    
            messages.success(request, "Your profile has Update successfully.")
            return redirect("update_profile")
        
        messages.error(request, "Please correct the errors below")
        
    else:
        
        user_form = UpdateUserDetailsForm(instance=user)
        profile_form = UpdateUserProfileForm(instance=profile)
        
        journalist_form = None
        
        if journalist_profile is not None:
            journalist_form = UpdateJournalistProfileForm(instance=profile,)
    
    return render(request, "user/update_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "journalist_form": journalist_form
        })

@login_required
def become_journalist(request):
    
    if hasattr(request.user, "journalist_profile"):
        messages.info(
            request, "You already have a journalist_profile."
        )
        return redirect("home")
    
    if request.method == "POST":
        
        try:
            
            with transaction.atomic():
                JournalistProfile.objects.create(
                    user=request.user
                )
                
        except IntegrityError:
            
            messages.error(request, "We could'nt create your journalist profile. "
                          "please try again")
            
            return redirect("become_journalist")
        
        messages,success(request, "Your journalist profile has been created successfully.")
        
        return redirect("update_profile")
    
    return render(request, (request, "user/become_journalist.html"))


def delete_profile(request):
    pass