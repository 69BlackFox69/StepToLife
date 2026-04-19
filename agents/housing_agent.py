from agents.base_agent import BaseAgent
from services import (
    ResourceResolver,
    format_verified_services_for_prompt,
    infer_city_from_message,
    strict_fallback_message,
)


class HousingAgent(BaseAgent):
    """Specialized agent for housing support"""

    def __init__(self):
        system_prompt = """You are a practical housing consultant in Slovakia on the StepToLife platform.

    Your task:
    - help the user find safe housing or temporary accommodation,
    - provide clear "what to do now" steps,
    - consider that the user may lack documents, money, or a stable address.

    Response format:
    1) briefly state the priority,
    2) provide 2-4 concrete steps,
    3) add a ready-to-use phrase for contacting services,
    4) suggest an alternative in case of refusal.

    Style: calm, supportive, non-judgmental.
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
        services = self.resolver.find_services(categories=['shelter'], city=city, limit=3)

        if not services:
            return {
                'success': True,
                'message': strict_fallback_message('housing', city),
                'problem_domain': 'housing',
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
            'problem_domain': 'housing',
            'resource_source': 'verified_db',
            'needs_verification': False,
            'verified_resources': self._compact_services(services),
        }
