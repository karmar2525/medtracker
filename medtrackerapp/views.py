from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from .models import Medication, DoseLog, Note
from .serializers import MedicationSerializer, DoseLogSerializer, NoteSerializer

class MedicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing medications.

    Provides standard CRUD operations via ModelViewSet, as well as custom actions:
        - retrieving additional information from an external API (OpenFDA)
        - getting expected doses over a given number of days
    """
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

    @action(detail=True, methods=["get"], url_path="info")
    def get_external_info(self, request, pk=None):
        """
        GET endpoint: retrieve external drug information from the OpenFDA API.
        Returns 502 if the API call fails.
        """
        medication = self.get_object()
        data = medication.fetch_external_info()

        if isinstance(data, dict) and data.get("error"):
            return Response(data, status=status.HTTP_502_BAD_GATEWAY)
        return Response(data)

    @action(detail=True, methods=["get"], url_path="expected-doses")
    def expected_doses(self, request, pk=None):
        """
        GET endpoint: retrieve expected number of doses for a medication over a number of days.

        Query parameters:
            - days (int, required): number of days for the calculation

        Responses:
            - 200 OK: {medication_id, days, expected_doses}
            - 400 Bad Request: if days is missing or invalid
        """
        medication = self.get_object()
        days_param = request.query_params.get("days")

        if not days_param:
            return Response({"error": "Missing 'days' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            days = int(days_param)
            expected = medication.expected_doses(days)
        except (ValueError, TypeError):
            return Response({"error": "Invalid 'days' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "medication_id": medication.id,
            "days": days,
            "expected_doses": expected
        })


class DoseLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing dose logs.

    Provides CRUD operations and filtering by date range.
    """
    queryset = DoseLog.objects.all()
    serializer_class = DoseLogSerializer

    @action(detail=False, methods=["get"], url_path="filter")
    def filter_by_date(self, request):
        """
        GET endpoint: retrieve dose logs within a specified date range.

        Query parameters:
            - start (YYYY-MM-DD): start date (inclusive)
            - end (YYYY-MM-DD): end date (inclusive)

        Returns 400 if parameters are missing or invalid.
        """
        start_param = request.query_params.get("start")
        end_param = request.query_params.get("end")

        if not start_param or not end_param:
            return Response(
                {"error": "Both 'start' and 'end' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        start = parse_date(start_param)
        end = parse_date(end_param)
        if not start or not end:
            return Response(
                {"error": "Both 'start' and 'end' must be valid dates in YYYY-MM-DD format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        logs = self.get_queryset().filter(
            taken_at__date__gte=start,
            taken_at__date__lte=end
        ).order_by("taken_at")

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


class NoteViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    API endpoint for managing doctor's notes associated with medications.

    Supports:
        - Create
        - Retrieve (single note)
        - List all notes
        - Delete
    Updating notes is NOT allowed.
    """
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
