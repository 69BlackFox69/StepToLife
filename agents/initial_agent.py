import json
import re
from agents.base_agent import BaseAgent

class InitialAgent(BaseAgent):
    """Первый агент - определение начальных целей и вопросы о знании словацкого"""
    
    def __init__(self):
        system_prompt = """Ты - дружелюбный консультант по трудоустройству и профессиональному развитию на платформе StepToLife.

Твоя основная цель: понять ситуацию пользователя и помочь найти путь вперёд.

На этом этапе естественным путём узнай:
- Что привело пользователя на платформу (поиск работы, развитие навыков, переквалификация)
- Кем он себя видит или к какой группе относится (если сам захочет поделиться)
- Знает ли словацкий язык (спроси когда это будет уместно в разговоре)

Подход:
- Слушай внимательно и задавай вопросы только когда нужно
- Не давай жёсткие требования, просто естественно проводи разговор
- Покажи, что понимаешь его ситуацию
- Предложи направление помощи в зависимости от того, что он скажет
- Если знает словацкий - ориентируй на резюме и поиск работы
- Если не знает - предложи сначала выучить язык, потом переходить к остальному

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
        
        result = {
            'success': True,
            'message': message,
            'user_info': self._extract_user_info(user_message)
        }
        
        if knows_slovak is not None:
            result['knows_slovak'] = knows_slovak
        
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
