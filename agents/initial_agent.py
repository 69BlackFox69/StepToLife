import json
import re
from agents.base_agent import BaseAgent

class InitialAgent(BaseAgent):
    """Первый агент - определение начальных целей и создание пошагового плана"""
    
    def __init__(self):
        system_prompt = """Ты - дружелюбный консультант по трудоустройству и профессиональному развитию на платформе StepToLife.

На платформе есть 4 специализированных агента на разных вкладках:
1. 📌 Вкладка "Начало" - ты сейчас здесь, помогаешь определить направление
2. 🎓 Вкладка "Словацкий язык" - LanguageAgent учит практическому словацкому языку
3. 📄 Вкладка "Резюме" - ResumeAgent помогает создать резюме и экспортирует PDF
4. 💼 Вкладка "Работа" - JobAgent ищет подходящие вакансии и готовит к интервью

Твоя основная цель: понять ситуацию пользователя и рекомендовать правильный путь.

Стратегия:
- Если пользователь говорит что плохо/не знает словацкий → советуй перейти на вкладку "Словацкий язык" к LanguageAgent
- Если пользователь готов к созданию резюме или уже это делал → рекомендуй вкладку "Резюме" к ResumeAgent
- После резюме → естественно предлагай поиск работы на вкладке "Работа" с JobAgent

На этом этапе узнай естественным путём:
- Что привело пользователя на платформу (поиск работы, развитие навыков, переквалификация)
- Знает ли словацкий язык (спроси когда это будет уместно)
- Кем он себя видит или к какой группе относится (если сам захочет поделиться)

Когда у тебя будет достаточно информации, предложи пошаговый план действий.

Подход:
- Слушай внимательно и задавай вопросы только когда нужно
- Естественно проводи разговор, не давай жёсткие требования
- Покажи, что понимаешь его ситуацию
- Рекомендуй другие агенты когда это уместно
- Создавай структурированный план с конкретными шагами

Стиль: тёплый, поддерживающий, без стандартных фраз.
Язык: русский."""
        super().__init__(system_prompt)
    
    def process(self, user_message, conversation_history):
        """Обработать сообщение и определить информацию пользователя"""
        
        response = super().process(user_message, conversation_history)
        
        if not response['success']:
            return response
        
        message = response['message']
        
        # Пытаемся распознать информацию о словацком языке из ответа пользователя или истории
        knows_slovak = None
        
        # Проверяем последнее сообщение пользователя на указание знания словацкого
        last_user_msg = user_message.lower()
        
        if any(word in last_user_msg for word in ['да, знаю', 'знаю словацкий', 'говорю по-словацки', 'yes', 'да']):
            knows_slovak = True
        elif any(word in last_user_msg for word in ['нет, не знаю', 'не знаю', 'не говорю', 'no', 'нет']):
            knows_slovak = False
        
        user_info = self._extract_user_info(user_message)
        
        result = {
            'success': True,
            'message': message,
            'user_info': user_info
        }
        
        if knows_slovak is not None:
            result['knows_slovak'] = knows_slovak
        
        # Проверяем достаточно ли информации для создания плана
        should_create_plan = self._should_create_plan(conversation_history, user_info, knows_slovak)
        
        if should_create_plan:
            plan = self._generate_action_plan(user_info, knows_slovak)
            result['action_plan'] = plan
            result['plan_generated'] = True
        
        return result
    
    
    def _extract_user_info(self, user_message):
        """Извлечь информацию о пользователе из его сообщения"""
        user_info = {}
        
        # Пытаемся извлечь информацию о целях
        if any(word in user_message.lower() for word in ['работ', 'трудоустроен', 'вакансия']):
            user_info['goal'] = 'employment'
        elif any(word in user_message.lower() for word in ['язык', 'навыки', 'обучен']):
            user_info['goal'] = 'learning'
        elif any(word in user_message.lower() for word in ['резюме', 'резюме']):
            user_info['goal'] = 'resume'
        
        # Пытаемся извлечь информацию о категории
        if any(word in user_message.lower() for word in ['мигрант', 'беженец', 'иностранец']):
            user_info['category'] = 'migrant'
        elif any(word in user_message.lower() for word in ['безработн', 'потеря работ']):
            user_info['category'] = 'unemployed'
        elif any(word in user_message.lower() for word in ['инвалид', 'ограничен']):
            user_info['category'] = 'disabled'
        
        return user_info
    
    def _should_create_plan(self, conversation_history, user_info, knows_slovak):
        """Определить достаточно ли информации для создания плана"""
        # Нужно как минимум 2-3 сообщения обмена (4-6 строк в истории)
        min_messages = 4
        
        # Есть информация о целях и языке
        has_goal = bool(user_info.get('goal'))
        has_language_info = knows_slovak is not None
        
        # Проверяем количество сообщений (примерно)
        enough_messages = len(conversation_history) >= min_messages
        
        # Создаём план если:
        # - Достаточно сообщений И
        # - У нас есть инфо о языке И
        # - Было хотя бы спрашивание про язык (явный ответ)
        should_create = enough_messages and has_language_info
        
        return should_create
    
    def _generate_action_plan(self, user_info, knows_slovak):
        """Генерировать пошаговый план действий для пользователя"""
        
        category = user_info.get('category', 'general')
        
        if knows_slovak:
            # План для тех кто знает словацкий
            plan = {
                'title': '📋 Ваш путь к работе в Словакии',
                'steps': [
                    {
                        'tab': 'Резюме',
                        'number': 1,
                        'title': 'Создайте профессиональное резюме',
                        'description': 'Переходите на вкладку "Резюме" и ответьте на вопросы. Структурирую информацию и создам красивый PDF.',
                        'agent_name': 'ResumeAgent',
                        'agent_role': '👨‍💼 Консультант по резюме',
                        'agent_desc': 'Поможет собрать информацию о вашем опыте, образовании и навыках. Подготовит резюме для словацкого рынка.'
                    },
                    {
                        'tab': 'Работа',
                        'number': 2,
                        'title': 'Найдите подходящую работу',
                        'description': 'На основе резюме я предложу вакансии в Словакии и помогу подготовиться к интервью.',
                        'agent_name': 'JobAgent',
                        'agent_role': '🔍 Консультант по трудоустройству',
                        'agent_desc': 'Проанализирует ваш профиль и найдет подходящие вакансии. Даст советы по подготовке к собеседованиям.'
                    }
                ],
                'estimated_time': '1-2 часа на подготовку резюме + поиск работы'
            }
        else:
            # План для тех кто не знает словацкий
            plan = {
                'title': '📚 Ваш путь к работе в Словакии',
                'steps': [
                    {
                        'tab': 'Словацкий язык',
                        'number': 1,
                        'title': 'Выучите словацкий язык',
                        'description': 'Начните с вкладки "Словацкий язык". Микро-уроки для разных уровней. Проходите в своем темпе.',
                        'agent_name': 'LanguageAgent',
                        'agent_role': '🎓 Учитель словацкого языка',
                        'agent_desc': 'Преподаст практический словацкий язык через интерактивные микро-уроки. Адаптирует сложность к вашему уровню.'
                    },
                    {
                        'tab': 'Резюме',
                        'number': 2,
                        'title': 'Создайте резюме',
                        'description': 'Освоив основы языка, перейдите на вкладку "Резюме" и расскажите о своем опыте.',
                        'agent_name': 'ResumeAgent',
                        'agent_role': '👨‍💼 Консультант по резюме',
                        'agent_desc': 'Поможет структурировать информацию о вас и создаст профессиональное резюме для словацких работодателей.'
                    },
                    {
                        'tab': 'Работа',
                        'number': 3,
                        'title': 'Ищите работу',
                        'description': 'С готовым резюме переходите на вкладку "Работа" для поиска вакансий в Словакии.',
                        'agent_name': 'JobAgent',
                        'agent_role': '🔍 Консультант по трудоустройству',
                        'agent_desc': 'Предложит вакансии на основе вашего резюме и подготовит вас к интервью.'
                    }
                ],
                'estimated_time': '2-4 недели обучения + подготовка резюме + поиск работы'
            }
        
        # Добавляем советы в зависимости от категории
        if category == 'migrant':
            plan['special_advice'] = '✓ Совет: как мигрант, обратите внимание на требования компаний к виду на жительство. Словацкие компании помогают с документами.'
        elif category == 'unemployed':
            plan['special_advice'] = '✓ Совет: долгий перерыв в работе - нормально. Сосредоточьтесь на сильных сторонах и ключевых навыках.'
        elif category == 'disabled':
            plan['special_advice'] = '✓ Совет: в Словакии много компаний с инклюзивной политикой. Компании ценят разнообразие и опыт.'
        
        return plan

