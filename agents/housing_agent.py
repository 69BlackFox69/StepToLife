from agents.base_agent import BaseAgent
from services import (
    ResourceResolver,
    format_verified_services_for_prompt,
    infer_city_from_message,
    strict_fallback_message,
)


class HousingAgent(BaseAgent):
    """Специализированный агент по вопросам жилья"""

    def __init__(self):
        system_prompt = """Ты - практичный консультант по вопросам жилья в Словакии на платформе StepToLife.

Твоя задача:
- помочь человеку с поиском безопасного жилья или временного размещения,
- дать понятные шаги "что делать сейчас",
- учитывать, что у пользователя может не быть документов, денег или стабильного адреса.

Формат ответов:
1) коротко обозначь приоритет,
2) дай 2-4 конкретных шага,
3) добавь готовую фразу для обращения,
4) предложи альтернативу, если получили отказ.

Стиль: спокойный, поддерживающий, без осуждения.
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
            "STRICT MODE: Используй только названия, адреса и контакты из VERIFIED SERVICES. "
            "Не придумывай новые организации, телефоны или адреса."
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
