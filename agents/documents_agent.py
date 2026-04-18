from agents.base_agent import BaseAgent


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

    def process(self, user_message, conversation_history):
        response = super().process(user_message, conversation_history)

        if not response['success']:
            return response

        return {
            'success': True,
            'message': response['message'],
            'problem_domain': 'documents'
        }
