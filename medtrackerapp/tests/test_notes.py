from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from medtrackerapp.models import Medication

class NotesTests(APITestCase):

    def setUp(self):
        self.med = Medication.objects.create(
            name="Ibuprofen",
            dosage_mg=200,
            prescribed_per_day=2
        )
        self.notes_url = reverse("note-list")

    def test_create_note(self):
        data = {
            "medication": self.med.id,
            "text": "Patient reported mild headache."
        }
        response = self.client.post(self.notes_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_get_notes_list(self):
        response = self.client.get(self.notes_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_single_note(self):
        create = self.client.post(self.notes_url, {
            "medication": self.med.id,
            "text": "Test note"
        }, format="json")
        note_id = create.data["id"]

        url = reverse("note-detail", args=[note_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], note_id)

    def test_delete_note(self):
        create = self.client.post(self.notes_url, {
            "medication": self.med.id,
            "text": "Note to delete"
        }, format="json")
        note_id = create.data["id"]

        url = reverse("note-detail", args=[note_id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update_not_allowed(self):
        create = self.client.post(self.notes_url, {
            "medication": self.med.id,
            "text": "Original text"
        }, format="json")
        note_id = create.data["id"]

        url = reverse("note-detail", args=[note_id])
        response = self.client.put(url, {"text": "New text"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
