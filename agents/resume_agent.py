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
    """Third agent: interactive resume creation"""
    
    def __init__(self):
        system_prompt = """You are an experienced professional resume consultant on the StepToLife platform.

Your goal: help the user create a strong resume for the Slovak job market.

Approach:
- Ask questions naturally, one by one, without rushing
- Listen carefully and ask clarifying questions when needed
- Help structure information about:
    * Personal details (name, contacts: email, phone)
    * Professional experience (roles, companies, achievements)
    * Education (specialization, school, years)
    * Key skills and knowledge
    * Languages (which languages and level)
    * Certificates, awards, additional achievements
- Provide formatting advice for the Slovak market
- Suggest improvements and rephrasing

When enough information is collected:
- Say something like "We seem to have enough information for the resume"
- Offer PDF download
- Ask whether any changes are needed

Important: the user may belong to a vulnerable group, so stay especially supportive and positive. Help them see their strengths.

Language: English."""
        super().__init__(system_prompt)
        self.resume_data = {}
    
    def process(self, user_message, conversation_history):
        """Process message and collect resume data"""
        
        response = super().process(user_message, conversation_history)
        
        if not response['success']:
            return response
        
        message = response['message']
        
        # Check whether resume is ready (flexible conditions)
        ready_keywords = [
            'достаточно информации',
            'готовы создать',
            'готово создать',
            'скачать pdf',
            'скачать резюме',
            'готово',
            'готов ваше резюме',
            'pdf готов',
            'enough information',
            'ready to create',
            'download pdf',
            'download resume',
            'resume is ready',
            'pdf is ready'
        ]
        
        resume_ready = any(keyword in message.lower() for keyword in ready_keywords)
        
        result = {
            'success': True,
            'message': message,
            'resume_ready': resume_ready
        }
        
        # Try to extract data from user messages
        self._extract_resume_data(user_message)
        
        if self.resume_data:
            result['resume_data'] = self.resume_data
        
        return result
    
    def _extract_resume_data(self, user_message):
        """Try to extract structured data from message"""
        # Simplified version: production use should rely on explicit structured extraction.
        
        msg_lower = user_message.lower()
        
        # Name extraction (simple heuristic)
        if 'зовут' in msg_lower or 'меня' in msg_lower:
            # Name can be obtained from history or explicit parser.
            pass
        
        # Additional extraction heuristics can be added here.
    
    def generate_pdf(self, resume_data, user_id):
        """Generate resume PDF file"""
        
        # Create output folder if missing
        os.makedirs('resumes', exist_ok=True)
        
        filename = f'resumes/resume_{user_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        # Build PDF document
        doc = SimpleDocTemplate(filename, pagesize=letter,
                               rightMargin=0.5*inch, leftMargin=0.5*inch,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Styles
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
        
        # Document content
        story = []
        
        # Title
        name = resume_data.get('name', 'Candidate Resume')
        story.append(Paragraph(name, title_style))
        
        # Contacts
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
        
        # Professional objective
        if 'objective' in resume_data:
            story.append(Paragraph('PROFESSIONAL OBJECTIVE', heading_style))
            story.append(Paragraph(resume_data['objective'], body_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Work experience
        if 'experience' in resume_data:
            story.append(Paragraph('WORK EXPERIENCE', heading_style))
            experiences = resume_data['experience']
            if isinstance(experiences, list):
                for exp in experiences:
                    story.append(Paragraph(f"<b>{exp.get('position', '')}</b> - {exp.get('company', '')}", body_style))
                    story.append(Paragraph(f"{exp.get('duration', '')}", body_style))
                    if 'description' in exp:
                        story.append(Paragraph(exp['description'], body_style))
                    story.append(Spacer(1, 0.05*inch))
        
        # Education
        if 'education' in resume_data:
            story.append(Paragraph('EDUCATION', heading_style))
            educations = resume_data['education']
            if isinstance(educations, list):
                for edu in educations:
                    story.append(Paragraph(f"<b>{edu.get('degree', '')}</b> - {edu.get('school', '')}", body_style))
                    story.append(Paragraph(f"{edu.get('year', '')}", body_style))
                    story.append(Spacer(1, 0.05*inch))
        
        # Skills
        if 'skills' in resume_data:
            story.append(Paragraph('SKILLS', heading_style))
            skills = resume_data['skills']
            if isinstance(skills, list):
                story.append(Paragraph(', '.join(skills), body_style))
            else:
                story.append(Paragraph(str(skills), body_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Languages
        if 'languages' in resume_data:
            story.append(Paragraph('LANGUAGES', heading_style))
            languages = resume_data['languages']
            if isinstance(languages, dict):
                for lang, level in languages.items():
                    story.append(Paragraph(f"{lang} - {level}", body_style))
            else:
                story.append(Paragraph(str(languages), body_style))
        
        # Build document
        doc.build(story)
        
        return filename
