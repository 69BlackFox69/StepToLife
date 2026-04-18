from agents.base_agent import BaseAgent
from services import (
    ResourceResolver,
    format_verified_services_for_prompt,
    infer_city_from_message,
    strict_fallback_message,
)


class EmergencyAgent(BaseAgent):
    """Специализированный агент экстренной помощи"""

    def __init__(self):
        system_prompt = """Ты - агент экстренной поддержки StepToLife.

Твоя задача:
- в кризисной ситуации дать короткие и безопасные шаги,
- говорить простыми фразами,
- давать по одному действию за раз,
- направлять к экстренным службам, если есть риск для жизни или здоровья.

Критические сигналы: насилие, угроза на улице, отсутствие еды/ночлега, паника, самоповреждение.

Правила ответа:
1) сначала безопасность,
2) потом ближайшее действие,
3) затем контакт/куда обратиться,
4) добавь фразу, которую можно сказать сотруднику службы.

Важно: поддерживай пользователя, но не ставь диагнозы и не проводи лечение.
Стиль: очень спокойный, короткий, неосуждающий.
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
        services = self.resolver.find_services(categories=['emergency', 'shelter'], city=city, limit=3)

        if not services:
            fallback = strict_fallback_message('emergency', city)
            return {
                'success': True,
                'message': f"{fallback}\n\nЕсли есть непосредственная угроза жизни, звоните 112.",
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
            "STRICT MODE: Используй только названия, адреса и контакты из VERIFIED SERVICES. "
            "Не придумывай новые организации, телефоны или адреса."
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
