import re
from agents.base_agent import BaseAgent


class InitialAgent(BaseAgent):
    """First agent: intake, routing, and specialized-agent orchestration"""

    def __init__(self):
        system_prompt = """You are the first coordination agent of StepToLife.

Your task:
- quickly understand the user's situation,
- identify the primary problem type,
- route to the right specialized agent,
- provide an adaptive step-by-step plan.

Problem domains:
1) employment
2) housing
3) documents/legalization
4) benefits/social support
5) emergency

Communication rules:
- use a soft, non-judgmental tone,
- ask only necessary clarifying questions,
- avoid long overloaded responses,
- if the situation is risky, prioritize safety.

Intake fields:
- has_documents
- has_stable_address
- language_level
- urgency

Language: English."""
        super().__init__(system_prompt)

    def process(self, user_message, conversation_history):
        """Process message and build adaptive route"""

        response = super().process(user_message, conversation_history)

        if not response['success']:
            return response

        message = response['message']
        user_info = self._extract_user_info(user_message)

        # Backward compatibility with legacy flag
        knows_slovak = self._detect_knows_slovak(user_message, user_info)
        if knows_slovak is not None:
            user_info['knows_slovak'] = knows_slovak

        result = {
            'success': True,
            'message': message,
            'user_info': user_info,
        }

        if knows_slovak is not None:
            result['knows_slovak'] = knows_slovak

        should_create_plan = self._should_create_plan(conversation_history, user_info)

        if should_create_plan:
            plan = self._generate_action_plan(user_info)
            result['action_plan'] = plan
            result['plan_generated'] = True
            result['orchestration'] = {
                'primary_problem': user_info.get('problem_type', 'employment'),
                'recommended_agent': plan.get('primary_agent', {}),
                'intake': {
                    'has_documents': user_info.get('has_documents', 'unknown'),
                    'has_stable_address': user_info.get('has_stable_address', 'unknown'),
                    'language_level': user_info.get('language_level', 'unknown'),
                    'urgency': user_info.get('urgency', 'unknown'),
                }
            }

        return result

    def _extract_user_info(self, user_message):
        """Extract intake data and problem type"""
        text = (user_message or '').lower()
        user_info = {}

        problem_keywords = {
            'emergency': [
                'urgent', 'emergency', 'danger', 'violence', 'threat',
                'no food', 'hungry', 'street', 'afraid', 'suicide', 'self-harm',
                'срочно', 'экстренно', 'опасно', 'насилие', 'угроза', 'голод', 'на улице', 'боюсь'
            ],
            'housing': [
                'housing', 'apartment', 'rent', 'shelter', 'homeless', 'no place to stay',
                'жиль', 'квартир', 'общежит', 'ночлег', 'приют'
            ],
            'documents': [
                'documents', 'passport', 'visa', 'permit', 'residence', 'legalization',
                'документ', 'паспорт', 'виза', 'внж', 'легализац'
            ],
            'benefits': [
                'benefit', 'allowance', 'social support', 'financial help', 'subsidy',
                'пособи', 'выплат', 'соц', 'помощ', 'субсид'
            ],
            'employment': [
                'job', 'work', 'vacancy', 'interview', 'resume', 'employment',
                'работ', 'ваканс', 'трудоустро', 'собесед', 'резюме'
            ],
        }

        for problem_type, keywords in problem_keywords.items():
            if any(word in text for word in keywords):
                user_info['problem_type'] = problem_type
                break

        # Intake: documents
        if any(w in text for w in ['no documents', 'without documents', 'lost passport', 'undocumented', 'нет документов', 'без документов', 'потерял паспорт']):
            user_info['has_documents'] = 'no'
        elif any(w in text for w in ['have documents', 'all documents', 'documents are fine', 'есть документы', 'документы в порядке']):
            user_info['has_documents'] = 'yes'

        # Intake: stable address
        if any(w in text for w in ['no housing', 'no address', 'living on the street', 'without housing', 'no place to stay', 'нет жилья', 'нет адреса', 'живу на улице', 'без жилья']):
            user_info['has_stable_address'] = 'no'
        elif any(w in text for w in ['have housing', 'have address', 'stable address', 'rent apartment', 'есть жилье', 'есть адрес', 'стабильный адрес', 'снимаю квартиру']):
            user_info['has_stable_address'] = 'yes'

        # Intake: language level
        if any(w in text for w in ['do not know slovak', 'poor slovak', "don't know slovak", 'не знаю словацкий', 'плохо знаю словацкий', 'совсем не знаю']):
            user_info['language_level'] = 'none'
        elif any(w in text for w in ['basic slovak', 'know a little slovak', 'базовый словацкий', 'немного знаю словацкий']):
            user_info['language_level'] = 'basic'
        elif any(w in text for w in ['speak slovak well', 'fluent slovak', 'говорю по-словацки', 'хорошо знаю словацкий', 'свободно']):
            user_info['language_level'] = 'intermediate'

        # Intake: urgency
        if any(w in text for w in ['urgent', 'right now', 'emergency', 'danger', 'violence', 'срочно', 'прямо сейчас', 'экстренно', 'опасно', 'насилие']):
            user_info['urgency'] = 'high'
        elif any(w in text for w in ['soon', 'next days', 'critical', 'very needed', 'скоро', 'в ближайшие дни', 'критично', 'очень нужно']):
            user_info['urgency'] = 'medium'
        else:
            user_info['urgency'] = 'low'

        # Legacy field for compatibility
        if user_info.get('problem_type') == 'employment':
            user_info['goal'] = 'employment'

        return user_info

    def _detect_knows_slovak(self, user_message, user_info):
        text = (user_message or '').lower()
        if user_info.get('language_level') in ['none', 'basic']:
            return False
        if user_info.get('language_level') == 'intermediate':
            return True

        if any(word in text for word in ['yes, i know', 'i know slovak', 'i speak slovak', 'yes', 'да, знаю', 'знаю словацкий', 'говорю по-словацки']):
            return True
        if any(word in text for word in ["no, i don't", "i don't know", 'poor slovak', "i don't speak", 'no', 'нет, не знаю', 'не знаю', 'плохо знаю', 'не говорю']):
            return False
        return None

    def _should_create_plan(self, conversation_history, user_info):
        """Create plan quickly in emergency and after short intake in other cases"""
        if user_info.get('problem_type') == 'emergency':
            return True

        enough_messages = len(conversation_history) >= 4
        has_problem = bool(user_info.get('problem_type'))

        intake_known_count = 0
        for key in ['has_documents', 'has_stable_address', 'language_level', 'urgency']:
            if key in user_info:
                intake_known_count += 1

        return has_problem and (enough_messages or intake_known_count >= 2)

    def _action_card(self, do_now, where, what_to_say, bring_with_you, if_refused):
        return {
            'do_now': do_now,
            'where': where,
            'what_to_say': what_to_say,
            'bring_with_you': bring_with_you,
            'if_refused': if_refused,
        }

    def _generate_action_plan(self, user_info):
        problem = user_info.get('problem_type', 'employment')
        urgency = user_info.get('urgency', 'low')
        has_documents = user_info.get('has_documents', 'unknown')
        has_address = user_info.get('has_stable_address', 'unknown')
        language_level = user_info.get('language_level', 'unknown')

        agent_map = {
            'employment': {
                'agent_name': 'JobAgent',
                'agent_role': 'Job consultant',
                'agent_api': '/api/chat/jobs'
            },
            'housing': {
                'agent_name': 'HousingAgent',
                'agent_role': 'Housing consultant',
                'agent_api': '/api/chat/housing'
            },
            'documents': {
                'agent_name': 'DocumentsAgent',
                'agent_role': 'Documents consultant',
                'agent_api': '/api/chat/documents'
            },
            'benefits': {
                'agent_name': 'BenefitsAgent',
                'agent_role': 'Benefits consultant',
                'agent_api': '/api/chat/benefits'
            },
            'emergency': {
                'agent_name': 'EmergencyAgent',
                'agent_role': 'Emergency support agent',
                'agent_api': '/api/chat/emergency'
            },
        }

        primary_agent = agent_map.get(problem, agent_map['employment'])

        if problem == 'emergency' or urgency == 'high':
            steps = [
                {
                    'tab': 'Emergency',
                    'number': 1,
                    'title': 'Stabilize safety right now',
                    'description': 'Take one safe action in the next 5 minutes.',
                    'agent_name': 'EmergencyAgent',
                    'agent_role': 'Emergency support agent',
                    'agent_api': '/api/chat/emergency',
                    'action_card': self._action_card(
                        do_now='Move to a safe place or call 112 if there is direct threat.',
                        where='Nearest safe location: police station, hospital, social center.',
                        what_to_say='I need urgent help. I am in danger and need a safe place.',
                        bring_with_you='Phone, any document, required medication.',
                        if_refused='Ask to speak with a senior staff member and call 112 again.'
                    )
                },
                {
                    'tab': 'Documents',
                    'number': 2,
                    'title': 'Prepare minimum information for support',
                    'description': 'You can start support procedures even without a full document pack.',
                    'agent_name': 'DocumentsAgent',
                    'agent_role': 'Documents consultant',
                    'agent_api': '/api/chat/documents',
                    'action_card': self._action_card(
                        do_now='Gather name, date of birth, citizenship, and any available document.',
                        where='Municipal service office or migration office.',
                        what_to_say='I need first-response help and guidance on temporary legalization.',
                        bring_with_you='Any paper, document photo, witness/relative contact.',
                        if_refused='Request written refusal and contact NGO or free legal aid.'
                    )
                },
            ]
            estimated_time = '1-24 hours (emergency mode)'
        elif problem == 'housing':
            steps = [
                {
                    'tab': 'Housing',
                    'number': 1,
                    'title': 'Find temporary safe accommodation',
                    'description': 'Start with a temporary solution to stabilize your situation.',
                    'agent_name': 'HousingAgent',
                    'agent_role': 'Housing consultant',
                    'agent_api': '/api/chat/housing',
                    'action_card': self._action_card(
                        do_now='Contact the nearest shelter/crisis center and ask about availability today.',
                        where='Shelter, crisis center, municipal social office.',
                        what_to_say='I need temporary safe housing for the next few days.',
                        bring_with_you='Document (if any), phone, basic personal items.',
                        if_refused='Ask for an alternative address/contact and request NGO partner support.'
                    )
                },
                {
                    'tab': 'Documents',
                    'number': 2,
                    'title': 'Prepare documents for long-term housing',
                    'description': 'Check what documents are needed for renting or support programs.',
                    'agent_name': 'DocumentsAgent',
                    'agent_role': 'Documents consultant',
                    'agent_api': '/api/chat/documents',
                    'action_card': self._action_card(
                        do_now='Create a list of available and missing documents.',
                        where='Migration office, municipality, or free legal consultation.',
                        what_to_say='I need a document list for legal stay and renting.',
                        bring_with_you='Passport/ID, registration, proof of income (if available).',
                        if_refused='Request a written checklist and contact NGO support.'
                    )
                }
            ]
            estimated_time = '1-7 days to stabilize housing'
        elif problem == 'documents':
            steps = [
                {
                    'tab': 'Documents',
                    'number': 1,
                    'title': 'Identify your priority document pack',
                    'description': 'First gather the minimum set that allows the process to start.',
                    'agent_name': 'DocumentsAgent',
                    'agent_role': 'Documents consultant',
                    'agent_api': '/api/chat/documents',
                    'action_card': self._action_card(
                        do_now='Photograph/write down all available documents.',
                        where='At home or with an NGO consultant.',
                        what_to_say='Help me identify which documents are needed first.',
                        bring_with_you='All available documents and copies.',
                        if_refused='Ask for written reasons and a missing-items list.'
                    )
                },
                {
                    'tab': 'Benefits',
                    'number': 2,
                    'title': 'Start available support in parallel',
                    'description': 'While documents are in progress, connect basic support programs.',
                    'agent_name': 'BenefitsAgent',
                    'agent_role': 'Benefits consultant',
                    'agent_api': '/api/chat/benefits',
                    'action_card': self._action_card(
                        do_now='Ask which temporary support options are available without full documents.',
                        where='Social service office or NGO.',
                        what_to_say='What urgent support can I receive while my documents are being processed?',
                        bring_with_you='Identity/status proof if available.',
                        if_refused='Ask for alternative programs or partner referrals.'
                    )
                }
            ]
            estimated_time = '3-14 days for initial processing'
        elif problem == 'benefits':
            steps = [
                {
                    'tab': 'Benefits',
                    'number': 1,
                    'title': 'Check available benefits and support',
                    'description': 'Focus on realistic programs for your exact situation.',
                    'agent_name': 'BenefitsAgent',
                    'agent_role': 'Benefits consultant',
                    'agent_api': '/api/chat/benefits',
                    'action_card': self._action_card(
                        do_now='Prepare a short profile: income, household, current expenses.',
                        where='Social office, assistance center, or free consultation.',
                        what_to_say='I want to check which benefits and support I may qualify for.',
                        bring_with_you='ID, family documents, income proof (if available).',
                        if_refused='Ask for refusal grounds and alternative programs.'
                    )
                },
                {
                    'tab': 'Documents',
                    'number': 2,
                    'title': 'Close missing documents for application',
                    'description': 'Prepare missing papers to avoid losing the application timeline.',
                    'agent_name': 'DocumentsAgent',
                    'agent_role': 'Documents consultant',
                    'agent_api': '/api/chat/documents',
                    'action_card': self._action_card(
                        do_now='Review application checklist and mark missing items.',
                        where='Application office or NGO.',
                        what_to_say='I need the exact document list to complete my application.',
                        bring_with_you='Draft application and copies of available documents.',
                        if_refused='Ask them to accept a partial pack and schedule completion date.'
                    )
                }
            ]
            estimated_time = '2-10 days to submit application'
        else:
            steps = [
                {
                    'tab': 'Slovak language' if language_level in ['none', 'basic'] else 'Resume',
                    'number': 1,
                    'title': 'Prepare the employment foundation',
                    'description': 'If language is weak, start with micro-lessons; otherwise move to resume.',
                    'agent_name': 'LanguageAgent' if language_level in ['none', 'basic'] else 'ResumeAgent',
                    'agent_role': 'Slovak language teacher' if language_level in ['none', 'basic'] else 'Resume consultant',
                    'agent_api': '/api/chat/language' if language_level in ['none', 'basic'] else '/api/chat/resume',
                    'action_card': self._action_card(
                        do_now='Pick one immediate goal: language (20 min) or resume draft (10 lines).',
                        where='Relevant StepToLife tab.',
                        what_to_say='I want quick step-by-step preparation for employment.',
                        bring_with_you='Skills list, experience, and language level.',
                        if_refused='Ask for a simplified 2-3 step path.'
                    )
                },
                {
                    'tab': 'Jobs',
                    'number': 2,
                    'title': 'Start targeted job search',
                    'description': 'Search for roles that fit your current profile and constraints.',
                    'agent_name': 'JobAgent',
                    'agent_role': 'Job consultant',
                    'agent_api': '/api/chat/jobs',
                    'action_card': self._action_card(
                        do_now='Select 2 roles and 1 city/region to start searching.',
                        where='Jobs tab in StepToLife.',
                        what_to_say='Find 3 realistic vacancies for me and a one-week application plan.',
                        bring_with_you='Resume draft, schedule preferences, and location preferences.',
                        if_refused='Narrow filters and ask for alternative entry-level positions.'
                    )
                }
            ]
            estimated_time = '3-14 days to first applications'

        plan = {
            'title': 'Adaptive Action Plan',
            'intro': 'This plan is built for your situation: problem type + available resources + urgency.',
            'primary_agent': primary_agent,
            'steps': steps,
            'estimated_time': estimated_time,
            'intake_snapshot': {
                'problem_type': problem,
                'urgency': urgency,
                'has_documents': has_documents,
                'has_stable_address': has_address,
                'language_level': language_level,
            }
        }

        if urgency == 'high':
            plan['special_advice'] = 'High urgency: start with emergency support and one safe action right now.'
        elif has_documents == 'no':
            plan['special_advice'] = 'No documents: work on immediate safety and initial legalization in parallel with DocumentsAgent.'
        elif has_address == 'no':
            plan['special_advice'] = 'No stable address: first secure temporary accommodation, then move to long-term options.'

        return plan
