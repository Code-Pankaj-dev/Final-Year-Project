from django.test import TestCase, Client
from AdminZone.models import LoginModel, DonorRegisterModel, BloodStock, RequestBloodModel
from HospitalZone.models import Hospital, BloodRequest
from DonorZone.models import Donor


class AdminZoneFunctionalityTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Seed Admin session
        LoginModel.objects.create(
            email='admin@hemocampus.edu',
            password='hashed_admin_pass',
            role='admin'
        )
        session = self.client.session
        session['aid'] = 'admin@hemocampus.edu'
        session.save()

        # Seed Stock
        BloodStock.objects.get_or_create(blood_group='O+', defaults={'units': 20})
        BloodStock.objects.get_or_create(blood_group='A-', defaults={'units': 5})

    def test_admin_dashboard_view(self):
        response = self.client.get('/Admin_Dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_blood_stock_quick_adjust(self):
        # Quick increment O+ by +1
        response = self.client.post('/Blood_Stock/', {
            'action_type': 'quick_adjust',
            'blood_group': 'O+',
            'delta': 1
        })
        stock = BloodStock.objects.get(blood_group='O+')
        self.assertEqual(stock.units, 21)

    def test_manage_donors_search_filter(self):
        DonorRegisterModel.objects.create(
            full_name='Aarav Sharma',
            email='aarav@test.com',
            gender='Male',
            blood_group='O+',
            mobile='9876500001',
            city='Lucknow',
            state='UP',
            pincode='226001',
            address='Aliganj Lucknow',
            dob='1990-01-01',
            age=34,
            weight=65,
            status='Pending'
        )
        DonorRegisterModel.objects.create(
            full_name='Rohan Verma',
            email='rohan@test.com',
            gender='Male',
            blood_group='B+',
            mobile='9876500002',
            city='Kanpur',
            state='UP',
            pincode='208001',
            address='Civil Lines Kanpur',
            dob='1992-02-02',
            age=32,
            weight=70,
            status='Approved'
        )
        # Search by query 'Aarav'
        response = self.client.get('/Manage_Donors/?q=Aarav')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aarav Sharma')
        self.assertNotContains(response, 'Rohan Verma')

    def test_manage_requests_fulfill_and_stock_deduction(self):
        from django.utils import timezone
        hosp = Hospital.objects.create(
            hospital_name='Apollo Hospital',
            registration_no='APL100',
            email='apollo@test.com',
            phone='9111111111',
            district='Lucknow'
        )
        req = BloodRequest.objects.create(
            hospital=hosp,
            patient_name='Rahul Kumar',
            blood_group='O+',
            units=4,
            required_date=timezone.now().date(),
            status='Pending'
        )

        # Fulfill request via admin action
        response = self.client.post(f'/admin_action_request/{req.id}/fulfill/')
        req.refresh_from_db()
        self.assertEqual(req.status, 'Fulfilled')
        # Verify 4 units deducted from 20 initial
        stock = BloodStock.objects.get(blood_group='O+')
        self.assertEqual(stock.units, 16)

    def test_reports_analytics_context(self):
        response = self.client.get('/Report_Analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('stocks', response.context)
        self.assertIn('total_stock_units', response.context)
        self.assertIn('total_hospitals', response.context)
