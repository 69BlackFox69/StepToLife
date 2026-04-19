import json
import os
import unicodedata


class ResourceResolver:
    """Resolver for verified local services. Only returns vetted records from JSON."""

    def __init__(self, data_file=None):
        if data_file is None:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_file = os.path.join(root, "data", "slovakia_services_demo.json")
        self.data_file = data_file
        self.services = self._load_services()

    def _load_services(self):
        if not os.path.exists(self.data_file):
            return []

        with open(self.data_file, "r", encoding="utf-8") as f:
            payload = json.load(f)

        if isinstance(payload, dict):
            payload = [payload]

        valid = []
        for service in payload:
            if self._is_valid_service(service):
                valid.append(service)
        return valid

    def _is_valid_service(self, service):
        if not isinstance(service, dict):
            return False

        required_top = ["service_id", "name", "category", "city", "contact", "address"]
        if any(key not in service for key in required_top):
            return False

        contact = service.get("contact", {})
        has_contact = bool(contact.get("phone") or contact.get("website") or contact.get("email"))
        return has_contact

    def _norm(self, text):
        if text is None:
            return ""
        text = str(text).strip().lower()
        text = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in text if not unicodedata.combining(ch))

    def find_services(self, categories=None, city=None, limit=3):
        categories = categories or []
        categories_norm = {self._norm(c) for c in categories}
        city_norm = self._norm(city) if city else ""

        matches = []
        for service in self.services:
            service_category = self._norm(service.get("category"))
            service_city = self._norm(service.get("city"))

            if categories_norm and service_category not in categories_norm:
                continue

            if city_norm and service_city != city_norm:
                continue

            matches.append(service)

        return matches[:limit]


def infer_city_from_message(message, default_city="Kosice"):
    text = (message or "").lower()
    if "košice" in text or "kosice" in text:
        return "Kosice"
    if "bratislava" in text:
        return "Bratislava"
    return default_city


def format_verified_services_for_prompt(services):
    if not services:
        return ""

    lines = ["VERIFIED SERVICES (use only these contacts and names):"]
    for s in services:
        contact = s.get("contact", {})
        address = s.get("address", {})
        lines.append(
            f"- {s.get('name')} | category={s.get('category')} | city={s.get('city')} | "
            f"phone={contact.get('phone')} | website={contact.get('website')} | "
            f"street={address.get('street')}"
        )
    return "\n".join(lines)


def strict_fallback_message(problem_domain, city):
    base = (
        "Need clarification: the verified local database currently has no exact contact "
        f"for domain '{problem_domain}' in {city}. "
        "I will not invent addresses or phone numbers."
    )

    next_step = (
        "Next step: specify district/service type and repeat your request, "
        "or contact the nearest city social support center."
    )

    return f"{base}\n\n{next_step}"
