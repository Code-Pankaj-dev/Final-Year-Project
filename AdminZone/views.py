from django.shortcuts import render, redirect, HttpResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password

from AdminZone.models import (
    ContactModel,
    DonateBloodModel,
    RequestBloodModel,
    DonorRegisterModel,
    LoginModel,
    BloodStock
)
from DonorZone.models import Donor, DonationHistory, DonorBloodRequest
from HospitalZone.models import Hospital, BloodRequest


def ensure_initial_blood_stock():
    """Seed initial blood stock for all groups if not present."""
    groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    default_units = {'A+': 14, 'A-': 4, 'B+': 18, 'B-': 3, 'AB+': 7, 'AB-': 2, 'O+': 22, 'O-': 5}
    for g in groups:
        BloodStock.objects.get_or_create(
            blood_group=g,
            defaults={'units': default_units.get(g, 10)}
        )


def check_admin_session(request):
    """Ensure user is logged in as admin."""
    return request.session.get('aid')


# ==========================================
# 1. Admin Dashboard
# ==========================================
def dashboard(request):
    if not check_admin_session(request):
        return HttpResponse("<script>alert('First Login as Admin');window.location.href='/login/'</script>")

    ensure_initial_blood_stock()

    # Aggregate counts
    total_donors = DonorRegisterModel.objects.count()
    total_hospitals = Hospital.objects.count()
    
    # Combined requests
    hospital_requests_count = BloodRequest.objects.count()
    public_requests_count = RequestBloodModel.objects.count()
    total_requests = hospital_requests_count + public_requests_count

    pending_hospital_req = BloodRequest.objects.filter(status='Pending').count()
    pending_public_req = RequestBloodModel.objects.filter(status='Pending').count()
    pending_requests = pending_hospital_req + pending_public_req

    total_stock_units = BloodStock.objects.aggregate(total=Sum('units'))['total'] or 0

    # Recent Donors & Requests
    recent_donors = DonorRegisterModel.objects.order_by('-id')[:6]
    recent_hospital_req = BloodRequest.objects.order_by('-id')[:5]

    # Blood Stock levels
    stocks = BloodStock.objects.order_by('blood_group')

    context = {
        'total_donors': total_donors,
        'total_hospitals': total_hospitals,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'total_stock_units': total_stock_units,
        'recent_donors': recent_donors,
        'recent_requests': recent_hospital_req,
        'stocks': stocks,
        'admin_email': request.session.get('aid', 'Admin'),
    }
    return render(request, "AdminPages/Admin_Dashboard.html", context)


def admin_master(request):
    return render(request, "AdminPages/AdminMaster.html")


# ==========================================
# 2. Blood Stock Management
# ==========================================
def blood_stock(request):
    if not check_admin_session(request):
        return HttpResponse("<script>alert('First Login as Admin');window.location.href='/login/'</script>")

    ensure_initial_blood_stock()

    if request.method == "POST":
        action_type = request.POST.get("action_type", "quick_adjust")
        blood_group = request.POST.get("blood_group")

        if action_type == "add_stock":
            units_to_add = int(request.POST.get("units", 1))
            stock_item, _ = BloodStock.objects.get_or_create(blood_group=blood_group)
            stock_item.units += units_to_add
            stock_item.save()
            return HttpResponse(
                f"<script>alert('Successfully added {units_to_add} units to {blood_group}!');window.location.href='/Blood_Stock/'</script>"
            )

        elif action_type == "quick_adjust":
            stock_item, _ = BloodStock.objects.get_or_create(blood_group=blood_group)
            if "delta" in request.POST:
                delta = int(request.POST.get("delta", 0))
                stock_item.units = max(0, stock_item.units + delta)
            elif "new_total" in request.POST:
                new_total = int(request.POST.get("new_total", 0))
                stock_item.units = max(0, new_total)
            stock_item.save()
            return HttpResponse(
                f"<script>alert('Updated {blood_group} stock to {stock_item.units} units!');window.location.href='/Blood_Stock/'</script>"
            )

    stocks = BloodStock.objects.order_by('blood_group')
    total_units = sum(s.units for s in stocks)
    critical_count = sum(1 for s in stocks if s.units < 5)

    context = {
        'stocks': stocks,
        'total_units': total_units,
        'total_stock_units': total_units,
        'critical_count': critical_count,
    }
    return render(request, "AdminPages/Blood_Stock.html", context)


# ==========================================
# 3. Manage Donors
# ==========================================
def manage_donors(request):
    if not check_admin_session(request):
        return HttpResponse("<script>alert('First Login as Admin');window.location.href='/login/'</script>")

    blood_filter = request.GET.get('blood_group', '').strip()
    status_filter = request.GET.get('status', '').strip()
    search_q = (request.GET.get('q', '') or request.GET.get('search', '')).strip()

    donors = DonorRegisterModel.objects.all().order_by('-id')

    if blood_filter:
        donors = donors.filter(blood_group=blood_filter)
    if status_filter:
        donors = donors.filter(status__iexact=status_filter)
    if search_q:
        donors = donors.filter(
            full_name__icontains=search_q
        ) | donors.filter(
            email__icontains=search_q
        ) | donors.filter(
            city__icontains=search_q
        ) | donors.filter(
            mobile__icontains=search_q
        )

    total_count = DonorRegisterModel.objects.count()
    approved_count = DonorRegisterModel.objects.filter(status__iexact='Approved').count()
    pending_count = DonorRegisterModel.objects.filter(status__iexact='Pending').count()
    rejected_count = DonorRegisterModel.objects.filter(status__iexact='Rejected').count()

    context = {
        'donors': donors,
        'total_count': total_count,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
        'selected_blood': blood_filter,
        'selected_status': status_filter,
        'search_q': search_q,
        'query': search_q,
    }
    return render(request, "AdminPages/Manage_Donors.html", context)


def admin_action_donor(request, donor_id, action):
    if not check_admin_session(request):
        return HttpResponse("<script>alert('First Login as Admin');window.location.href='/login/'</script>")

    donor = DonorRegisterModel.objects.filter(id=donor_id).first()
    if not donor:
        return HttpResponse("<script>alert('Donor record not found');window.location.href='/Manage_Donors/'</script>")

    if action == 'approve':
        donor.status = 'Approved'
        donor.save()
        # Also sync to Donor in DonorZone
        Donor.objects.update_or_create(
            email=donor.email,
            defaults={
                'full_name': donor.full_name,
                'blood_group': donor.blood_group,
                'date_of_birth': donor.dob,
                'age': donor.age,
                'mobile': donor.mobile,
                'city': donor.city,
                'state': donor.state,
                'address': donor.address,
            }
        )
        return HttpResponse("<script>alert('Donor Approved Successfully!');window.location.href='/Manage_Donors/'</script>")

    elif action == 'reject':
        donor.status = 'Rejected'
        donor.save()
        return HttpResponse("<script>alert('Donor Rejected!');window.location.href='/Manage_Donors/'</script>")

    elif action == 'delete':
        donor.delete()
        return HttpResponse("<script>alert('Donor Record Deleted!');window.location.href='/Manage_Donors/'</script>")

    return redirect('/Manage_Donors/')


# ==========================================
# 4. Manage Requests
# ==========================================
def manage_request(request):
    if not check_admin_session(request):
        return HttpResponse("<script>alert('First Login as Admin');window.location.href='/login/'</script>")

    q = request.GET.get('q', '').strip()
    blood_group = request.GET.get('blood_group', '').strip()
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()

    hospital_requests = BloodRequest.objects.select_related('hospital').all().order_by('-id')
    public_requests = RequestBloodModel.objects.all().order_by('-id')

    if q:
        hospital_requests = hospital_requests.filter(
            patient_name__icontains=q
        ) | hospital_requests.filter(
            hospital__hospital_name__icontains=q
        ) | hospital_requests.filter(
            remarks__icontains=q
        )
        public_requests = public_requests.filter(
            patient_name__icontains=q
        ) | public_requests.filter(
            hospital_name__icontains=q
        )
    if blood_group:
        hospital_requests = hospital_requests.filter(blood_group=blood_group)
        public_requests = public_requests.filter(blood_group=blood_group)
    if status:
        hospital_requests = hospital_requests.filter(status__iexact=status)
        public_requests = public_requests.filter(status__iexact=status)
    if priority:
        hospital_requests = hospital_requests.filter(priority__iexact=priority)
        public_requests = public_requests.filter(urgency__iexact=priority)

    total_hospital_req = hospital_requests.count()
    public_req_count = public_requests.count()
    total_count = total_hospital_req + public_req_count

    context = {
        'hospital_requests': hospital_requests,
        'public_requests': public_requests,
        'total_count': total_count,
        'total_requests': total_count,
        'pending_requests': hospital_requests.filter(status='Pending').count() + public_requests.filter(status='Pending').count(),
        'approved_requests': hospital_requests.filter(status='Approved').count() + public_requests.filter(status='Approved').count(),
        'emergency_count': hospital_requests.filter(priority='Emergency').count() + public_requests.filter(urgency='Emergency').count(),
        'query': q,
        'selected_group': blood_group,
        'selected_status': status,
        'selected_priority': priority,
    }
    return render(request, "AdminPages/Manage_Requests.html", context)


def admin_action_request(request, req_id, action):
    if not check_admin_session(request):
        return HttpResponse("<script>alert('First Login as Admin');window.location.href='/login/'</script>")

    req = BloodRequest.objects.filter(id=req_id).first()
    if not req:
        # Check in RequestBloodModel
        req_pub = RequestBloodModel.objects.filter(id=req_id).first()
        if req_pub:
            if action in ['approve', 'priority']:
                req_pub.status = 'Approved'
            elif action == 'reject':
                req_pub.status = 'Rejected'
            elif action == 'fulfill':
                req_pub.status = 'Fulfilled'
            req_pub.save()
            return HttpResponse(f"<script>alert('Request updated to {req_pub.status}!');window.location.href='/Manage_Request/'</script>")
        return HttpResponse("<script>alert('Request not found');window.location.href='/Manage_Request/'</script>")

    if action == 'approve':
        req.status = 'Approved'
        req.save()
    elif action == 'priority':
        req.status = 'Approved'
        req.priority = 'Emergency'
        req.save()
    elif action == 'reject':
        req.status = 'Rejected'
        req.save()
    elif action == 'fulfill':
        req.status = 'Fulfilled'
        req.save()
        # Deduct blood stock if available
        stock = BloodStock.objects.filter(blood_group=req.blood_group).first()
        if stock and stock.units >= req.units:
            stock.units -= req.units
            stock.save()

    return HttpResponse(f"<script>alert('Request updated to {req.status}!');window.location.href='/Manage_Request/'</script>")


# ==========================================
# 5. Reports & Analytics
# ==========================================
def reports_analytics(request):
    if not check_admin_session(request):
        return HttpResponse("<script>alert('First Login as Admin');window.location.href='/login/'</script>")

    total_donors = DonorRegisterModel.objects.count()
    total_hospitals = Hospital.objects.count()
    total_donations = DonateBloodModel.objects.count() + DonationHistory.objects.count()
    total_requests = BloodRequest.objects.count() + RequestBloodModel.objects.count()
    pending_requests = BloodRequest.objects.filter(status='Pending').count() + RequestBloodModel.objects.filter(status='Pending').count()
    fulfilled_requests = BloodRequest.objects.filter(status='Fulfilled').count() + RequestBloodModel.objects.filter(status='Fulfilled').count()

    ensure_initial_blood_stock()
    stocks = BloodStock.objects.order_by('blood_group')
    total_stock = sum(s.units for s in stocks)

    context = {
        'total_donors': total_donors,
        'total_hospitals': total_hospitals,
        'total_donations': total_donations,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'fulfilled_requests': fulfilled_requests,
        'stocks': stocks,
        'total_stock': total_stock,
        'total_stock_units': total_stock,
        'total_units': total_stock,
    }
    return render(request, "AdminPages/Reports_Analytics.html", context)


# ==========================================
# 6. Change Password & Settings
# ==========================================
def change_password(request):
    if not check_admin_session(request):
        return HttpResponse("<script>alert('First Login as Admin');window.location.href='/login/'</script>")

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            return HttpResponse(
                "<script>alert('Passwords do not match');window.location.href='/change_password/'</script>"
            )
        else:
            aid = request.session.get('aid')
            data = LoginModel.objects.filter(email=aid).first()
            if data:
                data.password = make_password(new_password)
                data.save()

                user_obj = User.objects.filter(email=aid).first()
                if user_obj:
                    user_obj.set_password(new_password)
                    user_obj.save()

                return HttpResponse(
                    "<script>alert('Password Changed Successfully');window.location.href='/Setting/'</script>"
                )
            else:
                return HttpResponse(
                    "<script>alert('User account not found');window.location.href='/Setting/'</script>"
                )

    return render(request, "AdminPages/ChangePassword.html")


def settings(request):
    if not check_admin_session(request):
        return HttpResponse("<script>alert('First Login as Admin');window.location.href='/login/'</script>")

    admin_email = request.session.get('aid')
    admin_login = LoginModel.objects.filter(email=admin_email).first()
    admin_user = User.objects.filter(email=admin_email).first()

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        new_email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()

        if new_email and admin_login:
            admin_login.email = new_email
            admin_login.save()
            request.session['aid'] = new_email
            admin_email = new_email

        if admin_user:
            if full_name:
                parts = full_name.split(' ', 1)
                admin_user.first_name = parts[0]
                if len(parts) > 1:
                    admin_user.last_name = parts[1]
            if new_email:
                admin_user.email = new_email
            admin_user.save()

        return HttpResponse("<script>alert('Profile Settings updated successfully!');window.location.href='/Setting/'</script>")

    user_data = {
        'name': f"{admin_user.first_name} {admin_user.last_name}".strip() if admin_user and (admin_user.first_name or admin_user.last_name) else (admin_login.role.title() if admin_login else "Admin"),
        'email': admin_email,
        'phone': getattr(admin_user, 'phone', '+91 9876543210') if admin_user else '+91 9876543210',
        'profile_pic': None
    }

    context = {
        'admin_email': admin_email,
        'admin_user': admin_login,
        'user': user_data
    }
    return render(request, "AdminPages/Settings.html", context)
