from django.test import TestCase
from unittest.mock import patch
from medtrackerapp.services import DrugInfoService


class DrugInfoServiceTests(TestCase):

    @patch('medtrackerapp.services.requests.get')
    def test_get_drug_info_mocked(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "results": [
                {
                    "openfda": {
                        "brand_name": ["Paracetamol"],
                        "manufacturer_name": ["Test Pharma"]
                    },
                    "warnings": ["Do not exceed recommended dose"],
                    "purpose": ["Pain relief"]
                }
            ]
        }

        result = DrugInfoService.get_drug_info("Paracetamol")

        self.assertEqual(result["name"], "Paracetamol")
        self.assertEqual(result["manufacturer"], "Test Pharma")
        self.assertIn("Do not exceed recommended dose", result["warnings"])
        self.assertIn("Pain relief", result["purpose"])
