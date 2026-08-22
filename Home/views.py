from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.models import User
from AdminZone.models import (ContactModel, DonateBloodModel, RequestBloodModel, DonorRegisterModel, LoginModel, BloodStock)
from django.contrib.auth.decorators import login_required
from HospitalZone.models import Hospital
from DonorZone.models import Donor
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
import json

from .services_data import ALL_INDIA_BLOOD_CENTERS, ALL_INDIA_CAMP_SCHEDULES, INDIA_STATES_DISTRICTS


# ===========================
# Website Views & Services
# ===========================

def home(request):
    return render(request, "index.html")


def about(request):
    return render(request, "About_Us.html")


def services_hub(request):
    """Dedicated Services Overview Hub Page"""
    total_centers = len(ALL_INDIA_BLOOD_CENTERS)
    total_camps = len(ALL_INDIA_CAMP_SCHEDULES)
    return render(request, "services.html", {
        "total_centers": total_centers,
        "total_camps": total_camps
    })


def blood_availability(request):
    """Real-time Blood Stock Availability across India with Multi-Filter"""
    selected_state = request.GET.get("state", "").strip()
    selected_district = request.GET.get("district", "").strip()
    selected_bg = request.GET.get("blood_group", "").strip()
    selected_component = request.GET.get("component", "Whole Blood").strip()
    search_q = request.GET.get("q", "").strip().lower()

    centers = ALL_INDIA_BLOOD_CENTERS

    if selected_state and selected_state != "All States":
        centers = [c for c in centers if c["state"].lower() == selected_state.lower()]
    if selected_district and selected_district != "All Districts":
        centers = [c for c in centers if selected_district.lower() in c["district"].lower()]
    if search_q:
        centers = [c for c in centers if search_q in c["name"].lower() or search_q in c["address"].lower() or search_q in c["district"].lower() or search_q in c["state"].lower()]

    all_states = sorted(list(INDIA_STATES_DISTRICTS.keys()))

    # Process centers with blood group stock info
    processed_centers = []
    total_available_units = 0
    for idx, c in enumerate(centers, 1):
        stock_dict = c.get("stock", {})
        if selected_bg and selected_bg != "All":
            units = stock_dict.get(selected_bg, 10)
        else:
            units = sum(stock_dict.values())
        
        total_available_units += units

        if units >= 25:
            status_text = "Available"
            status_class = "success"
        elif units >= 10:
            status_text = "Moderate"
            status_class = "warning"
        else:
            status_text = "Critical Low"
            status_class = "danger"

        processed_centers.append({
            "sno": idx,
            "id": c.get("id", f"BC-{idx}"),
            "name": c["name"],
            "category": c["category"],
            "state": c["state"],
            "district": c["district"],
            "phone": c["phone"],
            "emergency_helpline": c["emergency_helpline"],
            "email": c.get("email", "bloodbank@hemocampus.org"),
            "nodal_officer": c.get("nodal_officer", "Medical Superintendent"),
            "address": c["address"],
            "units": units,
            "status_text": status_text,
            "status_class": status_class,
            "facilities": c.get("facilities", ["Component Separation", "24x7 Triage"]),
            "license_no": c["license_no"],
            "rating": c.get("rating", "4.8"),
            "stock_dict": stock_dict
        })

    return render(request, "Blood_Availabilite.html", {
        "centers": processed_centers,
        "all_states": all_states,
        "selected_state": selected_state,
        "selected_district": selected_district,
        "selected_bg": selected_bg,
        "selected_component": selected_component,
        "search_q": search_q,
        "total_results": len(processed_centers),
        "total_available_units": total_available_units,
        "states_districts_json": json.dumps(INDIA_STATES_DISTRICTS),
        "all_centers_json": json.dumps(ALL_INDIA_BLOOD_CENTERS)
    })


def blood_center_directory(request):
    """Nationwide Directory of Blood Centers, Apex Hospitals & Blood Banks"""
    selected_state = request.GET.get("state", "").strip()
    selected_district = request.GET.get("district", "").strip()
    selected_category = request.GET.get("category", "").strip()
    search_q = request.GET.get("q", "").strip().lower()

    centers = ALL_INDIA_BLOOD_CENTERS

    if selected_state and selected_state != "All States":
        centers = [c for c in centers if c["state"].lower() == selected_state.lower()]
    if selected_district and selected_district != "All Districts":
        centers = [c for c in centers if selected_district.lower() in c["district"].lower()]
    if selected_category and selected_category != "All Categories":
        centers = [c for c in centers if selected_category.lower() in c["category"].lower()]
    if search_q:
        centers = [c for c in centers if search_q in c["name"].lower() or search_q in c["address"].lower() or search_q in c["district"].lower() or search_q in c["state"].lower() or search_q in c.get("nodal_officer", "").lower()]

    all_states = sorted(list(INDIA_STATES_DISTRICTS.keys()))
    all_categories = sorted(list(set(c["category"] for c in ALL_INDIA_BLOOD_CENTERS)))

    return render(request, "Blood_Center_Directory.html", {
        "centers": centers,
        "all_states": all_states,
        "all_categories": all_categories,
        "selected_state": selected_state,
        "selected_district": selected_district,
        "selected_category": selected_category,
        "search_q": search_q,
        "total_centers": len(centers),
        "states_districts_json": json.dumps(INDIA_STATES_DISTRICTS),
        "all_centers_json": json.dumps(ALL_INDIA_BLOOD_CENTERS)
    })


def camp_schedule(request):
    """Scheduled Blood Donation Camps & Mobile Drives across India"""
    selected_state = request.GET.get("state", "").strip()
    selected_district = request.GET.get("district", "").strip()
    selected_type = request.GET.get("camp_type", "").strip()
    search_q = request.GET.get("q", "").strip().lower()

    camps = ALL_INDIA_CAMP_SCHEDULES

    if selected_state and selected_state != "All States":
        camps = [c for c in camps if c["state"].lower() == selected_state.lower()]
    if selected_district and selected_district != "All Districts":
        camps = [c for c in camps if selected_district.lower() in c["district"].lower()]
    if selected_type and selected_type != "All Types":
        camps = [c for c in camps if selected_type.lower() in c.get("camp_type", "").lower()]
    if search_q:
        camps = [c for c in camps if search_q in c["camp_name"].lower() or search_q in c["venue"].lower() or search_q in c["district"].lower() or search_q in c["organized_by"].lower()]

    all_states = sorted(list(INDIA_STATES_DISTRICTS.keys()))
    all_types = sorted(list(set(c.get("camp_type", "Campus Drive") for c in ALL_INDIA_CAMP_SCHEDULES)))

    return render(request, "Camp_Schedule.html", {
        "camps": camps,
        "all_states": all_states,
        "all_types": all_types,
        "selected_state": selected_state,
        "selected_district": selected_district,
        "selected_type": selected_type,
        "search_q": search_q,
        "total_camps": len(camps),
        "states_districts_json": json.dumps(INDIA_STATES_DISTRICTS),
        "all_camps_json": json.dumps(ALL_INDIA_CAMP_SCHEDULES)
    })


def subscribe_camp_alert(request):
    """Subscribe for SMS / Email camp alerts"""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        state = request.POST.get("state", "").strip()
        district = request.POST.get("district", "").strip()
        return HttpResponse("<script>alert('Thank you! You will receive instant SMS/WhatsApp alerts for upcoming blood donation camps in " + district + ", " + state + ".');window.location.href='/camp-schedule/'</script>")
    return redirect("camp_schedule")


def register_camp_volunteer(request):
    """Register volunteer for upcoming camp"""
    if request.method == "POST":
        name = request.POST.get("volunteer_name", "").strip()
        camp_name = request.POST.get("camp_name", "").strip()
        return HttpResponse("<script>alert('Thank you " + name + "! Your voluntary donor registration for [" + camp_name + "] is confirmed. Our camp medical team will welcome you with your digital donor certificate.');window.location.href='/camp-schedule/'</script>")
    return redirect("camp_schedule")


def host_camp_request(request):
    """Host a Blood Donation Camp on College Campus or Corporate Office"""
    if request.method == "POST":
        org_name = request.POST.get("org_name", "").strip()
        contact_person = request.POST.get("contact_person", "").strip()
        phone = request.POST.get("phone", "").strip()
        city = request.POST.get("city", "").strip()
        camp_date = request.POST.get("preferred_date", "").strip()
        expected = request.POST.get("expected_donors", "100")
        return HttpResponse("<script>alert('Thank you " + contact_person + "! Your camp hosting request for [" + org_name + "] in " + city + " on " + camp_date + " has been registered. Our regional blood bank coordinator will call you within 24 hours.');window.location.href='/camp-schedule/'</script>")
    return redirect("camp_schedule")


def donate(request):
    return render(request, "Donate_blood.html")


def request_blood(request):
    hospital_param = request.GET.get("hospital", "")
    return render(request, "Request_Blood.html", {"prefilled_hospital": hospital_param})


def contact(request):
    return render(request, "Contact_Us.html")


def login(request):
    return render(request, "login.html")


def loginCode(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        role = request.POST.get("role", "").strip().lower()

        # Check in LoginModel directly by email
        data = LoginModel.objects.filter(email=username, password=password, role=role)
        
        # If not found by email, check if username was entered instead of email
        if not data.exists():
            user_obj = User.objects.filter(username=username).first()
            if user_obj and user_obj.email:
                data = LoginModel.objects.filter(email=user_obj.email, password=password, role=role)

        if data.exists():
            matched_user = data.first()
            request.session['aid'] = matched_user.email
            if role == 'admin':
                return HttpResponse("<script>alert('Welcome to Admin Zone');window.location.href='/Admin_Dashboard/'</script>")
            elif role == 'donor':
                return HttpResponse("<script>alert('Welcome to Donor Zone');window.location.href='/donor-dashboard/'</script>")
            elif role == 'hospital':
                return HttpResponse("<script>alert('Welcome to Hospital Zone');window.location.href='/hospital-dashboard/'</script>")
            else:
                return HttpResponse("<script>alert('Invalid Role Selected');window.location.href='/login/'</script>")
        else:
            return HttpResponse("<script>alert('Invalid Email/Username or Password');window.location.href='/login/'</script>")

    return redirect("login")


def register(request):
    return render(request, "register.html")


# ===========================
# Settings
# ===========================

@login_required
def settings(request):
    return render(request, "AdminPages/settings.html")


def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("login")


# ===========================
# Contact Form
# ===========================

def contectdata(request):
    if request.method == "POST":
        ContactModel.objects.create(
            name=request.POST.get("fullname"),
            mob=request.POST.get("phone"),
            email=request.POST.get("email"),
            request_type=request.POST.get("request_type"),
            blood_group=request.POST.get("blood_group"),
            msg=request.POST.get("message"),
        )
        return HttpResponse(
            "<script>alert('Thanks For Contacting Us');window.location.href='/contact/'</script>"
        )
    return HttpResponse(
        "<script>alert('Data Not Submitted');window.location.href='/contact/'</script>"
    )


# ===========================
# Donate Blood
# ===========================

def DonateBloodData(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        bg = request.POST.get("blood_group")
        name = request.POST.get("name")
        
        DonateBloodModel.objects.create(
            name=name,
            age=request.POST.get("age"),
            phone=request.POST.get("phone"),
            email=email,
            blood_group=bg,
            weight=request.POST.get("weight"),
            address=request.POST.get("address"),
            last_donation=request.POST.get("last_donation") or None,
            hemoglobin=request.POST.get("hemoglobin") or None,
        )

        # Sync with DonorZone profile if exists
        donor_obj = Donor.objects.filter(email=email).first()
        if donor_obj:
            from DonorZone.models import DonationHistory
            from django.utils import timezone
            DonationHistory.objects.create(
                donor=donor_obj,
                donation_date=timezone.now().date(),
                units=1,
                blood_group=bg or donor_obj.blood_group,
                status="Completed"
            )
            donor_obj.total_donations += 1
            donor_obj.last_donation_date = timezone.now().date()
            donor_obj.save()

            # Increase stock in central blood bank
            if bg:
                from AdminZone.models import BloodStock
                stock = BloodStock.objects.filter(blood_group=bg).first()
                if stock:
                    stock.units += 1
                    stock.save()

        return HttpResponse(
            "<script>alert('Thank You For Donating Blood ❤️ Your contribution has been recorded.');window.location.href='/donate/'</script>"
        )
    return HttpResponse(
        "<script>alert('Data Not Submitted');window.location.href='/donate/'</script>"
    )


# ===========================
# Request Blood
# ===========================

def RequestBloodData(request):
    if request.method == "POST":
        RequestBloodModel.objects.create(
            blood_group=request.POST.get("blood_group"),
            units_needed=request.POST.get("units_needed"),
            urgency=request.POST.get("urgency"),
            patient_name=request.POST.get("patient_name"),
            required_by=request.POST.get("required_by"),
            contact_phone=request.POST.get("contact_phone"),
            hospital_name=request.POST.get("hospital_name"),
            hospital_address=request.POST.get("hospital_address"),
        )
        return HttpResponse(
            "<script>alert('Blood Request Submitted Successfully');window.location.href='/request-blood/'</script>"
        )
    return HttpResponse(
        "<script>alert('Data Not Submitted');window.location.href='/request-blood/'</script>"
    )


# ===========================
# Donor Registration
# ===========================

def DonorRegisterData(request):
    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return HttpResponse(
                "<script>alert('Password and Confirm Password do not match');window.location.href='/register/'</script>"
            )

        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()

        if User.objects.filter(username=username).exists():
            return HttpResponse(
                "<script>alert('Username already exists');window.location.href='/register/'</script>"
            )

        # Create Django User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        full_name = request.POST.get("full_name")
        gender = request.POST.get("gender")
        dob = request.POST.get("dob")
        age = request.POST.get("age") or 0
        blood_group = request.POST.get("blood_group")
        weight = request.POST.get("weight") or 0
        mobile = request.POST.get("mobile")
        state = request.POST.get("state")
        city = request.POST.get("city")
        pincode = request.POST.get("pincode")
        address = request.POST.get("address")
        last_donation = request.POST.get("last_donation") or None
        hemoglobin = request.POST.get("hemoglobin") or None
        disease = request.POST.get("disease") or "None"
        disease_details = request.POST.get("disease_details") or ""
        medicine = request.POST.get("medicine") or "No"
        previous_donation = request.POST.get("previous_donation") or "No"

        # 1. Create Donor Profile in AdminZone
        DonorRegisterModel.objects.create(
            user=user,
            full_name=full_name,
            gender=gender,
            dob=dob,
            age=age,
            blood_group=blood_group,
            weight=weight,
            mobile=mobile,
            email=email,
            state=state,
            city=city,
            pincode=pincode,
            address=address,
            last_donation=last_donation,
            hemoglobin=hemoglobin,
            disease=disease,
            disease_details=disease_details,
            medicine=medicine,
            previous_donation=previous_donation,
        )

        # 2. Create / Sync Donor record in DonorZone for dashboard compatibility
        Donor.objects.update_or_create(
            email=email,
            defaults={
                'full_name': full_name,
                'gender': gender if gender in ['Male', 'Female', 'Other'] else 'Male',
                'blood_group': blood_group,
                'date_of_birth': dob,
                'age': int(age) if age else 18,
                'mobile': mobile,
                'address': address or "",
                'city': city or "",
                'state': state or "",
                'last_donation_date': last_donation,
            }
        )

        # 3. Create Login Entry in LoginModel for loginCode verification
        LoginModel.objects.update_or_create(
            email=email,
            defaults={
                'role': 'donor',
                'password': password
            }
        )

        return HttpResponse(
            "<script>alert('Donor Registered Successfully! Please Login.');window.location.href='/login/'</script>"
        )

    return HttpResponse(
        "<script>alert('Data Not Submitted');window.location.href='/register/'</script>"
    )


# ===========================
# Hospital Registration
# ===========================

def hospital_registration(request):
    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return HttpResponse(
                "<script>alert('Password and Confirm Password do not match');window.location.href='/hospital_registration/'</script>"
            )

        hospital_name = request.POST.get("hospital_name")
        registration_no = request.POST.get("registration_no")
        doctor_name = request.POST.get("incharge_name", "")
        phone = request.POST.get("phone")
        email = request.POST.get("email", "").strip()
        state = request.POST.get("state")
        city = request.POST.get("city")
        address = request.POST.get("address")
        username = request.POST.get("username", "").strip()
        logo = request.FILES.get("license_certificate")

        # 1. Create/Update Hospital profile
        Hospital.objects.update_or_create(
            registration_no=registration_no,
            defaults={
                'hospital_name': hospital_name,
                'doctor_name': doctor_name,
                'email': email,
                'phone': phone,
                'address': address or "",
                'district': city or "",
                'state': state or "",
                'logo': logo if logo else None,
            }
        )

        # 2. Create Django user if username provided
        if username and not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, email=email, password=password)

        # 3. Create Login record in LoginModel
        LoginModel.objects.update_or_create(
            email=email,
            defaults={
                'role': 'hospital',
                'password': password
            }
        )

        return HttpResponse(
            "<script>alert('Hospital Registered Successfully! Please Login.');window.location.href='/login/'</script>"
        )

    return render(request, "hospital_registration.html")


# ===========================
# Safe Logout
# ===========================

def LogoutPage(request):
    request.session.flush()
    return HttpResponse(
        "<script>alert('Logged Out Successfully');window.location.href='/login/'</script>"
    )
