from rest_framework import serializers
from .models import Medication, DoseLog, Note


class MedicationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Medication model.

    Adds an 'adherence' field computed from the related DoseLog entries.
    """

    adherence = serializers.SerializerMethodField()

    class Meta:
        model = Medication
        fields = ["id", "name", "dosage_mg", "prescribed_per_day", "adherence"]

    def get_adherence(self, obj):
        """
        Compute the adherence rate of this medication.
        """
        return obj.adherence_rate()

    def validate_name(self, value):
        """
        Ensure the medication name is not empty.
        """
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value

    def validate_dosage_mg(self, value):
        """
        Ensure dosage is greater than zero.
        """
        if value <= 0:
            raise serializers.ValidationError("Dosage must be greater than 0")
        return value

    def validate_prescribed_per_day(self, value):
        """
        Ensure prescribed_per_day is greater than zero.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Prescribed per day must be greater than 0"
            )
        return value


class DoseLogSerializer(serializers.ModelSerializer):
    """
    Serializer for the DoseLog model.
    Records whether a medication dose was taken at a specific time.
    """

    class Meta:
        model = DoseLog
        fields = ["id", "medication", "taken_at", "was_taken"]


class NoteSerializer(serializers.ModelSerializer):
    """
    Serializer for the Note model.

    Allows creation, retrieval, and listing of doctor's notes associated with medications.
    'created_at' is read-only.
    """

    class Meta:
        model = Note
        fields = ["id", "medication", "text", "created_at"]
        read_only_fields = ["created_at"]
