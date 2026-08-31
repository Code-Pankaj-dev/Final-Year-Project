from django.test import TestCase, Client
from HospitalZone.models import Hospital, BloodRequest
from AdminZone.models import BloodStock


class HospitalZoneSecurityAndFunctionalityTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Seed first hospital
        self.hosp1 = Hospital.objects.create(
            hospital_name='Apex Hospital A',
            registration_no='HOSP001',
            email='hospitalA@test.com',
            phone='9999999991',
            district='Lucknow'
        )
        # Seed second hospital
        self.hosp2 = Hospital.objects.create(
            hospital_name='Apex Hospital B',
            registration_no='HOSP002',
            email='hospitalB@test.com',
            phone='9999999992',
            district='Kanpur'
        )

    def test_anonymous_access_redirects_to_login(self):
        response = self.client.get('/hospital-dashboard/')
        self.assertIn('/login/', response.content.decode())

    def test_tenant_isolation_invalid_session_does_not_leak_first_hospital(self):
        session = self.client.session
        session['aid'] = 'unknown@test.com'
        session.save()

        response = self.client.get('/hospital-dashboard/')
        self.assertIn('/login/', response.content.decode())
        self.assertNotIn('Apex Hospital A', response.content.decode())

    def test_authenticated_hospital_sees_own_data_only(self):
        session = self.client.session
        session['aid'] = 'hospitalB@test.com'
        session.save()

        response = self.client.get('/hospital-dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apex Hospital B')
        self.assertNotContains(response, 'Apex Hospital A')

    def test_emergency_blood_request_submission(self):
        session = self.client.session
        session['aid'] = 'hospitalB@test.com'
        session.save()

        response = self.client.post('/hospital-dashboard/emergency-request/', {
            'patient_name': 'Emergency Patient',
            'blood_group': 'O-',
            'units': 3,
            'remarks': 'Trauma ICU Surgery'
        })
        self.assertEqual(BloodRequest.objects.count(), 1)
        req = BloodRequest.objects.first()
        self.assertEqual(req.hospital, self.hosp2)
        self.assertEqual(req.priority, 'Emergency')
        self.assertEqual(req.units, 3)
