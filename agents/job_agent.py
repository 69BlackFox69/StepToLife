import json
from agents.base_agent import BaseAgent

class JobAgent(BaseAgent):
    """Fourth agent: search and suggest suitable jobs in Slovakia"""
    
    def __init__(self):
        system_prompt = """You are an experienced employment consultant in Slovakia on the StepToLife platform.

    Your goal: help the user find suitable jobs and prepare for employment.

    Approach:
    1. Analyze the user's resume when available
    2. Understand qualification and experience level
    3. Suggest 2-4 suitable vacancies or search directions
    4. Explain why these positions fit this person
    5. Give practical advice on:
       - Interview preparation
       - Standing out among other candidates
       - Salary negotiation
       - Adapting skills to the Slovak market

    Slovak market context:
    - Common sectors: IT, healthcare, tourism, manufacturing, services
    - Typical requirements: Slovak language, relevant experience, soft skills
    - Salary ranges vary by level and role

    Important: many users belong to vulnerable groups.
    - Migrants/refugees: consider language barriers, documents, cultural differences
    - Long-term unemployed: highlight strengths and explain employment gaps constructively
    - People with disabilities: suggest accessible roles and inclusive employers
    - People with criminal records: support realistic second-chance pathways

    Style:
    - Practical and supportive
    - Specific and not overcomplicated
    - Show that progress is possible despite barriers
    - Listen to personal constraints and goals

    Language: English."""
        super().__init__(system_prompt)
    
    def process(self, user_message, conversation_history, resume_data=None):
        """Process message and suggest jobs"""
        
        # Build context with resume information
        context_message = user_message
        
        if resume_data:
            resume_summary = self._create_resume_summary(resume_data)
            context_message = f"[User resume information:\n{resume_summary}]\n\nMessage: {user_message}"
        
        response = super().process(context_message, conversation_history)
        
        if not response['success']:
            return response
        
        message = response['message']
        
        # Try to extract suggested roles
        job_suggestions = self._extract_job_suggestions(message)
        
        result = {
            'success': True,
            'message': message
        }
        
        if job_suggestions:
            result['job_suggestions'] = job_suggestions
        
        return result
    
    def _create_resume_summary(self, resume_data):
        """Create short resume summary for model context"""
        summary = []
        
        if 'name' in resume_data:
            summary.append(f"Name: {resume_data['name']}")
        
        if 'skills' in resume_data:
            skills = resume_data['skills']
            if isinstance(skills, list):
                summary.append(f"Skills: {', '.join(skills)}")
        
        if 'experience' in resume_data:
            summary.append("Work experience:")
            experiences = resume_data['experience']
            if isinstance(experiences, list):
                for exp in experiences:
                    summary.append(f"  - {exp.get('position', '')}: {exp.get('duration', '')}")
        
        if 'languages' in resume_data:
            summary.append("Languages:")
            languages = resume_data['languages']
            if isinstance(languages, dict):
                for lang, level in languages.items():
                    summary.append(f"  - {lang}: {level}")
        
        return '\n'.join(summary)
    
    def _extract_job_suggestions(self, message):
        """Try to extract suggested vacancies"""
        # Simplified extractor; production version should use structured output.
        
        job_suggestions = []
        
        # Look for common role mentions in both Russian and English.
        job_keywords = {
            'разработчик': 'Developer',
            'developer': 'Developer',
            'медсестра': 'Nurse',
            'nurse': 'Nurse',
            'учитель': 'Teacher',
            'teacher': 'Teacher',
            'менеджер': 'Manager',
            'manager': 'Manager',
            'консультант': 'Consultant',
            'consultant': 'Consultant',
            'аналитик': 'Analyst',
            'analyst': 'Analyst',
            'инженер': 'Engineer',
            'engineer': 'Engineer'
        }
        
        for keyword, job_title in job_keywords.items():
            if keyword in message.lower():
                job_suggestions.append(job_title)
        
        return list(set(job_suggestions))
