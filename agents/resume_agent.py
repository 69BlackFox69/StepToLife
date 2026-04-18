import json
import os
from agents.base_agent import BaseAgent
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

class ResumeAgent(BaseAgent):
    """Третий агент - создание резюме в интерактивном формате"""
    
    def __init__(self):
        system_prompt = """Ты - опытный консультант по составлению профессионального резюме на платформе StepToLife.

Твоя цель: помочь пользователю создать сильное резюме для словацкого рынка труда.

Подход:
- Задавай вопросы естественно, один за другим, не спешком
- Слушай ответы внимательно и задавай уточняющие вопросы если нужно
- Помогай структурировать информацию о:
  * Личные данные (имя, контакты - email, телефон)
  * Профессиональный опыт (должности, компании, достижения)
  * Образование (специальность, школа, годы)
  * Ключевые навыки и знания
  * Языки (какие языки и уровень)
  * Сертификаты, награды, дополнительные достижения
- Давай советы по оформлению для словацкого рынка
- Предлагай улучшения и переформулировки

Когда соберёшь достаточно информации:
- Скажи что-то вроде "Кажется, у нас достаточно информации для резюме" или "Думаю, мы готовы создать ваше резюме"
- Предложи скачать PDF версию
- Спроси нужны ли какие-то изменения

Важно: Помни, что пользователь может быть из маргинализированной группы, поэтому будь особенно поддерживающим и позитивным. Помоги ему увидеть его сильные стороны.

Язык: русский."""
        super().__init__(system_prompt)
        self.resume_data = {}
    
    def process(self, user_message, conversation_history):
        """Обработать сообщение и собрать данные для резюме"""
        
        response = super().process(user_message, conversation_history)
        
        if not response['success']:
            return response
        
        message = response['message']
        
        # Проверяем, готово ли резюме (более гибкие условия)
        ready_keywords = [
            'достаточно информации',
            'готовы создать',
            'готово создать',
            'скачать pdf',
            'скачать резюме',
            'готово',
            'готов ваше резюме',
            'pdf готов'
        ]
        
        resume_ready = any(keyword in message.lower() for keyword in ready_keywords)
        
        result = {
            'success': True,
            'message': message,
            'resume_ready': resume_ready
        }
        
        # Пытаемся извлечь информацию из сообщений пользователя
        self._extract_resume_data(user_message)
        
        if self.resume_data:
            result['resume_data'] = self.resume_data
        
        return result
    
    def _extract_resume_data(self, user_message):
        """Пытаемся извлечь структурированные данные из сообщения"""
        # Это упрощённая версия - в реальном приложении нужен парсер посложнее
        # или явное запрашивание структурированных данных
        
        msg_lower = user_message.lower()
        
        # Извлечение имени (простая эвристика)
        if 'зовут' in msg_lower or 'меня' in msg_lower:
            # Получим имя из истории или явного запроса
            pass
        
        # Здесь могут быть добавлены другие эвристики для извлечения информации
    
    def generate_pdf(self, resume_data, user_id):
        """Генерировать PDF файл резюме"""
        
        # Создаём директорию для PDF если её нет
        os.makedirs('resumes', exist_ok=True)
        
        filename = f'resumes/resume_{user_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        # Создаём документ
        doc = SimpleDocTemplate(filename, pagesize=letter,
                               rightMargin=0.5*inch, leftMargin=0.5*inch,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Стили
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1f4788',
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#1f4788',
            spaceAfter=6,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            spaceAfter=6
        )
        
        # Содержимое документа
        story = []
        
        # Заголовок
        name = resume_data.get('name', 'Резюме кандидата')
        story.append(Paragraph(name, title_style))
        
        # Контакты
        contact_info = []
        if 'email' in resume_data:
            contact_info.append(resume_data['email'])
        if 'phone' in resume_data:
            contact_info.append(resume_data['phone'])
        if 'location' in resume_data:
            contact_info.append(resume_data['location'])
        
        if contact_info:
            story.append(Paragraph(' | '.join(contact_info), body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Профессиональная цель
        if 'objective' in resume_data:
            story.append(Paragraph('ПРОФЕССИОНАЛЬНАЯ ЦЕЛЬ', heading_style))
            story.append(Paragraph(resume_data['objective'], body_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Опыт работы
        if 'experience' in resume_data:
            story.append(Paragraph('ОПЫТ РАБОТЫ', heading_style))
            experiences = resume_data['experience']
            if isinstance(experiences, list):
                for exp in experiences:
                    story.append(Paragraph(f"<b>{exp.get('position', '')}</b> - {exp.get('company', '')}", body_style))
                    story.append(Paragraph(f"{exp.get('duration', '')}", body_style))
                    if 'description' in exp:
                        story.append(Paragraph(exp['description'], body_style))
                    story.append(Spacer(1, 0.05*inch))
        
        # Образование
        if 'education' in resume_data:
            story.append(Paragraph('ОБРАЗОВАНИЕ', heading_style))
            educations = resume_data['education']
            if isinstance(educations, list):
                for edu in educations:
                    story.append(Paragraph(f"<b>{edu.get('degree', '')}</b> - {edu.get('school', '')}", body_style))
                    story.append(Paragraph(f"{edu.get('year', '')}", body_style))
                    story.append(Spacer(1, 0.05*inch))
        
        # Навыки
        if 'skills' in resume_data:
            story.append(Paragraph('НАВЫКИ', heading_style))
            skills = resume_data['skills']
            if isinstance(skills, list):
                story.append(Paragraph(', '.join(skills), body_style))
            else:
                story.append(Paragraph(str(skills), body_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Языки
        if 'languages' in resume_data:
            story.append(Paragraph('ЯЗЫКИ', heading_style))
            languages = resume_data['languages']
            if isinstance(languages, dict):
                for lang, level in languages.items():
                    story.append(Paragraph(f"{lang} - {level}", body_style))
            else:
                story.append(Paragraph(str(languages), body_style))
        
        # Построение документа
        doc.build(story)
        
        return filename
