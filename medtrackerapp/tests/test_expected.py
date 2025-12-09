from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from medtrackerapp.models import Medication

class ExpectedDosesTests(APITestCase):

    def setUp(self):
        self.med = Medication.objects.create(
            name="Paracetamol",
            dosage_mg=500,
            prescribed_per_day=3
        )
        self.url = lambda days=None: reverse('medication-expected-doses', args=[self.med.id]) + (f'?days={days}' if days else '')

    # --- positive case ---
    def test_expected_doses_valid(self):
        response = self.client.get(self.url(days=5))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['expected_doses'], self.med.expected_doses(5))

    # --- missing 'days' parameter ---
    def test_missing_days(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- negative 'days' value ---
    def test_invalid_days(self):
        response = self.client.get(self.url(days=-2))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- 'days' is not an integer ---
    def test_non_integer_days(self):
        response = self.client.get(self.url(days='abc'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
