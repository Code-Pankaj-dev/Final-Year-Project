from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from django.utils import timezone

from .models import Hospital, BloodRequest


def get_current_hospital(request):
    aid = request.session.get('aid')
    if aid:
        hospital = Hospital.objects.filter(email=aid).first()
        if hospital:
            return hospital
    return Hospital.objects.first()


# ======================================
# Hospital Dashboard
# ======================================

def hospital_dashboard(request):
    if not request.session.has_key('aid'):
        return HttpResponse(
            "<script>alert('First Login as Hospital');window.location.href='/login/'</script>"
        )

    hospital = get_current_hospital(request)

    if request.method == "POST" and "update_profile" in request.POST:
        if hospital:
            hospital.hospital_name = request.POST.get("hospital_name", hospital.hospital_name)
            hospital.doctor_name = request.POST.get("doctor_name", hospital.doctor_name)
            hospital.phone = request.POST.get("phone", hospital.phone)
            hospital.district = request.POST.get("district", hospital.district)
            hospital.address = request.POST.get("address", hospital.address)
            hospital.save()
            return HttpResponse(
                "<script>alert('Hospital Profile Updated Successfully!');window.location.href='/hospital-dashboard/'</script>"
            )

    from AdminZone.models import BloodStock
    from AdminZone.views import ensure_initial_blood_stock
    ensure_initial_blood_stock()
    stocks = BloodStock.objects.order_by('blood_group')

    if hospital:
        requests = BloodRequest.objects.filter(hospital=hospital).order_by('-id')
    else:
        requests = BloodRequest.objects.none()

    approved_units = list(requests.filter(status__in=["Approved", "Fulfilled"]).values_list("units", flat=True))
    total_received = sum(approved_units) if approved_units else 0

    context = {
        "hospital": hospital,
        "stocks": stocks,
        "requests": requests,
        "today": timezone.now(),
        "total_requests": requests.count(),
        "approved_requests": requests.filter(status__in=["Approved", "Fulfilled"]).count(),
        "pending_requests": requests.filter(status="Pending").count(),
        "rejected_requests": requests.filter(status="Rejected").count(),
        "blood_units_received": total_received,
        "emergency_requests": requests.filter(priority="Emergency").count(),
    }

    return render(
        request,
        "HospitalPages/hospital_dashboard.html",
        context
    )


# ======================================
# Request Blood
# ======================================

def request_blood(request):
    if not request.session.has_key('aid'):
        return HttpResponse("<script>alert('First Login');window.location.href='/login/'</script>")
    hospital = get_current_hospital(request)
    if request.method == "POST":
        patient_name = request.POST.get("patient_name")
        blood_group = request.POST.get("blood_group")
        units = request.POST.get("units") or 1
        required_date = request.POST.get("required_date") or timezone.now().date()
        priority = request.POST.get("priority", "Normal")
        remarks = request.POST.get("remarks", "")
        if hospital:
            BloodRequest.objects.create(
                hospital=hospital,
                patient_name=patient_name,
                blood_group=blood_group,
                units=units,
                required_date=required_date,
                priority=priority,
                remarks=remarks,
                status="Pending"
            )
            return HttpResponse("<script>alert('Blood Request Submitted Successfully!');window.location.href='/hospital-dashboard/'</script>")
    return redirect("/hospital-dashboard/")


# ======================================
# Emergency Request
# ======================================

def emergency_request(request):
    if not request.session.has_key('aid'):
        return HttpResponse("<script>alert('First Login');window.location.href='/login/'</script>")
    hospital = get_current_hospital(request)
    if request.method == "POST":
        patient_name = request.POST.get("patient_name")
        blood_group = request.POST.get("blood_group")
        units = request.POST.get("units") or 1
        required_date = request.POST.get("required_date") or timezone.now().date()
        remarks = request.POST.get("remarks", "")
        if hospital:
            BloodRequest.objects.create(
                hospital=hospital,
                patient_name=patient_name,
                blood_group=blood_group,
                units=units,
                required_date=required_date,
                priority="Emergency",
                remarks=remarks,
                status="Pending"
            )
            return HttpResponse("<script>alert('Emergency Blood Request Submitted Successfully!');window.location.href='/hospital-dashboard/'</script>")
    return redirect("/hospital-dashboard/#emergency-section")


# ======================================
# Blood Availability
# ======================================

def blood_availability(request):
    return redirect("/hospital-dashboard/#stock-section")


# ======================================
# My Requests
# ======================================

def my_requests(request):
    return redirect("/hospital-dashboard/#requests-section")


# ======================================
# Request History
# ======================================

def request_history(request):
    return redirect("/hospital-dashboard/#requests-section")


# ======================================
# Notifications
# ======================================

def notifications(request):
    return redirect("/hospital-dashboard/#requests-section")


# ======================================
# Hospital Profile
# ======================================

def hospital_profile(request):
    return redirect("/hospital-dashboard/#profile-section")


# ======================================
# Settings
# ======================================

def settings(request):
    return redirect("/hospital-dashboard/#profile-section")


# ======================================
# Download Report
# ======================================

def download_report(request):
    return redirect("/hospital-dashboard/#requests-section")


# ======================================
# Logout
# ======================================

def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("/login/")
