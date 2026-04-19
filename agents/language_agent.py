from agents.base_agent import BaseAgent

class LanguageAgent(BaseAgent):
    """Второй агент - обучение словацкому языку через микро-уроки"""
    
    def __init__(self):
        system_prompt = """Ты - увлечённый и терпеливый учитель словацкого языка на платформе StepToLife.

Твоя цель: помочь пользователю выучить практический словацкий язык для трудоустройства, используя микро-уроки.

Подход:
- Адаптируй сложность к уровню пользователя (beginner, intermediate, advanced)
- Структурируй каждый урок так:
  1. Представь тему в 1-2 предложениях
  2. Дай основной материал (5-7 полезных словосочетаний или фраз)
  3. Включи практику (2-3 интерактивных вопроса)
  4. Покажи как это использовать на работе (примеры из реальных ситуаций)
- Используй реальные примеры из трудоустройства и работы
- Будь поддерживающим - каждый может выучить язык!

Рекомендуемые темы:
- Beginner: приветствие, самопрезентация, числа, дни недели, профессии, основные фразы
- Intermediate: деловое общение, разговор на собеседовании, написание письма
- Advanced: переговоры, специализированная лексика, культурные нюансы

Помни: многие пользователи - из уязвимых групп, поэтому:
- Будь особенно позитивен и поддерживающ
- Никогда не критикуй ошибки, а радуйся прогрессу
- Показывай что язык - это достижимо даже для взрослых
- Давай мотивирующие примеры успеха людей как они

Язык: русский с примерами на словацком."""
        super().__init__(system_prompt)
    
    def process(self, user_message, conversation_history, lesson_level='beginner'):
        """Обработать сообщение и дать первый микро-урок"""

        normalized = ' '.join((user_message or '').lower().replace('!', ' ').replace('.', ' ').replace(',', ' ').replace('?', ' ').replace(':', ' ').replace(';', ' ').replace('"', ' ').replace("'", ' ').replace('`', ' ').split())
        start_phrases = {
            'да',
            'готов',
            'готова',
            'начать',
            'поехали',
            'да, помоги мне начать говорить по словацки',
            'помоги мне начать говорить по словацки',
            'помоги мне выучить словацкий',
            'хочу учить словацкий',
            'yes',
            'ok',
            'okay',
        }

        if normalized in start_phrases or normalized.startswith('да') or 'помоги мне' in normalized:
            lesson = (
                "Отлично. Начнем с самого простого.\n\n"
                "Мини-урок 1: приветствие.\n"
                "Запомни 3 короткие фразы:\n"
                "- Dobrý deň - Добрый день\n"
                "- Ahoj - Привет\n"
                "- Ďakujem - Спасибо\n\n"
                "Как использовать на работе: скажи «Dobrý deň» при входе и «Ďakujem» в конце разговора.\n\n"
                "Теперь попробуй написать: Dobrý deň."
            )
            return {
                'success': True,
                'message': lesson,
                'lesson_level': lesson_level,
                'lesson_step': 1
            }

        if not normalized or normalized in {'нет', 'не', 'no'}:
            return {
                'success': True,
                'message': 'Напишите "да", если хотите начать короткий урок словацкого.',
                'lesson_level': lesson_level,
                'lesson_step': 0
            }

        enhanced_history = conversation_history.copy() if conversation_history else []
        level_info = f"\n[Уровень урока: {lesson_level}]"
        response = super().process(user_message + level_info, enhanced_history)

        if not response['success']:
            return response

        return {
            'success': True,
            'message': response['message'],
            'lesson_level': lesson_level,
            'lesson_step': 1
        }
