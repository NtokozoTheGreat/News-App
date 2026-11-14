from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction 
from django.contrib import messages
from .models import Publisher, PublisherMembership, AdministrativeCorrection
from .forms import AdiministrativeCorrectionForm
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .utils.validators import apply_membership_correction, validate_active_admin_rule


@user_passes_test(lambda user: user.is_superuser)
def create_administrative_correction(request):
    
    if request.method == "POST":
        
        form = AdiministrativeCorrectionForm(request.POST)
        
        if form.is_valid():
            
            membership_id = form.cleaned_data["membership"].pk
            field_corrected = form.cleaned_data["field_corrected"]
            new_value = form.cleaned_data["new_value"]
            reason = form.cleaned_data["reason"].strip()
            
            if not reason:
                form.add_error("reason", "A reason is required")
                
            else:
                
                try:
                    with transaction.atomic():
                        
                        publisher_id = (PublisherMembership.objects.values_list(
                            "publisher_id", flat=True).get(pk=membership_id))
                        
                        Publisher.objects.select_for_update().get(pk=publisher_id)
                        
                        membership = (PublisherMembership.objects.select_for_update().select_related(
                            "publisher", "journalist__user").get(pk=membership_id)
                        )
                        
                        validate_active_admin_rule(membership, field_corrected, new_value)
                        
                        previous_value = apply_membership_correction(membership, field_corrected, new_value)
                        
                        journalist = membership.journalist.user
                                                 
                        membership_reference = (
                            f"membership #{membership.pk} - {journalist.username} at {membership.publisher.name}"
                        )
                        
                        AdministrativeCorrection.objects.create(
                            membership=membership,
                            membership_reference=membership_reference,
                            publisher_reference=membership.publisher.name,
                            journalist_reference=membership.journalist.user.username,
                            field_corrected=field_corrected,
                            previous_value=previous_value,
                            new_value=new_value,
                            reason=reason,
                            corrected_by=request.user
                        )
                            
                    messages.success(request, "administrative correction completed successfully.")
                    
                    return redirect("administravtive_correction_history")
                        
                except Publisher.DoesNotExist:
                    form.add_error("membership", "the publisher associated with this membership no longer exists.")
                    
                except PublisherMembership.DoesNotExist:
                    form.add_error("membership", "the selected mebership no longer exists.")
                    
                except ValueError as error:
                    form.add_error("new_value", str(error))

    else:
            
        form = AdiministrativeCorrectionForm()
            
    return render(request, "create_administravtive_correcrtion.html", {"form": form})


@user_passes_test(lambda user: user.is_superuser)
def administrative_correction_history(request):
    
    corrections = (AdministrativeCorrection.objects.select_related(
        "corrected_by",
        "membership",
        "membership__publisher",
        "membership__journalist__user"
    ).all()
    )

    search_query = request.GET.get("search", "").strip()
    
    if search_query:
        
        corrections = corrections.filter(
            Q(membership_reference__icontains=search_query)
            | Q(publisher_reference__icontains=search_query)
            | Q(journalist_reference__icontains=search_query)
            | Q(reason__icontains=search_query)
        )
        
        field_corrected = request.GET.get("field_corrected", "")
        
        if field_corrected in ["role", "status"]:
            
            corrections = corrections.filter(field_corrected=field_corrected)
            
        publisher = request.GET.get("publisher", "").strip()
        
        if publisher:
            
            corrections = corrections.filter(publisher_reference__iexact=publisher)
            
        journalist = request.GET.get("journalist", "").strip()
        
        if journalist:
            corrections = corrections.filter(journalist_reference__iexact=journalist)
            
        corrected_by_id = request.GET.get("corrected_by", "")
        
        if corrected_by_id.isdigit():
            
            corrections = corrections.filter(corrected_by_id=corrected_by_id)
            
        date_from = request.GET.get("date_from", "")
        date_to = request.GET.get("date_to", "")
        
        if date_from:
            
            corrections = corrections.filter(created_at__date__gte=date_from)
            
        if date_to:
            
            corrections = corrections.filter(created_at_date__lte=date_to)
            
        context = {
            "corrections": corrections,
            "search_query": search_query,
            "field_corrected": field_corrected,
            "publisher": publisher,
            "journalist": journalist,
            "corrected_by_id": corrected_by_id,
            "date_from": date_from,
            "date_to": date_to,
            }
        
        return render(request, "administrative_correction_hisory.html", context)
    
    
@user_passes_test(lambda user: user.is_superuser)
def administrative_correction_detail(request, pk):
    
    corrrection = get_object_or_404(AdministrativeCorrection.objects.select_related(
        "corrected_by",
        "membership",
        "membership__publisher",
        "membership__journalist__user"
    ),pk=pk)
    
    context = {"correction": corrrection}
    
    return render(request, "administrative_correction_detail.html", context)


