from agents.base_agent import BaseAgent
from services import (
    ResourceResolver,
    format_verified_services_for_prompt,
    infer_city_from_message,
    strict_fallback_message,
)


class EmergencyAgent(BaseAgent):
    """Specialized emergency support agent"""

    def __init__(self):
        system_prompt = """You are the StepToLife emergency support agent.

    Your task:
    - in crisis situations, provide short and safe steps,
    - use simple language,
    - provide one action at a time,
    - direct users to emergency services if there is risk to life or health.

    Critical signals: violence, street threat, lack of food/shelter, panic, self-harm risk.

    Response rules:
    1) safety first,
    2) then the nearest concrete action,
    3) then contact information and where to go,
    4) add a phrase the user can say to service staff.

    Important: support the user, but do not diagnose or provide treatment.
    Style: very calm, short, non-judgmental.
    Language: English."""
        super().__init__(system_prompt)
        self.resolver = ResourceResolver()

    def _compact_services(self, services):
        compact = []
        for service in services:
            compact.append({
                'service_id': service.get('service_id'),
                'name': service.get('name'),
                'category': service.get('category'),
                'city': service.get('city'),
                'phone': service.get('contact', {}).get('phone'),
                'website': service.get('contact', {}).get('website'),
                'street': service.get('address', {}).get('street'),
            })
        return compact

    def process(self, user_message, conversation_history):
        city = infer_city_from_message(user_message, default_city='Kosice')
        services = self.resolver.find_services(categories=['emergency', 'shelter'], city=city, limit=3)

        if not services:
            fallback = strict_fallback_message('emergency', city)
            return {
                'success': True,
                'message': f"{fallback}\n\nIf there is an immediate threat to life, call 112.",
                'problem_domain': 'emergency',
                'safety_mode': True,
                'resource_source': 'fallback',
                'needs_verification': True,
                'verified_resources': [],
            }

        verified_context = format_verified_services_for_prompt(services)
        grounded_message = (
            f"{user_message}\n\n"
            f"{verified_context}\n\n"
            "STRICT MODE: Use only names, addresses, and contacts from VERIFIED SERVICES. "
            "Do not invent new organizations, phone numbers, or addresses."
        )

        response = super().process(grounded_message, conversation_history)

        if not response['success']:
            return response

        return {
            'success': True,
            'message': response['message'],
            'problem_domain': 'emergency',
            'safety_mode': True,
            'resource_source': 'verified_db',
            'needs_verification': False,
            'verified_resources': self._compact_services(services),
        }
