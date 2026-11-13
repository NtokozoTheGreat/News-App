from django import forms
from .models import Publisher, PublisherMembership, MembershipRequest
from users.utils.validators import validate_image_upload, validate_website_url


class PublisherRegistrationForm(forms.ModelForm):

    name = forms.CharField(max_length=200, label="Publisher name", help_text="Enter the official name of your news organisation.")

    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False, label="about the publisher")

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
   
        description = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False, label="about the publisher")
   
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
            

class AdiministrativeCorrectionForm(forms.Form):
    
    membership = forms.ModelChoiceField(queryset=PublisherMembership.objects.none(), label="Mebership")
    
    field_corrected = forms.ChoiceField(choices=[
        ("role", "Membership role"),
        ("status", "Membership status")
        ], label="Field to correct"
    )
    
    new_value = forms.ChoiceField(choices=[], label="New value")
    
    reason = forms.CharField(widget=forms.Textarea, label="Reason for correction")
    
    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        
        self.fields["membership"].queryset = (PublisherMembership.objects.select_related(
            "journalist__user",
            "publisher"
        ).filter(status="active"))
        
        field_corrected = (self.data.get("field_corrected") or self.initial.get("field_corrected"))
        
        if field_corrected == "role":
            
            self.fields["new_value"].choices = (PublisherMembership.ROLE_CHOICES)
            
        elif field_corrected == "status":
            
            self.fields["new_value"].choices = (PublisherMembership.STATUS_CHOICES)
