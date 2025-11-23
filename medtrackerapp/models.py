from django.db import models
from datetime import date as _date
from django.utils import timezone
from .services import DrugInfoService


class Medication(models.Model):
    """
    Represents a prescribed medication with dosage and daily schedule.
    Each Medication instance can have multiple associated DoseLog entries
    that record when doses were taken or missed.
    """

    name = models.CharField(max_length=100)
    dosage_mg = models.PositiveIntegerField()
    prescribed_per_day = models.PositiveIntegerField(help_text="Expected number of doses per day")

    def __str__(self):
        return f"{self.name} ({self.dosage_mg}mg)"

    def adherence_rate(self):
        logs = self.doselog_set.all()
        if not logs.exists():
            return 0.0
        taken = logs.filter(was_taken=True).count()
        return round((taken / logs.count()) * 100, 2)

    def expected_doses(self, days: int) -> int:
        """
        Compute the expected number of doses over a given number of days.

        Returns 0 if prescribed_per_day is 0.
        Raises ValueError if days < 0.
        """
        if days < 0:
            raise ValueError("Days must be non-negative.")
        if self.prescribed_per_day <= 0:
            return 0
        return days * self.prescribed_per_day

    def adherence_rate_over_period(self, start_date: _date, end_date: _date) -> float:
        if start_date > end_date:
            raise ValueError("start_date must be before or equal to end_date")
        logs = self.doselog_set.filter(
            taken_at__date__gte=start_date,
            taken_at__date__lte=end_date
        )
        days = (end_date - start_date).days + 1
        expected = self.expected_doses(days)
        if expected == 0:
            return 0.0
        taken = logs.filter(was_taken=True).count()
        return round((taken / expected) * 100, 2)

    def fetch_external_info(self):
        try:
            return DrugInfoService.get_drug_info(self.name)
        except Exception as exc:
            return {"error": str(exc)}


class DoseLog(models.Model):
    """
    Records the administration of a medication dose.
    """

    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    taken_at = models.DateTimeField()
    was_taken = models.BooleanField(default=True)

    class Meta:
        ordering = ["-taken_at"]

    def __str__(self):
        status = "Taken" if self.was_taken else "Missed"
        when = timezone.localtime(self.taken_at).strftime("%Y-%m-%d %H:%M")
        return f"{self.medication.name} at {when} - {status}"

from django.test import TestCase
from datetime import datetime, date, timedelta
from medtrackerapp.models import Medication, DoseLog

class MedicationModelTests(TestCase):

    def setUp(self):
        # Create a sample medication
        self.med = Medication.objects.create(
            name="Ibuprofen",
            dosage_mg=200,
            prescribed_per_day=2
        )

    # --- POSITIVE TESTS ---

    def test_str_representation(self):
        """Test __str__ returns correct human-readable string"""
        self.assertEqual(str(self.med), "Ibuprofen (200mg)")

    def test_expected_doses_positive(self):
        """Test expected doses calculation with valid days"""
        self.assertEqual(self.med.expected_doses(5), 10)  # 2 doses/day * 5 days

    def test_adherence_rate_no_logs(self):
        """Test adherence rate when no DoseLogs exist"""
        self.assertEqual(self.med.adherence_rate(), 0.0)

    def test_adherence_rate_with_logs(self):
        """Test adherence rate with some taken and some missed doses"""
        DoseLog.objects.create(medication=self.med, taken_at=datetime.now(), was_taken=True)
        DoseLog.objects.create(medication=self.med, taken_at=datetime.now(), was_taken=True)
        DoseLog.objects.create(medication=self.med, taken_at=datetime.now(), was_taken=False)
        self.assertEqual(self.med.adherence_rate(), round(2/3*100, 2))

    def test_adherence_rate_over_period(self):
        """Test adherence rate over a specific period"""
        today = date.today()
        DoseLog.objects.create(
            medication=self.med,
            taken_at=datetime.combine(today, datetime.min.time()),
            was_taken=True
        )
        # Expected adherence = taken doses / expected doses * 100
        expected = (1 / self.med.prescribed_per_day) * 100
        self.assertEqual(self.med.adherence_rate_over_period(today, today), round(expected, 2))

    # --- NEGATIVE TESTS ---

    def test_expected_doses_negative_days(self):
        """Test expected_doses raises ValueError for negative days"""
        with self.assertRaises(ValueError):
            self.med.expected_doses(-1)

    def test_expected_doses_invalid_schedule(self):
        """Test expected_doses raises ValueError if prescribed_per_day <= 0"""
        self.med.prescribed_per_day = 0
        with self.assertRaises(ValueError):
            self.med.expected_doses(5)

    def test_adherence_rate_over_period_invalid_dates(self):
        """Test adherence_rate_over_period raises ValueError if start_date > end_date"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        with self.assertRaises(ValueError):
            self.med.adherence_rate_over_period(today, yesterday)

    def test_doselog_without_medication(self):
        """Test DoseLog creation without medication raises Exception"""
        with self.assertRaises(Exception):
            DoseLog.objects.create(taken_at=datetime.now())

    def test_doselog_without_taken_at(self):
        """Test DoseLog creation without taken_at raises Exception"""
        with self.assertRaises(Exception):
            DoseLog.objects.create(medication=self.med)
