from rest_framework import serializers
from .models import Medication, DoseLog

class MedicationSerializer(serializers.ModelSerializer):
    adherence = serializers.SerializerMethodField()

    class Meta:
        model = Medication
        fields = ["id", "name", "dosage_mg", "prescribed_per_day", "adherence"]

    def get_adherence(self, obj):
        return obj.adherence_rate()

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value

    def validate_dosage_mg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Dosage must be greater than 0")
        return value

    def validate_prescribed_per_day(self, value):
        if value <= 0:
            raise serializers.ValidationError("Prescribed per day must be greater than 0")
        return value


class DoseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoseLog
        fields = ["id", "medication", "taken_at", "was_taken"]
