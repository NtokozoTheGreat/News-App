from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from content.models import Region
from .models import UserProfile, JournalistProfile
from .utils.validators import validate_image_upload


class RegisterForm(UserCreationForm):

    email = forms.EmailField(label="", required=True, widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email"
            }
        )
    )

    first_name = forms.CharField(label="", max_length=150, required=True,
                                 widget=forms.TextInput(
                                    attrs={
                                        "class": "form-control",
                                        "placeholder": "First Name"
                                    }
                                    ))

    last_name = forms.CharField(
        label="",
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last Name"
            }
        )
    )

    date_of_birth = forms.DateField(
        label="",
        required=True,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date"
            }
        )
    )

    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=True,
        empty_label="Select your region",
        widget=forms.Select(
            attrs={
                "class": "form-control"
            }
        )
    )

    class Meta:
        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "date_of_birth",
            "region",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["username"].widget.attrs["placeholder"] = "User Name"
        self.fields["username"].label = ""
        self.fields["username"].help_text = (
            '<span class="form-text text-muted">'
            '<small>Required. 150 characters or fewer. '
            'Letters, digits and @/./+/-/_ only.</small>'
            '</span>'
        )

        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password1"].widget.attrs["placeholder"] = "Password"
        self.fields["password1"].label = ""
        self.fields["password1"].help_text = (
            '<ul class="form-text text-muted small">'
            "<li>Your password can't be too similar to your other personal information.</li>"
            "<li>Your password must contain at least 8 characters.</li>"
            "<li>Your password can't be a commonly used password.</li>"
            "<li>Your password can't be entirely numeric.</li>"
            "</ul>"
        )

        self.fields["password2"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm Password"
        self.fields["password2"].label = ""
        self.fields["password2"].help_text = (
            '<span class="form-text text-muted">'
            '<small>Enter the same password as before, for verification.</small>'
            '</span>'
        )

    def clean_email(self):
        email = self.cleaned_data["email"]

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email


class UpdateUserDetailsForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email"
            ]

        widgets = {

            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last-name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),

            }
        
    def clean_username(self):
        
        username = self.cleaned_data["username"]
        
        if User.objects.filter(
            username__iexact=username
        ).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("this username is already taken.")
        
        return username
    
    def clean_email(self):
        
        email = self.cleaned_data["email"]
        
        if User.objects.filter(
            email__exact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                "An account with this email already exits")
            
        return email


class UpdateUserProfileForm(forms.ModelForm):

    class Meta:

        model = UserProfile
        fields = [
            "date_of_birth",
            "region",
            "image",
            ]
        
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"class": "form-conrtol", "type": "date"}),
            "region": forms.Select(attrs={"class": "form-conrtol"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-conrtol"}),
            }
        
        def clean_image(self):
            
            image = self.cleaned_data.get("image")
            validate_image_upload("image")
            
            return image


class UpdateJournalistProfileForm(forms.ModelForm):

    class Meta:

        model = JournalistProfile
        fields = ["bio"]

        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-control",
                                         "rows": 4,
                                         "placeholder": "Tell readers about yourself...",
                                         }
                                  )
            }
