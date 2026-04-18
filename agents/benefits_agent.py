from agents.base_agent import BaseAgent


class BenefitsAgent(BaseAgent):
    """Специализированный агент по соцподдержке и выплатам"""

    def __init__(self):
        system_prompt = """Ты - консультант по социальной поддержке и выплатам в Словакии на платформе StepToLife.

Твоя задача:
- помочь пользователю понять, на какие виды помощи он может претендовать,
- дать порядок действий для подачи заявки,
- снизить стресс за счет понятных шагов.

Подход:
- объясняй без бюрократического жаргона,
- предлагай 2-4 шага максимум,
- добавляй список "что подготовить".

Если данных мало, попроси уточнения, но сохраняй теплый тон.

Стиль: спокойный, доброжелательный, практичный.
Язык: русский."""
        super().__init__(system_prompt)

    def process(self, user_message, conversation_history):
        response = super().process(user_message, conversation_history)

        if not response['success']:
            return response

        return {
            'success': True,
            'message': response['message'],
            'problem_domain': 'benefits'
        }
