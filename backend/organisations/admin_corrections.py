from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction 
from django.contrib import messages
from .models import Publisher, PublisherMembership, AdministrativeCorrection, AdministrativeCorrectionReversal
from .forms import AdiministrativeCorrectionForm, AdmininstrativeCorrectionReversalForm
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .utils.validators import apply_membership_correction, validate_active_admin_rule
from django.utils.dateparse import parse_date


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
            
    return render(request, "create_administravtive_correction.html", {"form": form})


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
        
        corrections = corrections.filter(created_at__date__lte=date_to)
        
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


@user_passes_test(lambda user: user.is_superuser)
def reverse_administrative_correction(request, pk):
    
    correction = get_object_or_404(AdministrativeCorrection, pk=pk)
    
    if correction.membership_id is None:
        messages.error(reqest, "The membership asssociated with this correction no longer exists")
        
        return redirect("admininstrative_correction_deatil", pk=pk)
    
    if request.method == "POST":
        
        form = AdmininstrativeCorrectionReversalForm(request.POST)
        
        if form.is_valid():
            
            reason = form.cleaned_data["reason"].strip()
            
            if not reason:
                form.add_error("reason", "A reason is required.")
                
            else:
                try:
                    with transaction.atomic():
                        
                        membership_id = (AdministrativeCorrection.objects.values_list(
                            "membership_id", flat=True
                        ).get(pk=pk))
                        
                        if membership_id is None:
                            raise ValueError("This correction cannot be reversed, associated membership no longer exists.")
                        
                        
                        
                        publisher_id = (PublisherMembership.objects.values_list(
                            "publisher_id", flat=True
                        ).get(pk=membership_id))
                        
                        Publisher.objects.select_for_update().get(pk=publisher_id)
                        
                        membership = (PublisherMembership.objects.select_for_update().select_related(
                            "publisher",
                            "journalist__user"
                        ).get(pk=membership_id))
                        
                        correction = AdministrativeCorrection.objects.select_for_update().get(pk=pk)
                        
                        if correction.membership_id is None:
                            raise ValueError("This correction cannot be reversed, associated membership no longer exists.")
                        
                        if AdministrativeCorrectionReversal.objects.filter(original_correction=correction).exists():
                            raise ValueError("This correction has already been reversed")
                        
                        current_value = getattr(membership, correction.field_corrected)
                        
                        if current_value != correction.new_value:
                            raise ValueError("this membership has changed since the original correction. it cannot be automatically reversed.")
                        
                        validate_active_admin_rule(
                            membership,
                            correction.field_corrected,
                            correction.previous_value
                        )
                        
                        restored_value = correction.previous_value
                        
                        previous_value = apply_membership_correction(
                            membership,
                            correction.field_corrected,
                            restored_value
                        )
                        
                        AdministrativeCorrectionReversal.objects.create(
                            original_correction=correction,
                            membership=membership,
                            membership_reference=correction.membership_reference,
                            publisher_reference=correction.publisher_reference,
                            journalist_reference=correction.journalist_reference,
                            field_corrected=correction.field_corrected,
                            previous_value=previous_value,
                            restored_value=restored_value,
                            reason=reason,
                            reversed_by=request.user
                        )
                        
                    messages.success(request, "Administrative correction reversed successfully.")
                    
                    return redirect("administrative_correction_detail", pk=pk)

                except AdministrativeCorrection.DoesNotExist:
                    form.add_error(None, "The administrative correction could not be found.")
                    
                except Publisher.DoesNotExist:
                    form.add_error(None, "The membership associated with this correction no longer exists.")
                    
                except PublisherMembership.DoesNotExist:
                    form.add_error(None, "The membership associated with this correction no longer exists.")
                    
                except ValueError as error:
                    form.add_error(None, str(error))
                    
    else:
        form = AdmininstrativeCorrectionReversalForm()
        
    return render(request, "reverse_administrative_correction.html", {
        "form": form,
        "correction": get_object_or_404(
            AdministrativeCorrection, pk=pk
        )
    })


@user_passes_test(lambda user: user.is_superuser)
def administrative_correction_reversal_history(request):
    
    reversals = (AdministrativeCorrectionReversal.objects.select_related(
        "original_correction",
        "membership",
        "membership__publisher",
        "membership__journalist__user",
        "reversed_by"
    ).all())
    
    search_query = request.GET.get("search", "").strip()
    
    if search_query:
        
        reversals = reversals.filter(
            Q(membership_reference__icontains=search_query)
            | Q(publisher_reference__icontains=search_query)
            | Q(journalist_reference__icontains=search_query)
            | Q(reason__icontains=search_query)
        )
        
    original_correction = request.GET.get("original_correction", "").strip()
    
    if original_correction.isdigit():
        
        reversals = reversals.filter(original_correction_id=original_correction)
        
    reversed_by_id = request.GET.get("reversed_by", "").strip()
    
    if reversed_by_id.isdigit():
        
        reversals = reversals.filter(reversed_by_id=reversed_by_id)
        
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    
    parsed_date_from = parse_date(date_from) if date_from else None
    parsed_date_to = parse_date(date_to) if date_to else None
    
    date_error = None
    
    if date_from and parsed_date_from is None:
        
        date_error = "invalid start date"
        
    elif date_to and parsed_date_to is None:
        
        date_error = "Invalid end date"
        
    elif (parsed_date_from and parsed_date_to and parsed_date_from > parsed_date_to):
        
        date_error = "The start date cannot be later than the end date."
    
    if not date_error:
        
        if parsed_date_from:
            
            reversals = reversals.filter(created_at__date__gte=parsed_date_from)
            
        if parsed_date_to:
            
            reversals = reversals.filter(created_at__date__lte=parsed_date_to)
            
    context = {
        "reversals": reversals,
        "search_query": search_query,
        "original_correction": original_correction,
        "reversed_by_id": reversed_by_id,
        "date_from": date_from,
        "date_to": date_to,
        "date_error": date_error
    }

    return render(request, "administrative_correction_reversal_history.html", context)
