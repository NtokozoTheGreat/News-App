from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction 
from django.contrib import messages
from .models import Publisher, PublisherMembership, AdministrativeCorrection
from .forms import AdiministrativeCorrectionForm


@user_passes_test(lambda user: user.is_supersuer)
def create_administrative_correction(request):
    
    form = AdiministrativeCorrectionForm(request.POST)
    
    if form.is_valid():
        
        membership_id = form.cleaned_data["membership"].pk
        field_corrected = form.cleaned_data["field_corrected"]
        new_value = form.cleaned_data["new_value"]
        reason = form.cleaned_data["reason"].srtip()
        
        if not reason:
            form.add_error("reason", "A reason is required")
            
        else: 
            
            try:
                with transaction.atomic():
                    
                    membership = (PublisherMembership.objects.select_for_update().select_related(
                        "publisher", "journalist__user").get(pk=membership_id)
                    )
                    
                    Publisher.objects.select_for_update().get(pk=membership.publisher_id)
                    
                    previous_value = getattr(membership, field_corrected)
                    
                    if previous_value == new_value:
                        
                        form.add_error("new_value", "The selected value is already assigned.")
                        
                    else:
                        
                        setattr(membership, field_corrected, new_value)
                        
                        membership.save(update_fields=[field_corrected])
                        
                        journalist = membership.journalist.user
                        
                        membership_reference = (
                            f"membership #{membership.pk} - {journalist.username} at {membership.publisher.name}"
                        )
                        
                        AdministrativeCorrection.objects.create(
                            membership=membership,
                            membership_reference=membership_reference,
                            field_corrected=field_corrected,
                            previous_value= previous_value,
                            new_value=new_value,
                            reason=reason,
                            corrected_by=request.user
                        )
                        
                    if not form.errors:
                        messages.success(request, "administrative correction completed successfully.")
                        
                        return redirect("administravtive_correction_history")
                    
            except Publisher.DoesNotExist:
                form.add_error("membership", "the publisher associated with this membership no longer exists.")
               
        return render(request, "create_administravtive_correcrtion.html", {"form": form})

    else:
        
        form = AdiministrativeCorrectionForm()
        
    return render(request, "create_administravtive_correcrtion.html", {"form": form})

