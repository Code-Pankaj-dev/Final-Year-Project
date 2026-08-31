from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta, date

from AdminZone.models import LoginModel, DonorRegisterModel, BloodStock, RequestBloodModel, ContactModel, DonateBloodModel
from DonorZone.models import Donor, DonationHistory, DonorBloodRequest, DonorNotification
from HospitalZone.models import Hospital, BloodRequest


class Command(BaseCommand):
    help = 'Seed realistic demonstration data for HemoCampus'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Seeding HemoCampus database...'))

        # 1. Superuser / Admin
        admin_email = 'admin@hemocampus.edu'
        admin_pass = 'admin123'
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': admin_email,
                'first_name': 'HemoCampus',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
                'password': make_password(admin_pass)
            }
        )
        LoginModel.objects.update_or_create(
            email=admin_email,
            defaults={'password': make_password(admin_pass), 'role': 'admin'}
        )
        self.stdout.write(self.style.SUCCESS(f' Admin seeded: {admin_email} / {admin_pass}'))

        # 2. Seed Blood Stocks
        groups = {
            'A+': 18, 'A-': 6, 'B+': 24, 'B-': 5,
            'AB+': 9, 'AB-': 3, 'O+': 32, 'O-': 8
        }
        for g, u in groups.items():
            BloodStock.objects.update_or_create(
                blood_group=g,
                defaults={'units': u}
            )
        self.stdout.write(self.style.SUCCESS(' Blood Stock inventory seeded.'))

        # 3. Seed Partner Hospitals
        hospitals_data = [
            {
                'hospital_name': 'KGMU Trauma Center',
                'registration_no': 'HOSP-UP-001',
                'email': 'kgmu@hospital.edu',
                'phone': '9876543211',
                'state': 'Uttar Pradesh',
                'district': 'Lucknow',
                'address': 'Shah Mina Rd, Chowk, Lucknow, UP 226003',
                'doctor_name': 'Dr. S. K. Verma'
            },
            {
                'hospital_name': 'Apollo Hospital Bannerghatta',
                'registration_no': 'HOSP-KA-002',
                'email': 'apollo@hospital.edu',
                'phone': '9876543212',
                'state': 'Karnataka',
                'district': 'Bengaluru Urban',
                'address': '154/11, Opp IIM, Bannerghatta Rd, Bengaluru 560076',
                'doctor_name': 'Dr. Priya Nair'
            },
            {
                'hospital_name': 'AIIMS Trauma Center',
                'registration_no': 'HOSP-DL-003',
                'email': 'hospital@hemocampus.edu',
                'phone': '9876543210',
                'state': 'Delhi',
                'district': 'New Delhi',
                'address': 'Sri Aurobindo Marg, Ansari Nagar East, New Delhi 110029',
                'doctor_name': 'Dr. Rajesh Sharma'
            }
        ]

        hospitals = []
        for hd in hospitals_data:
            hosp, _ = Hospital.objects.update_or_create(
                registration_no=hd['registration_no'],
                defaults=hd
            )
            hospitals.append(hosp)
            LoginModel.objects.update_or_create(
                email=hd['email'],
                defaults={'password': make_password('hosp123'), 'role': 'hospital'}
            )
        self.stdout.write(self.style.SUCCESS(' Hospitals seeded (Login: hospital@hemocampus.edu / hosp123)'))

        # 4. Seed Donors
        donors_data = [
            {
                'full_name': 'Aarav Sharma',
                'email': 'donor@hemocampus.edu',
                'gender': 'Male',
                'blood_group': 'O+',
                'mobile': '9876500001',
                'city': 'Lucknow',
                'state': 'Uttar Pradesh',
                'address': 'B-12 Sector C, Aliganj, Lucknow',
                'dob': date(1996, 4, 15),
                'age': 28,
                'weight': 68,
                'reward_points': 250,
                'total_donations': 3,
                'status': 'Approved'
            },
            {
                'full_name': 'Ananya Roy',
                'email': 'ananya@donor.edu',
                'gender': 'Female',
                'blood_group': 'A+',
                'mobile': '9876500002',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'address': '45 Indiranagar, 100ft Road, Bengaluru',
                'dob': date(1998, 8, 22),
                'age': 26,
                'weight': 56,
                'reward_points': 150,
                'total_donations': 2,
                'status': 'Approved'
            },
            {
                'full_name': 'Vikram Singh',
                'email': 'vikram@donor.edu',
                'gender': 'Male',
                'blood_group': 'B+',
                'mobile': '9876500003',
                'city': 'New Delhi',
                'state': 'Delhi',
                'address': 'Flat 302, Dwarka Sector 10, New Delhi',
                'dob': date(1993, 11, 5),
                'age': 31,
                'weight': 74,
                'reward_points': 400,
                'total_donations': 5,
                'status': 'Approved'
            }
        ]

        for dd in donors_data:
            DonorRegisterModel.objects.update_or_create(
                email=dd['email'],
                defaults={
                    'full_name': dd['full_name'],
                    'gender': dd['gender'],
                    'dob': dd['dob'],
                    'age': dd['age'],
                    'blood_group': dd['blood_group'],
                    'weight': dd['weight'],
                    'mobile': dd['mobile'],
                    'state': dd['state'],
                    'city': dd['city'],
                    'pincode': '226001',
                    'address': dd['address'],
                    'status': dd['status']
                }
            )
            donor_obj, _ = Donor.objects.update_or_create(
                email=dd['email'],
                defaults={
                    'full_name': dd['full_name'],
                    'gender': dd['gender'],
                    'blood_group': dd['blood_group'],
                    'date_of_birth': dd['dob'],
                    'age': dd['age'],
                    'mobile': dd['mobile'],
                    'address': dd['address'],
                    'city': dd['city'],
                    'state': dd['state'],
                    'reward_points': dd['reward_points'],
                    'total_donations': dd['total_donations']
                }
            )
            LoginModel.objects.update_or_create(
                email=dd['email'],
                defaults={'password': make_password('donor123'), 'role': 'donor'}
            )

            # Sample donation history
            DonationHistory.objects.get_or_create(
                donor=donor_obj,
                donation_date=date.today() - timedelta(days=45),
                defaults={
                    'hospital_name': 'KGMU Trauma Center',
                    'units': 1,
                    'blood_group': dd['blood_group'],
                    'status': 'Approved',
                    'remarks': 'Voluntary blood donation camp'
                }
            )

            # Sample notification
            DonorNotification.objects.get_or_create(
                donor=donor_obj,
                title='Thank you for saving lives!',
                defaults={
                    'message': 'Your recent blood donation has successfully helped a patient in need. 50 reward points credited.'
                }
            )
        self.stdout.write(self.style.SUCCESS(' Donors seeded (Login: donor@hemocampus.edu / donor123)'))

        # 5. Seed Blood Requisitions
        if hospitals:
            BloodRequest.objects.get_or_create(
                patient_name='Sunil Mehra',
                hospital=hospitals[0],
                defaults={
                    'blood_group': 'O+',
                    'units': 2,
                    'priority': 'Emergency',
                    'status': 'Pending',
                    'required_date': date.today() + timedelta(days=1),
                    'remarks': 'Urgent Cardiac Surgery'
                }
            )
            BloodRequest.objects.get_or_create(
                patient_name='Meera Patel',
                hospital=hospitals[1],
                defaults={
                    'blood_group': 'A+',
                    'units': 1,
                    'priority': 'Normal',
                    'status': 'Approved',
                    'required_date': date.today() + timedelta(days=2),
                    'remarks': 'Scheduled Orthopedic Surgery'
                }
            )

        # 6. Seed Direct Public Requests
        RequestBloodModel.objects.get_or_create(
            patient_name='Kavita Joshi',
            defaults={
                'blood_group': 'B+',
                'units_needed': 2,
                'urgency': 'Emergency',
                'required_by': date.today() + timedelta(days=1),
                'contact_phone': '9876543220',
                'hospital_name': 'Civil Hospital Lucknow',
                'hospital_address': 'Hazratganj, Lucknow',
                'status': 'Pending'
            }
        )

        self.stdout.write(self.style.SUCCESS(' Requisitions & Public Requests seeded.'))
        self.stdout.write(self.style.SUCCESS('===================================================='))
        self.stdout.write(self.style.SUCCESS(' HemoCampus Seed Completed Successfully!'))
        self.stdout.write(self.style.SUCCESS(' Credentials for testing:'))
        self.stdout.write(self.style.SUCCESS('   • Admin:    admin@hemocampus.edu    / admin123'))
        self.stdout.write(self.style.SUCCESS('   • Donor:    donor@hemocampus.edu    / donor123'))
        self.stdout.write(self.style.SUCCESS('   • Hospital: hospital@hemocampus.edu / hosp123'))
        self.stdout.write(self.style.SUCCESS('===================================================='))
