from agents.base_agent import BaseAgent
from services import (
    ResourceResolver,
    format_verified_services_for_prompt,
    infer_city_from_message,
    strict_fallback_message,
)


class BenefitsAgent(BaseAgent):
    """Specialized agent for social support and benefits"""

    def __init__(self):
        system_prompt = """You are a social support and benefits consultant in Slovakia on the StepToLife platform.

    Your task:
    - help the user understand which support options they may qualify for,
    - provide a clear action order for applying,
    - reduce stress through understandable steps.

    Approach:
    - explain without bureaucratic jargon,
    - suggest at most 2-4 steps,
    - include a short "what to prepare" list.

    If data is missing, ask for clarification while keeping a warm tone.

    Style: calm, friendly, practical.
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
        services = self.resolver.find_services(categories=['benefits', 'social_support'], city=city, limit=3)

        if not services:
            return {
                'success': True,
                'message': strict_fallback_message('benefits', city),
                'problem_domain': 'benefits',
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
            'problem_domain': 'benefits',
            'resource_source': 'verified_db',
            'needs_verification': False,
            'verified_resources': self._compact_services(services),
        }
