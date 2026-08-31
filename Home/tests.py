from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from AdminZone.models import LoginModel, DonorRegisterModel, BloodStock
from DonorZone.models import Donor
from HospitalZone.models import Hospital


class HomePublicPagesTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_status(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HEMO CAMPUS")

    def test_about_page_status(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)

    def test_services_page_status(self):
        response = self.client.get('/services/')
        self.assertEqual(response.status_code, 200)

    def test_blood_availability_page(self):
        response = self.client.get('/blood-availability/')
        self.assertEqual(response.status_code, 200)

    def test_blood_availability_multi_filter_search(self):
        # Test 3 options: State, District, Blood Group (UP)
        response = self.client.get('/blood-availability/?state=Uttar%20Pradesh&district=Lucknow&blood_group=O%2B')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KGMU")
        self.assertContains(response, "Uttar Pradesh")
        self.assertContains(response, "Lucknow")

    def test_blood_availability_bihar_and_uttarakhand(self):
        # Test Bihar - Patna
        resp_bihar = self.client.get('/blood-availability/?state=Bihar&district=Patna&blood_group=A%2B')
        self.assertEqual(resp_bihar.status_code, 200)
        self.assertContains(resp_bihar, "AIIMS Patna")
        self.assertContains(resp_bihar, "Patna")

        # Test Uttarakhand - Dehradun
        resp_uk = self.client.get('/blood-availability/?state=Uttarakhand&district=Dehradun&blood_group=B%2B')
        self.assertEqual(resp_uk.status_code, 200)
        self.assertContains(resp_uk, "AIIMS Rishikesh")
        self.assertContains(resp_uk, "Dehradun")

        # Test Rajasthan - Jaipur
        resp_rj = self.client.get('/blood-availability/?state=Rajasthan&district=Jaipur')
        self.assertEqual(resp_rj.status_code, 200)
        self.assertContains(resp_rj, "SMS")
        self.assertContains(resp_rj, "Jaipur")

    def test_blood_center_directory_page(self):
        response = self.client.get('/blood-center-directory/')
        self.assertEqual(response.status_code, 200)

    def test_camp_schedule_page(self):
        response = self.client.get('/camp-schedule/')
        self.assertEqual(response.status_code, 200)

    def test_donate_page(self):
        response = self.client.get('/donate/')
        self.assertEqual(response.status_code, 200)

    def test_request_blood_page_with_prefill(self):
        response = self.client.get('/request-blood/?hospital=KGMU%20Trauma%20Center')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="KGMU Trauma Center"')

    def test_contact_page(self):
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 200)


class AuthenticationAndSecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Seed test admin account
        LoginModel.objects.create(
            email='admin@hemocampus.edu',
            password=make_password('admin123'),
            role='admin'
        )
        # Seed test donor account
        LoginModel.objects.create(
            email='donor@test.com',
            password=make_password('donorpass123'),
            role='donor'
        )
        Donor.objects.create(
            full_name='Test Donor',
            email='donor@test.com',
            gender='Male',
            blood_group='O+',
            mobile='9876543210',
            date_of_birth='1995-05-15',
            age=29,
            address='123 Test Street',
            city='Lucknow',
            state='Uttar Pradesh'
        )

    def test_admin_login_success(self):
        response = self.client.post('/loginCode/', {
            'username': 'admin@hemocampus.edu',
            'password': 'admin123',
            'role': 'admin'
        })
        self.assertEqual(self.client.session.get('aid'), 'admin@hemocampus.edu')
        self.assertIn('/Admin_Dashboard/', response.content.decode())

    def test_donor_login_success(self):
        response = self.client.post('/loginCode/', {
            'username': 'donor@test.com',
            'password': 'donorpass123',
            'role': 'donor'
        })
        self.assertEqual(self.client.session.get('aid'), 'donor@test.com')
        self.assertIn('/donor-dashboard/', response.content.decode())

    def test_login_invalid_password(self):
        response = self.client.post('/loginCode/', {
            'username': 'donor@test.com',
            'password': 'wrongpassword',
            'role': 'donor'
        })
        self.assertIsNone(self.client.session.get('aid'))
        self.assertIn('Invalid Email/Username or Password', response.content.decode())

    def test_legacy_plaintext_password_auto_upgrade(self):
        # Create user with plaintext password
        LoginModel.objects.create(
            email='legacy@test.com',
            password='plainpassword123',
            role='donor'
        )
        response = self.client.post('/loginCode/', {
            'username': 'legacy@test.com',
            'password': 'plainpassword123',
            'role': 'donor'
        })
        self.assertEqual(self.client.session.get('aid'), 'legacy@test.com')
        # Verify it was auto-upgraded to a secure hash
        upgraded_user = LoginModel.objects.get(email='legacy@test.com')
        self.assertTrue(upgraded_user.password.startswith(('pbkdf2_sha256$', 'argon2', 'bcrypt')))
