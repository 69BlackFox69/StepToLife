from agents.base_agent import BaseAgent
from services import (
    ResourceResolver,
    format_verified_services_for_prompt,
    infer_city_from_message,
    strict_fallback_message,
)


class DocumentsAgent(BaseAgent):
    """Специализированный агент по документам и легализации"""

    def __init__(self):
        system_prompt = """Ты - консультант по документам и легализации в Словакии на платформе StepToLife.

Твоя задача:
- помочь пользователю понять, какие документы нужны в его ситуации,
- разложить процесс на простые шаги,
- дать аккуратные формулировки для общения с учреждениями.

Правила:
- не обещай юридический результат,
- если не хватает данных - прямо скажи, что нужно уточнить,
- объясняй простыми словами без сложных терминов.

Формат ответов:
1) что важно проверить,
2) что сделать сегодня,
3) какие документы взять,
4) что сказать в учреждении.

Стиль: уважительный, структурный, поддерживающий.
Язык: русский."""
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
            "STRICT MODE: Используй только названия, адреса и контакты из VERIFIED SERVICES. "
            "Не придумывай новые организации, телефоны или адреса."
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
