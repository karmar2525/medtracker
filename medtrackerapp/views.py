from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from .models import Medication, DoseLog
from .serializers import MedicationSerializer, DoseLogSerializer


class MedicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing medications.

    Provides standard CRUD operations via the Django REST Framework
    `ModelViewSet`, as well as custom actions:
      - retrieving additional information from an external API (OpenFDA)
      - getting expected doses over a given number of days
    """
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

    @action(detail=True, methods=["get"], url_path="info")
    def get_external_info(self, request, pk=None):
        """
        Retrieve external drug information from the OpenFDA API.
        """
        medication = self.get_object()
        data = medication.fetch_external_info()

        if isinstance(data, dict) and data.get("error"):
            return Response(data, status=status.HTTP_502_BAD_GATEWAY)
        return Response(data)

    @action(detail=True, methods=["get"], url_path="expected-doses")
    def expected_doses(self, request, pk=None):
        """
        Get the expected number of doses for this medication over a given number of days.

        Query parameter:
            - days (int, required): number of days to calculate expected doses
        """
        medication = self.get_object()
        days_param = request.query_params.get("days")

        # brak parametru days
        if days_param is None:
            return Response({"error": "Missing 'days' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            days = int(days_param)
            expected = medication.expected_doses(days)
            return Response({
                "medication_id": medication.id,
                "days": days,
                "expected_doses": expected
            })
        except (ValueError, TypeError):
            return Response({"error": "Invalid 'days' parameter"}, status=status.HTTP_400_BAD_REQUEST)


class DoseLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing dose logs.

    Provides standard CRUD operations and filtering by date range.
    """
    queryset = DoseLog.objects.all()
    serializer_class = DoseLogSerializer

    @action(detail=False, methods=["get"], url_path="filter")
    def filter_by_date(self, request):
        """
        Retrieve all dose logs within a given date range.

        Query Parameters:
            - start (YYYY-MM-DD): Start date of the range (inclusive).
            - end (YYYY-MM-DD): End date of the range (inclusive).
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
