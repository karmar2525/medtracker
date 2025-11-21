from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone

class MedicationAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.medication_data = {
            "name": "Aspirin",
            "dosage_mg": 100,
            "prescribed_per_day": 2
        }

    def test_get_medications(self):
        """Test retrieving the list of medications"""
        Medication.objects.create(**self.medication_data)
        url = reverse('medication-list')  # corrected name
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_post_medication_valid(self):
        """Test creating a valid medication"""
        url = reverse('medication-list')
        response = self.client.post(url, self.medication_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Medication.objects.count(), 1)

    def test_post_medication_invalid(self):
        """Test creating an invalid medication (missing required fields)"""
        url = reverse('medication-list')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DoseLogAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.med = Medication.objects.create(
            name="Ibuprofen",
            dosage_mg=200,
            prescribed_per_day=2
        )

    def test_get_logs(self):
        """Test retrieving the list of dose logs"""
        DoseLog.objects.create(medication=self.med, taken_at=timezone.now(), was_taken=True)
        url = reverse('doselog-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_post_log_valid(self):
        """Test creating a valid dose log"""
        url = reverse('doselog-list')
        data = {
            "medication": self.med.id,
            "taken_at": timezone.now(),
            "was_taken": True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoseLog.objects.count(), 1)

    def test_post_log_invalid(self):
        """Test creating an invalid dose log (missing required fields)"""
        url = reverse('doselog-list')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
