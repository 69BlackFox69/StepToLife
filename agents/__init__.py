# Пакет для AI агентов
from agents.initial_agent import InitialAgent
from agents.language_agent import LanguageAgent
from agents.resume_agent import ResumeAgent
from agents.job_agent import JobAgent
from agents.housing_agent import HousingAgent
from agents.documents_agent import DocumentsAgent
from agents.benefits_agent import BenefitsAgent
from agents.emergency_agent import EmergencyAgent

__all__ = [
	'InitialAgent',
	'LanguageAgent',
	'ResumeAgent',
	'JobAgent',
	'HousingAgent',
	'DocumentsAgent',
	'BenefitsAgent',
	'EmergencyAgent',
]
