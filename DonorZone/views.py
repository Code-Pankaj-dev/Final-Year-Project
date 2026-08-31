from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

from .models import (
    Donor,
    DonationHistory,
    DonorBloodRequest,
    DonorNotification
)


def get_current_donor(request):
    aid = request.session.get('aid')
    if aid:
        return Donor.objects.filter(email=aid).first()
    return None


# =========Donor Dashboard==========#

def donor_dashboard(request):
    if not request.session.has_key('aid'):
        return HttpResponse(
            "<script>alert('First Login as Donor');window.location.href='/login/'</script>"
        )

    donor = get_current_donor(request)
    if not donor:
        return HttpResponse(
            "<script>alert('Donor session invalid or account not found. Please login.');window.location.href='/login/'</script>"
        )

    if request.method == "POST" and "update_profile" in request.POST:
        if donor:
            donor.full_name = request.POST.get("full_name", donor.full_name)
            donor.blood_group = request.POST.get("blood_group", donor.blood_group)
            donor.mobile = request.POST.get("mobile", donor.mobile)
            donor.city = request.POST.get("city", donor.city)
            donor.address = request.POST.get("address", donor.address)
            donor.save()
            return HttpResponse(
                "<script>alert('Donor Profile Updated Successfully!');window.location.href='/donor-dashboard/'</script>"
            )

    from AdminZone.models import BloodStock
    from AdminZone.views import ensure_initial_blood_stock
    ensure_initial_blood_stock()
    stocks = BloodStock.objects.order_by('blood_group')

    if donor:
        donations = DonationHistory.objects.filter(donor=donor).order_by('-id')
        blood_requests = DonorBloodRequest.objects.filter(donor=donor).order_by('-id')
        notifications = DonorNotification.objects.filter(donor=donor).order_by('-id')[:6]
    else:
        donations = DonationHistory.objects.none()
        blood_requests = DonorBloodRequest.objects.none()
        notifications = DonorNotification.objects.none()

    context = {
        "donor": donor,
        "stocks": stocks,
        "today": timezone.now(),
        "donations": donations,
        "blood_requests": blood_requests,
        "notifications": notifications,
        "total_donations": donations.count(),
        "approved_donations": donations.filter(status__in=["Approved", "Completed"]).count(),
        "pending_donations": donations.filter(status="Pending").count(),
        "rejected_donations": donations.filter(status="Rejected").count(),
        "reward_points": donor.reward_points if donor else 0,
    }
    return render(
        request,
        "DonorPages/Donor_dashboard.html",
        context
    )


# ==========================================
# My Profile
# ==========================================

def my_profile(request):
    return redirect("/donor-dashboard/#profile-section")


# ==========================================
# Donate Blood (In-Portal Action)
# ==========================================

def donate_blood(request):
    if not request.session.has_key('aid'):
        return HttpResponse(
            "<script>alert('First Login as Donor');window.location.href='/login/'</script>"
        )

    donor = get_current_donor(request)
    if not donor:
        return HttpResponse(
            "<script>alert('Donor session invalid. Please login.');window.location.href='/login/'</script>"
        )
    if request.method == "POST":
        units = int(request.POST.get("units", 1))
        bg = request.POST.get("blood_group") or (donor.blood_group if donor else "O+")
        hospital_name = request.POST.get("hospital_name", "Campus Blood Center")
        donation_date = request.POST.get("donation_date") or timezone.now().date()
        remarks = request.POST.get("remarks", "Direct Portal Donation")

        if donor:
            DonationHistory.objects.create(
                donor=donor,
                donation_date=donation_date,
                hospital_name=hospital_name,
                units=units,
                blood_group=bg,
                status="Completed",
                remarks=remarks
            )
            donor.total_donations += 1
            donor.reward_points += 50
            donor.last_donation_date = timezone.now().date()
            donor.save()

            # Record Donor Notification
            DonorNotification.objects.create(
                donor=donor,
                title="Blood Donation Recorded! ❤️",
                message=f"Thank you for donating {units} unit(s) of {bg} at {hospital_name}. 50 Reward points credited."
            )

            # Increase Central Stock
            from AdminZone.models import BloodStock
            stock_item = BloodStock.objects.filter(blood_group=bg).first()
            if stock_item:
                stock_item.units += units
                stock_item.save()

            return HttpResponse(
                "<script>alert('Thank you! Your donation has been recorded in your Donor Portal. 50 Reward Points Added! ❤️');window.location.href='/donor-dashboard/'</script>"
            )

    return redirect("/donor-dashboard/#donate-section")


# ==========================================
# Donation History
# ==========================================

def donation_history(request):
    return redirect("/donor-dashboard/#donations-section")


# ==========================================
# Blood Requests (In-Portal Action)
# ==========================================

def blood_requests(request):
    if not request.session.has_key('aid'):
        return HttpResponse(
            "<script>alert('First Login as Donor');window.location.href='/login/'</script>"
        )

    donor = get_current_donor(request)
    if not donor:
        return HttpResponse(
            "<script>alert('Donor session invalid. Please login.');window.location.href='/login/'</script>"
        )
    if request.method == "POST":
        patient_name = request.POST.get("patient_name")
        bg = request.POST.get("blood_group")
        units = int(request.POST.get("units", 1))
        hospital_name = request.POST.get("hospital_name", "City Hospital")
        required_date = request.POST.get("required_date") or timezone.now().date()
        remarks = request.POST.get("remarks", "Emergency Need")

        if donor:
            DonorBloodRequest.objects.create(
                donor=donor,
                hospital_name=hospital_name,
                blood_group=bg,
                required_units=units,
                requested_date=required_date,
                status="Pending"
            )

            # Also create in AdminZone RequestBloodModel for admin review
            from AdminZone.models import RequestBloodModel
            RequestBloodModel.objects.create(
                blood_group=bg,
                units_needed=units,
                urgency="Emergency",
                patient_name=patient_name or "Emergency Requisition",
                required_by=required_date,
                contact_phone=donor.mobile,
                hospital_name=hospital_name,
                hospital_address=donor.city or donor.address,
                status="Pending"
            )

            DonorNotification.objects.create(
                donor=donor,
                title="Blood Requisition Submitted",
                message=f"Your blood request for {units} unit(s) of {bg} ({patient_name}) has been submitted for verification."
            )

            return HttpResponse(
                "<script>alert('Your blood request has been submitted to the Admin & Hospital Network successfully!');window.location.href='/donor-dashboard/'</script>"
            )

    return redirect("/donor-dashboard/#requests-section")


# ==========================================
# Blood Availability
# ==========================================

def blood_availability(request):
    return redirect("/donor-dashboard/#stock-section")


# ==========================================
# Notifications
# ==========================================

def notifications(request):
    return redirect("/donor-dashboard/#notifications-section")


# ==========================================
# Settings
# ==========================================

def settings(request):
    return redirect("/donor-dashboard/#profile-section")


# ==========================================
# Help & Support
# ==========================================

def help_support(request):
    return redirect("/donor-dashboard/#support-section")


# ==========================================
# Logout
# ==========================================

def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("/login/")


# ==========================================
# Blood Donation Certificate
# ==========================================

def donor_certificate(request, donation_id):
    if not request.session.has_key('aid'):
        return HttpResponse("<script>alert('First Login as Donor');window.location.href='/login/'</script>")

    donor = get_current_donor(request)
    if not donor:
        return HttpResponse("<script>alert('Donor session invalid. Please login.');window.location.href='/login/'</script>")

    donation = DonationHistory.objects.filter(id=donation_id, donor=donor).first()
    if not donation:
        return HttpResponse("<script>alert('Donation record not found or access denied.');window.location.href='/donor-dashboard/'</script>")

    cert_number = f"HC-CERT-{donation.donation_date.strftime('%Y')}-{donation.id:05d}"
    context = {
        "donor": donor,
        "donation": donation,
        "cert_number": cert_number,
        "issued_date": timezone.now().date(),
    }
    return render(request, "DonorPages/Certificate.html", context)



