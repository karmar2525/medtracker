import requests


class DrugInfoService:
    """
    Wrapper around the OpenFDA Drug Label API.
    """

    BASE_URL = "https://api.fda.gov/drug/label.json"

    @classmethod
    def get_drug_info(cls, drug_name: str):
        if not drug_name:
            raise ValueError("drug_name is required")

        params = {"search": f"openfda.generic_name:{drug_name.lower()}", "limit": 1}

        resp = requests.get(cls.BASE_URL, params=params, timeout=10)
        if resp.status_code != 200:
            raise ValueError(f"OpenFDA API error: {resp.status_code}")

        data = resp.json()
        results = data.get("results")
        if not results:
            raise ValueError("No results found for this medication.")

        record = results[0]
        openfda = record.get("openfda", {})

        generic_name = openfda.get("generic_name")
        manufacturer = openfda.get("manufacturer_name")
        warnings = record.get("warnings")
        purpose = record.get("purpose")

        return {
            "name": generic_name[0]
            if isinstance(generic_name, list) and generic_name
            else drug_name,
            "manufacturer": manufacturer[0]
            if isinstance(manufacturer, list) and manufacturer
            else "Unknown",
            "warnings": warnings if warnings else ["No warnings available"],
            "purpose": purpose if purpose else ["Not specified"],
        }
