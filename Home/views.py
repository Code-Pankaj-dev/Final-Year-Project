from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.models import User
from AdminZone.models import (ContactModel, DonateBloodModel, RequestBloodModel, DonorRegisterModel, LoginModel)
from django.contrib.auth.decorators import login_required
from HospitalZone.models import Hospital
from DonorZone.models import Donor
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages


# ===========================
# Website Views
# ===========================

def home(request):
    return render(request, "index.html")


def about(request):
    return render(request, "About_Us.html")


def blood_availability(request):
    return render(request, "Blood_Availabilite.html")


def blood_center_directory(request):
    return render(request, "Blood_Center_Directory.html")


def camp_schedule(request):
    return render(request, "Camp_Schedule.html")


def donate(request):
    return render(request, "Donate_blood.html")


def request_blood(request):
    return render(request, "Request_Blood.html")


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