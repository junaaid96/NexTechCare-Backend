from unittest import mock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from profiles.models import User, CustomerProfile, EngineerProfile, AdminProfile
from services.models import Service


def make_user(username, t):
    u = User.objects.create_user(username=username, password='pass12345', first_name=username.title(), last_name='T', email=f'{username}@x.io', user_type=t)
    return u


class FlowTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        self.cu = make_user('cust', 'C'); self.cp = CustomerProfile.objects.create(user=self.cu)
        self.eu = make_user('eng', 'E'); self.ep = EngineerProfile.objects.create(user=self.eu)
        self.au = make_user('adm', 'A'); AdminProfile.objects.create(user=self.au)
        self.svc = Service.objects.create(name='Wi-Fi fix', description='router and wifi troubleshooting', price=40, duration=2,
                                          engineer=self.ep, admin_approved=True, category='networking', sla_hours=4)

    def login(self, u):
        r = self.c.post('/profiles/login/', {'username': u.username, 'password': 'pass12345'})
        self.assertEqual(r.status_code, 200)
        self.c.credentials(HTTP_AUTHORIZATION='Bearer ' + r.data['access'])

    def test_health_and_categories(self):
        self.assertEqual(self.c.get('/health/').status_code, 200)
        r = self.c.get('/bookings/categories/')
        self.assertEqual(len(r.data), 10)
        self.assertEqual({x['key']: x['count'] for x in r.data}['networking'], 1)

    def test_service_list_filters_and_trust(self):
        Service.objects.create(name='Pending', description='x', price=1, duration=1, engineer=self.ep)
        r = self.c.get('/services/?admin_approved=True&category=networking')
        self.assertEqual(len(r.data), 1)
        self.assertIn('score', r.data[0]['trust'])
        self.assertEqual(len(self.c.get('/services/?admin_approved=False').data), 1)

    def test_booking_lifecycle(self):
        self.login(self.cu)
        r = self.c.post('/bookings/', {'service': self.svc.pk, 'issue': 'wifi drops', 'priority': 'high'})
        self.assertEqual(r.status_code, 201, r.data)
        bid = r.data['id']
        self.assertEqual(self.c.post('/bookings/', {'service': self.svc.pk}).status_code, 400)
        self.assertEqual(self.c.post(f'/bookings/{bid}/status/', {'status': 'resolved'}).status_code, 400)
        self.login(self.eu)
        for st in ['accepted', 'in_progress', 'resolved']:
            r = self.c.post(f'/bookings/{bid}/status/', {'status': st, 'note': st})
            self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(len(r.data['events']), 4)
        self.assertTrue(self.svc.customer.filter(pk=self.cp.pk).exists())
        self.login(self.au)
        stats = self.c.get('/bookings/stats/').data
        self.assertEqual(stats['kpis']['open_bookings'], 0)
        self.assertEqual(stats['engineers'][0]['jobs_completed'], 1)

    def test_permissions(self):
        self.login(self.cu)
        self.assertEqual(self.c.get('/bookings/stats/').status_code, 403)
        self.login(self.eu)
        self.assertEqual(self.c.post('/bookings/', {'service': self.svc.pk}).status_code, 403)

    def test_admin_bulk_approve_and_verify(self):
        p = Service.objects.create(name='P', description='x', price=1, duration=1, engineer=self.ep)
        self.login(self.au)
        self.assertEqual(self.c.post('/services/approved/bulk/', {'ids': [p.pk]}, format='json').data['approved'], 1)
        self.assertTrue(self.c.post(f'/profiles/engineers/{self.ep.pk}/verify/').data['verified'])


class TriageTests(TestCase):
    def setUp(self):
        eu = make_user('eng', 'E'); ep = EngineerProfile.objects.create(user=eu)
        self.svc = Service.objects.create(name='Virus removal', description='malware cleanup', price=30, duration=1,
                                          engineer=ep, admin_approved=True, category='cybersecurity')

    @override_settings(GROQ_API_KEY='')
    def test_rule_fallback(self):
        r = APIClient().post('/triage/', {'description': 'My laptop got hacked, ransomware popup urgent'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['category'], 'cybersecurity')
        self.assertEqual(r.data['urgency'], 'high')
        self.assertEqual(r.data['source'], 'rules')
        self.assertEqual(r.data['services'][0]['id'], self.svc.pk)

    @override_settings(GROQ_API_KEY='test')
    def test_ai_failure_falls_back(self):
        with mock.patch('triage.engine._call_groq', side_effect=TimeoutError):
            r = APIClient().post('/triage/', {'description': 'wifi router keeps dropping'})
        self.assertEqual(r.data['source'], 'rules')
        self.assertEqual(r.data['category'], 'networking')

    @override_settings(GROQ_API_KEY='test')
    def test_ai_result_sanitized(self):
        fake = {'category': 'cybersecurity', 'urgency': 'critical', 'summary': 'ok', 'diy_steps': ['a'], 'recommended_service_ids': [self.svc.pk, 999]}
        with mock.patch('triage.engine._call_groq', return_value=fake):
            r = APIClient().post('/triage/', {'description': 'suspicious emails everywhere'})
        self.assertEqual(r.data['source'], 'ai')
        self.assertEqual(r.data['recommended_service_ids'], [self.svc.pk])
