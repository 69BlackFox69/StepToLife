from agents.base_agent import BaseAgent
from services import (
    ResourceResolver,
    format_verified_services_for_prompt,
    infer_city_from_message,
    strict_fallback_message,
)


class DocumentsAgent(BaseAgent):
    """Specialized agent for documents and legalization"""

    def __init__(self):
        system_prompt = """You are a documents and legalization consultant in Slovakia on the StepToLife platform.

    Your task:
    - help the user understand which documents are needed in their situation,
    - break the process into simple steps,
    - provide careful wording for communication with institutions.

    Rules:
    - do not promise legal outcomes,
    - if data is missing, clearly state what needs clarification,
    - explain in plain language without complex legal terms.

    Response format:
    1) what to check first,
    2) what to do today,
    3) which documents to bring,
    4) what to say at the institution.

    Style: respectful, structured, supportive.
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
        services = self.resolver.find_services(categories=['legal_aid', 'documents'], city=city, limit=3)

        if not services:
            return {
                'success': True,
                'message': strict_fallback_message('documents', city),
                'problem_domain': 'documents',
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
            'problem_domain': 'documents',
            'resource_source': 'verified_db',
            'needs_verification': False,
            'verified_resources': self._compact_services(services),
        }
