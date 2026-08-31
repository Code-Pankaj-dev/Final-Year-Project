from django.test import TestCase, Client
from django.utils import timezone
from DonorZone.models import Donor, DonationHistory, DonorBloodRequest
from AdminZone.models import BloodStock, LoginModel


class DonorZoneSecurityAndFunctionalityTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create victim donor
        self.donor1 = Donor.objects.create(
            full_name='Victim Donor',
            email='victim@test.com',
            gender='Male',
            blood_group='A+',
            mobile='1111111111',
            date_of_birth='1990-01-01',
            age=34,
            address='Victim Address',
            city='Lucknow',
            state='UP',
            reward_points=100
        )
        # Create second donor
        self.donor2 = Donor.objects.create(
            full_name='Second Donor',
            email='second@test.com',
            gender='Female',
            blood_group='B+',
            mobile='2222222222',
            date_of_birth='1995-05-05',
            age=29,
            address='Second Address',
            city='Kanpur',
            state='UP',
            reward_points=50
        )
        # Seed Blood Stock
        BloodStock.objects.get_or_create(blood_group='A+', defaults={'units': 10})

    def test_anonymous_access_redirects_to_login(self):
        response = self.client.get('/donor-dashboard/')
        self.assertIn('/login/', response.content.decode())

    def test_idor_protection_invalid_session_does_not_leak_first_donor(self):
        # Set session to non-existent email
        session = self.client.session
        session['aid'] = 'nonexistent@test.com'
        session.save()

        response = self.client.get('/donor-dashboard/')
        # Must redirect to login, NOT show victim donor's profile
        self.assertIn('/login/', response.content.decode())
        self.assertNotIn('Victim Donor', response.content.decode())

    def test_authenticated_donor_sees_own_data_only(self):
        session = self.client.session
        session['aid'] = 'second@test.com'
        session.save()

        response = self.client.get('/donor-dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Second Donor')
        self.assertNotContains(response, 'Victim Donor')

    def test_in_portal_donation_action(self):
        session = self.client.session
        session['aid'] = 'second@test.com'
        session.save()

        response = self.client.post('/donor-dashboard/donate-blood/', {
            'units': 2,
            'blood_group': 'A+',
            'hospital_name': 'KGMU Lucknow',
            'remarks': 'Voluntary Donor Camp'
        })
        self.donor2.refresh_from_db()
        self.assertEqual(self.donor2.total_donations, 1)
        self.assertEqual(self.donor2.reward_points, 100) # 50 initial + 50 reward
        stock = BloodStock.objects.get(blood_group='A+')
        self.assertEqual(stock.units, 12) # 10 initial + 2 added

    def test_donor_certificate_generation(self):
        donation = DonationHistory.objects.create(
            donor=self.donor2,
            donation_date=timezone.now().date(),
            hospital_name='Apollo Hospital',
            units=1,
            blood_group='B+',
            status='Approved'
        )
        session = self.client.session
        session['aid'] = 'second@test.com'
        session.save()

        response = self.client.get(f'/donor-dashboard/certificate/{donation.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Certificate of Appreciation')
        self.assertContains(response, 'Second Donor')
        self.assertContains(response, 'Apollo Hospital')
