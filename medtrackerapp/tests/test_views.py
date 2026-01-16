from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from unittest.mock import patch
from datetime import date, timedelta


class MedicationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_data = {"name": "Aspirin", "dosage_mg": 100, "prescribed_per_day": 2}

    def test_get_medications(self):
        Medication.objects.create(**self.valid_data)
        response = self.client.get(reverse("medication-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_medication(self):
        med = Medication.objects.create(**self.valid_data)
        response = self.client.get(reverse("medication-detail", args=[med.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_medication(self):
        response = self.client.get(reverse("medication-detail", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_valid_medication(self):
        response = self.client.post(
            reverse("medication-list"), self.valid_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_invalid_medication_empty(self):
        response = self.client.post(reverse("medication-list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_negative_dosage(self):
        data = {"name": "BadMed", "dosage_mg": -10, "prescribed_per_day": 2}
        response = self.client.post(reverse("medication-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_negative_prescribed_per_day(self):
        data = {"name": "BadMed", "dosage_mg": 10, "prescribed_per_day": -2}
        response = self.client.post(reverse("medication-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_zero_prescribed_per_day(self):
        data = {"name": "ZeroMed", "dosage_mg": 10, "prescribed_per_day": 0}
        response = self.client.post(reverse("medication-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_empty_name(self):
        data = {"name": "", "dosage_mg": 10, "prescribed_per_day": 1}
        response = self.client.post(reverse("medication-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_medication(self):
        med = Medication.objects.create(**self.valid_data)
        updated_data = {
            "name": "AspirinUpdated",
            "dosage_mg": 200,
            "prescribed_per_day": 1,
        }
        response = self.client.put(
            reverse("medication-detail", args=[med.id]), updated_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        med.refresh_from_db()
        self.assertEqual(med.name, "AspirinUpdated")

    def test_update_invalid_medication(self):
        updated_data = {"name": "Invalid", "dosage_mg": 50, "prescribed_per_day": 1}
        response = self.client.put(
            reverse("medication-detail", args=[999]), updated_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_medication(self):
        med = Medication.objects.create(**self.valid_data)
        response = self.client.delete(reverse("medication-detail", args=[med.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Medication.objects.count(), 0)

    def test_delete_invalid_medication(self):
        response = self.client.delete(reverse("medication-detail", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DoseLogAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.med = Medication.objects.create(
            name="Ibuprofen", dosage_mg=200, prescribed_per_day=2
        )

    def test_get_logs(self):
        DoseLog.objects.create(
            medication=self.med, taken_at=timezone.now(), was_taken=True
        )
        response = self.client.get(reverse("doselog-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_invalid_log(self):
        response = self.client.get(reverse("doselog-detail", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_valid_log(self):
        data = {
            "medication": self.med.id,
            "taken_at": timezone.now(),
            "was_taken": True,
        }
        response = self.client.post(reverse("doselog-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_invalid_log_empty(self):
        response = self.client.post(reverse("doselog-list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_log(self):
        log = DoseLog.objects.create(
            medication=self.med, taken_at=timezone.now(), was_taken=True
        )
        new_data = {
            "medication": self.med.id,
            "taken_at": timezone.now(),
            "was_taken": False,
        }
        response = self.client.put(
            reverse("doselog-detail", args=[log.id]), new_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log.refresh_from_db()
        self.assertFalse(log.was_taken)

    def test_update_invalid_log(self):
        new_data = {
            "medication": self.med.id,
            "taken_at": timezone.now(),
            "was_taken": False,
        }
        response = self.client.put(
            reverse("doselog-detail", args=[999]), new_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_log(self):
        log = DoseLog.objects.create(
            medication=self.med, taken_at=timezone.now(), was_taken=True
        )
        response = self.client.delete(reverse("doselog-detail", args=[log.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DoseLog.objects.count(), 0)

    def test_delete_invalid_log(self):
        response = self.client.delete(reverse("doselog-detail", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MedicationExternalInfoTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.med = Medication.objects.create(
            name="Paracetamol", dosage_mg=500, prescribed_per_day=2
        )

    @patch("medtrackerapp.models.Medication.fetch_external_info")
    def test_get_external_info_success(self, mock_fetch):
        mock_fetch.return_value = {"name": "Paracetamol"}
        url = reverse("medication-get-external-info", args=[self.med.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("name", response.data)

    @patch("medtrackerapp.models.Medication.fetch_external_info")
    def test_get_external_info_error(self, mock_fetch):
        mock_fetch.return_value = {"error": "API failure"}
        url = reverse("medication-get-external-info", args=[self.med.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("error", response.data)


class DoseLogFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.med = Medication.objects.create(
            name="Ibuprofen", dosage_mg=200, prescribed_per_day=2
        )
        now = timezone.now()
        DoseLog.objects.create(medication=self.med, taken_at=now, was_taken=True)
        DoseLog.objects.create(
            medication=self.med, taken_at=now - timedelta(days=1), was_taken=False
        )

    def test_filter_logs_valid_range(self):
        start = (date.today() - timedelta(days=1)).isoformat()
        end = date.today().isoformat()
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url + f"?start={start}&end={end}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_logs_missing_params(self):
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
