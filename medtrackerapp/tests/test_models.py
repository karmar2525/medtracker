from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
from unittest.mock import patch

from medtrackerapp.models import Medication, DoseLog
from medtrackerapp.services import DrugInfoService


class MedicationModelTests(TestCase):

    def test_str_returns_name_and_dosage(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.assertEqual(str(med), "Aspirin (100mg)")

    def test_negative_dosage_validation(self):
        med = Medication(name="TestMed", dosage_mg=-5, prescribed_per_day=1)
        with self.assertRaises(ValidationError):
            med.full_clean()

    def test_negative_prescribed_per_day_validation(self):
        med = Medication(name="TestMed", dosage_mg=10, prescribed_per_day=-1)
        with self.assertRaises(ValidationError):
            med.full_clean()

    def test_expected_doses_positive(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.assertEqual(med.expected_doses(5), 10)

    def test_expected_doses_zero_prescribed(self):
        med = Medication.objects.create(name="ZeroMed", dosage_mg=10, prescribed_per_day=0)
        self.assertEqual(med.expected_doses(5), 0)

    def test_expected_doses_invalid_days(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        with self.assertRaises(ValueError):
            med.expected_doses(-2)

    def test_adherence_rate_no_logs(self):
        med = Medication.objects.create(name="NoLogs", dosage_mg=10, prescribed_per_day=1)
        self.assertEqual(med.adherence_rate(), 0.0)

    def test_adherence_rate_all_taken(self):
        med = Medication.objects.create(name="AllTaken", dosage_mg=10, prescribed_per_day=2)
        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now, was_taken=True)
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1), was_taken=True)
        self.assertEqual(med.adherence_rate(), 100.0)

    def test_adherence_rate_partial(self):
        med = Medication.objects.create(name="Partial", dosage_mg=10, prescribed_per_day=2)
        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now, was_taken=True)
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1), was_taken=False)
        self.assertEqual(med.adherence_rate(), 50.0)

    def test_adherence_rate_over_period_valid(self):
        med = Medication.objects.create(name="PeriodMed", dosage_mg=50, prescribed_per_day=1)
        today = date.today()
        yesterday = today - timedelta(days=1)
        DoseLog.objects.create(medication=med, taken_at=timezone.now() - timedelta(days=1), was_taken=True)
        DoseLog.objects.create(medication=med, taken_at=timezone.now(), was_taken=False)
        self.assertEqual(med.adherence_rate_over_period(yesterday, today), 50.0)

    def test_adherence_rate_over_period_no_logs(self):
        med = Medication.objects.create(name="NoLogsPeriod", dosage_mg=10, prescribed_per_day=2)
        today = date.today()
        tomorrow = today + timedelta(days=1)
        self.assertEqual(med.adherence_rate_over_period(today, tomorrow), 0.0)

    def test_adherence_rate_over_period_zero_prescribed(self):
        med = Medication.objects.create(name="ZeroPrescribed", dosage_mg=10, prescribed_per_day=0)
        today = date.today()
        self.assertEqual(med.adherence_rate_over_period(today, today), 0.0)

    def test_adherence_rate_over_period_invalid_dates(self):
        med = Medication.objects.create(name="InvalidDates", dosage_mg=10, prescribed_per_day=1)
        with self.assertRaises(ValueError):
            med.adherence_rate_over_period(date(2025, 1, 5), date(2025, 1, 1))

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_fetch_external_info_success(self, mock_service):
        med = Medication.objects.create(name="Paracetamol", dosage_mg=500, prescribed_per_day=2)
        mock_service.return_value = {"name": "Paracetamol"}
        result = med.fetch_external_info()
        self.assertEqual(result["name"], "Paracetamol")

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_fetch_external_info_exception(self, mock_service):
        med = Medication.objects.create(name="TestMed", dosage_mg=10, prescribed_per_day=1)
        mock_service.side_effect = Exception("API down")
        result = med.fetch_external_info()
        self.assertIn("error", result)

class DoseLogModelTests(TestCase):

    def test_str_taken(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)
        log = DoseLog.objects.create(medication=med, taken_at=timezone.now(), was_taken=True)
        self.assertIn("Taken", str(log))

    def test_str_not_taken(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)
        log = DoseLog.objects.create(medication=med, taken_at=timezone.now(), was_taken=False)
        self.assertIn("Missed", str(log))

    def test_doselog_without_medication(self):
        log = DoseLog(taken_at=timezone.now())
        with self.assertRaises(ValidationError):
            log.full_clean()

    def test_doselog_without_taken_at(self):
        med = Medication.objects.create(name="MedTest", dosage_mg=10, prescribed_per_day=1)
        log = DoseLog(medication=med)
        with self.assertRaises(ValidationError):
            log.full_clean()

    def test_doselog_future_date_allowed(self):
        med = Medication.objects.create(name="FutureMed", dosage_mg=10, prescribed_per_day=1)
        future_time = timezone.now() + timedelta(days=1)
        log = DoseLog.objects.create(medication=med, taken_at=future_time, was_taken=True)
        self.assertEqual(log.taken_at, future_time)

    def test_doselog_default_was_taken(self):
        med = Medication.objects.create(name="DefaultTaken", dosage_mg=10, prescribed_per_day=1)
        log = DoseLog.objects.create(medication=med, taken_at=timezone.now())
        self.assertTrue(log.was_taken)
