from django import forms
from .models import Publisher, PublisherMembership, MembershipRequest
from users.utils.validators import validate_image_upload, validate_website_url


class PublisherRegistrationForm(forms.ModelForm):

    name = forms.CharField(max_length=200, label="Publisher name", help_text="Enter the official name of your news organisation.")

    description = forms.CharField(widgets=forms.Textarea(attrs={"rows": 4}), required=False, label="about the publisher")

    logo = forms.ImageField(required=False, validators=[validate_image_upload], help_text="Upload a JPEG, PNG or WEbP image (maximum 5 MB).")

    webiste = forms.URLField(required=False, label="Official website", validators=[validate_website_url], help_text="Enter your website address, including https://")

    class Meta:

        model = Publisher
        fields = [
            "name",
            "description",
            "logo",
            "email",
            "phone_number",
            "website",
            "region",
        ]


class PublisherUpdateForm(forms.ModelForm):
    
        name = forms.CharField(max_length=200, label="Publisher name", help_text="Enter the official name of your news organisation.")
   
        description = forms.CharField(widgets=forms.Textarea(attrs={"rows": 4}), required=False, label="about the publisher")
   
        logo = forms.ImageField(required=False, validators=[validate_image_upload], help_text="Upload a JPEG, PNG or WEbP image (maximum 5 MB).")
   
        webiste = forms.URLField(required=False, label="Official website", validators=[validate_website_url], help_text="Enter your website address, including https://")
        
        class Meta:
            model = Publisher
            fields = [
                "name",
                "description",
                "logo",
                "email",
                "phone_number",
                "website",
                "region",
            ]