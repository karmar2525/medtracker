from unittest.mock import patch
from django.test import TestCase
from medtrackerapp.services import DrugInfoService
import requests


class DrugInfoServiceTests(TestCase):
    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_timeout(self, mock_get):
        """Simulate a network timeout"""
        mock_get.side_effect = requests.exceptions.Timeout
        with self.assertRaises(requests.exceptions.Timeout):
            DrugInfoService.get_drug_info("Paracetamol")

    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_invalid_json(self, mock_get):
        """Simulate invalid JSON from API"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
        with self.assertRaises(ValueError):
            DrugInfoService.get_drug_info("Paracetamol")

    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_success(self, mock_get):
        """Test API returns valid data successfully"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "results": [
                {
                    "openfda": {
                        "brand_name": ["Paracetamol"],
                        "manufacturer_name": ["Test Pharma"],
                        "generic_name": ["Paracetamol"],
                    },
                    "warnings": ["Do not exceed recommended dose"],
                    "purpose": ["Pain relief"],
                }
            ]
        }

        result = DrugInfoService.get_drug_info("Paracetamol")

        self.assertEqual(result["name"], "Paracetamol")
        self.assertEqual(result["manufacturer"], "Test Pharma")
        self.assertIn("Do not exceed recommended dose", result["warnings"])
        self.assertIn("Pain relief", result["purpose"])

    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_no_results(self, mock_get):
        """Test API returns no results"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}

        with self.assertRaises(ValueError):
            DrugInfoService.get_drug_info("UnknownDrug")

    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_api_error(self, mock_get):
        """Test API returns error status"""
        mock_get.return_value.status_code = 500

        with self.assertRaises(ValueError):
            DrugInfoService.get_drug_info("ErrorDrug")

    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_empty_fields(self, mock_get):
        """Test API returns results with empty/missing fields"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"results": [{}]}

        result = DrugInfoService.get_drug_info("UnknownDrug")

        self.assertEqual(result["name"], "UnknownDrug")
        self.assertEqual(result["manufacturer"], "Unknown")
        self.assertEqual(result["warnings"], ["No warnings available"])
        self.assertEqual(result["purpose"], ["Not specified"])

    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_partial_fields(self, mock_get):
        """Test API returns some missing fields"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "results": [
                {
                    "openfda": {"generic_name": ["TestDrug"]},
                    "warnings": [],
                    "purpose": ["Pain relief"],
                }
            ]
        }

        result = DrugInfoService.get_drug_info("TestDrug")

        self.assertEqual(result["name"], "TestDrug")
        self.assertEqual(result["manufacturer"], "Unknown")
        self.assertEqual(result["warnings"], ["No warnings available"])
        self.assertEqual(result["purpose"], ["Pain relief"])
