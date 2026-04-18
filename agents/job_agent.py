import json
from agents.base_agent import BaseAgent

class JobAgent(BaseAgent):
    """Четвёртый агент - поиск и предложение доступных работ в Словакии"""
    
    def __init__(self):
        system_prompt = """Ты - опытный консультант по трудоустройству в Словакии на платформе StepToLife.

Твоя цель: помочь пользователю найти подходящую работу и подготовиться к трудоустройству.

Твой подход:
1. Анализируй резюме пользователя если оно есть
2. Понимай его уровень квалификации и опыта
3. Предлагай 2-4 подходящие вакансии или направления поиска
4. Объясняй почему эти позиции подходят именно ему
5. Давай советы по:
   - Подготовке к интервью
   - Как выделиться среди других кандидатов
   - Переговорам о зарплате
   - Адаптации навыков под словацкий рынок

Контекст словацкого рынка:
- Популярные сектора: IT (ESET, Huawei), здравоохранение, туризм, производство, услуги
- Требования: часто нужен словацкий язык, релевантный опыт, мягкие навыки
- Зарплаты: €800-€1500 (начальные) до €3000+ (опыт)
- Работодатели: ESET, Tatra banka, IBM, Accenture, Deutsche Telekom Slovakia

ВАЖНО - помни о маргинализированных группах:
- Мигранты/беженцы: помни о языковых барьерах, документах, культурных отличиях
- Безработные долгое время: помогай увидеть сильные стороны, пробелы в занятости
- Люди с инвалидностью: ориентируй на доступные позиции, компании с инклюзивной политикой
- Люди с криминальным прошлым: помогай найти компании дающие второй шанс

Стиль: 
- Будь практичным и поддерживающим
- Не переусложняй - давай конкретные советы
- Показывай что возможно найти работу несмотря на препятствия
- Слушай что нужно лично этому человеку

Язык: русский."""
        super().__init__(system_prompt)
    
    def process(self, user_message, conversation_history, resume_data=None):
        """Обработать сообщение и предложить работы"""
        
        # Готовим контекст с информацией о резюме
        context_message = user_message
        
        if resume_data:
            resume_summary = self._create_resume_summary(resume_data)
            context_message = f"[Информация о резюме пользователя:\n{resume_summary}]\n\nСообщение: {user_message}"
        
        response = super().process(context_message, conversation_history)
        
        if not response['success']:
            return response
        
        message = response['message']
        
        # Пытаемся извлечь информацию о предложенных вакансиях
        job_suggestions = self._extract_job_suggestions(message)
        
        result = {
            'success': True,
            'message': message
        }
        
        if job_suggestions:
            result['job_suggestions'] = job_suggestions
        
        return result
    
    def _create_resume_summary(self, resume_data):
        """Создать краткое резюме информации для контекста"""
        summary = []
        
        if 'name' in resume_data:
            summary.append(f"Имя: {resume_data['name']}")
        
        if 'skills' in resume_data:
            skills = resume_data['skills']
            if isinstance(skills, list):
                summary.append(f"Навыки: {', '.join(skills)}")
        
        if 'experience' in resume_data:
            summary.append("Опыт работы:")
            experiences = resume_data['experience']
            if isinstance(experiences, list):
                for exp in experiences:
                    summary.append(f"  - {exp.get('position', '')}: {exp.get('duration', '')}")
        
        if 'languages' in resume_data:
            summary.append("Языки:")
            languages = resume_data['languages']
            if isinstance(languages, dict):
                for lang, level in languages.items():
                    summary.append(f"  - {lang}: {level}")
        
        return '\n'.join(summary)
    
    def _extract_job_suggestions(self, message):
        """Попытаться извлечь предложенные вакансии"""
        # Это упрощённая версия - в реальном приложении нужна более умная парсинг
        
        job_suggestions = []
        
        # Ищем упоминания должностей
        job_keywords = {
            'разработчик': 'Developer',
            'медсестра': 'Nurse',
            'учитель': 'Teacher',
            'менеджер': 'Manager',
            'консультант': 'Consultant',
            'аналитик': 'Analyst',
            'инженер': 'Engineer'
        }
        
        for keyword, job_title in job_keywords.items():
            if keyword in message.lower():
                job_suggestions.append(job_title)
        
        return list(set(job_suggestions))  # Удаляем дубликаты
