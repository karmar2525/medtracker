from django.test import TestCase
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import timedelta, date


class MedicationModelTests(TestCase):

    def test_str_returns_name_and_dosage(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.assertEqual(str(med), "Aspirin (100mg)")

    def test_adherence_rate_all_doses_taken(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)

        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=30))
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1))

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)

    def test_adherence_rate_partial(self):
        med = Medication.objects.create(
            name="Ibuprofen",
            dosage_mg=200,
            prescribed_per_day=3
        )

        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now, was_taken=True)
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=5), was_taken=False)

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 50.0)  # 1 of 2 taken

    def test_adherence_rate_no_logs(self):
        med = Medication.objects.create(
            name="Paracetamol",
            dosage_mg=500,
            prescribed_per_day=1
        )
        self.assertEqual(med.adherence_rate(), 0.0)

    def test_expected_doses_valid(self):
        med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )
        self.assertEqual(med.expected_doses(3), 6)

    def test_expected_doses_raises_for_invalid_days(self):
        med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )
        with self.assertRaises(ValueError):
            med.expected_doses(-1)

    def test_adherence_rate_over_period(self):
        med = Medication.objects.create(
            name="Vitamin C",
            dosage_mg=500,
            prescribed_per_day=1
        )

        today = date.today()
        yesterday = today - timedelta(days=1)

        DoseLog.objects.create(
            medication=med,
            taken_at=timezone.now() - timedelta(days=1),
            was_taken=True
        )
        DoseLog.objects.create(
            medication=med,
            taken_at=timezone.now(),
            was_taken=False
        )

        rate = med.adherence_rate_over_period(yesterday, today)
        # 1 taken out of expected 2 days = 1/2 = 50%
        self.assertEqual(rate, 50.0)

    def test_adherence_rate_over_period_invalid_dates(self):
        med = Medication.objects.create(
            name="X",
            dosage_mg=10,
            prescribed_per_day=1
        )
        with self.assertRaises(ValueError):
            med.adherence_rate_over_period(date(2025, 1, 2), date(2025, 1, 1))


class DoseLogModelTests(TestCase):

    def test_str_includes_name_date_and_status(self):
        med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=1
        )

        log = DoseLog.objects.create(
            medication=med,
            taken_at=timezone.now(),
            was_taken=True
        )

        self.assertIn("Aspirin", str(log))
        self.assertIn("Taken", str(log))