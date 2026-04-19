import re
from agents.base_agent import BaseAgent


class CareerAgent(BaseAgent):
    """Agent that runs a short interview, creates a plan, and confirms start"""

    def __init__(self):
        system_prompt = """You are the StepToLife AI career assistant.

    Your goals:
    - after a short interview, create a personalized job-search plan;
    - reply briefly, clearly, and practically;
    - after plan confirmation, say that the user can move to resume creation.

    When the interview is finished, create the plan in English with 3-5 steps based on user answers.
    The plan should be concrete, supportive, and free of bureaucracy.
    """
        super().__init__(system_prompt)

    def get_questions(self):
        return [
            {
                'field': 'language',
                'question': 'First question: do you speak Slovak?'
            },
            {
                'field': 'documents',
                'question': 'Do you have your documents?'
            },
            {
                'field': 'residence',
                'question': 'Do you currently have a place to live?'
            },
            {
                'field': 'work_permit',
                'question': 'Do you have a work permit?'
            },
            {
                'field': 'concentration',
                'question': 'Concentration: is it hard for you to focus for a long time, or do short pieces of information work better?'
            },
            {
                'field': 'environment',
                'question': 'Environment: are new places difficult, is predictability important for you, or are crowded places uncomfortable?'
            },
            {
                'field': 'communication',
                'question': 'Communication: is it hard to start a conversation, are you afraid to say something wrong, or do prepared phrases help?'
            },
            {
                'field': 'stress',
                'question': 'Stress: in stressful situations do you freeze, need more time for decisions, or stop and struggle to continue?'
            },
        ]

    def _normalize(self, text):
        return ' '.join((text or '').lower().replace('!', ' ').replace('.', ' ').replace(',', ' ').replace('?', ' ').replace(':', ' ').replace(';', ' ').replace('"', ' ').replace("'", ' ').replace('`', ' ').split())

    def _is_yes(self, text):
        normalized = self._normalize(text)
        yes_tokens = [
            'да', 'есть', 'знаю', 'имею', 'конечно', 'ok', 'okay', 'ок', 'yes', 'yep',
            'yeah', 'yup', 'sure', 'of course', 'i do', 'have', 'can',
            'da', 'дa', 'ð´ð°'
        ]
        if normalized in {'y', 'д', 'ага', 'угу', 'ye', 'ys'}:
            return True
        if normalized.startswith('да') or normalized.startswith('ok') or normalized.startswith('ye'):
            return True
        return any(word in normalized for word in yes_tokens)

    def _is_no(self, text):
        normalized = self._normalize(text)
        no_tokens = [
            'нет', 'не имею', 'не знаю', 'no', 'nope', 'нету', 'неа', 'net', 'ð½ðµñ‚',
            'i do not', "don't", 'not really', 'none', 'nope'
        ]
        if normalized in {'n', 'н', 'не'}:
            return True
        if normalized.startswith('нет') or normalized.startswith('не ') or normalized.startswith('no') or normalized.startswith('net'):
            return True
        return any(word in normalized for word in no_tokens)

    def _parse_discomforts(self, text):
        normalized = (text or '').lower()
        if any(token in normalized for token in ['нет', 'нет проблем', 'никаких', 'ничего']):
            return []

        discomforts = []
        mapping = {
            'concentration-long': ['долго концентр', 'концентрир', 'тяжело концентр', 'сконцентриров'],
            'concentration-short': ['коротк', 'кратк', 'короткая информация', 'информация короткая', 'short info', 'short information', 'brief'],
            'environment-new-places': ['новых местах', 'новые места', 'незнаком'],
            'environment-predictability': ['что будет дальше', 'понимать, что будет', 'предсказуем', 'predictable', 'predictability', 'what comes next'],
            'environment-crowds': ['людных', 'много людей', 'толп', 'crowd'],
            'communication-start': ['начать разговор', 'сложно начать', 'как начать', 'start conversation', 'start talking'],
            'communication-fear': ['боюсь', 'неправильно', 'ошиб', 'страшно сказать', 'afraid', 'wrong', 'mistake'],
            'communication-phrases': ['готовые фразы', 'фразы', 'шаблоны фраз', 'prepared phrases', 'ready phrases'],
            'stress-lose': ['теряюсь', 'стресс', 'панику', 'теряюсь', 'freeze', 'panic', 'stressed'],
            'stress-time': ['больше времени', 'нужно время', 'медленно', 'more time', 'slow decision'],
            'stress-stop': ['остановиться', 'не продолжить', 'не смогу продолжить', 'stop', 'cannot continue'],
        }

        for key, keywords in mapping.items():
            if any(keyword in normalized for keyword in keywords):
                discomforts.append(key)
        return discomforts

    def _build_plan_prompt(self, characteristics):
        return (
            "Create a personalized job-search plan in English. "
            "Use 3-5 short steps. "
            "Use this user profile: "
            f"language={characteristics.get('language', 'unknown')}; "
            f"documents={characteristics.get('documents', 'unknown')}; "
            f"residence={characteristics.get('residence', 'unknown')}; "
            f"work_permit={characteristics.get('work_permit', 'unknown')}; "
            f"discomforts={characteristics.get('discomforts', [])}. "
            "At the end, ask whether this plan works for the user."
        )

    def _generate_plan(self, characteristics):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._build_plan_prompt(characteristics)},
        ]
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1200,
        )
        return completion.choices[0].message.content

    def process(self, user_message, conversation_history=None, session_state=None, is_init=False):
        session_state = session_state or {}
        questions = self.get_questions()
        phase = session_state.get('phase', 'interview')
        question_index = int(session_state.get('question_index', 0))
        answers = session_state.get('answers', []) or []
        characteristics = session_state.get('characteristics', {
            'language': 'unknown',
            'documents': 'unknown',
            'residence': 'unknown',
            'work_permit': 'unknown',
            'discomforts': [],
        })

        if is_init:
            first_question = questions[0]['question']
            return {
                'success': True,
                'message': f"Let's quickly clarify your situation. {first_question}",
                'phase': 'interview',
                'question_index': 1,
                'answers': [],
                'characteristics': characteristics,
            }

        if phase == 'language_offer':
            normalized = self._normalize(user_message)
            if self._is_yes(normalized):
                return {
                    'success': True,
                    'message': 'Great choice. Moving you to a short language course.',
                    'phase': 'redirect_language',
                    'question_index': question_index,
                    'answers': answers,
                    'characteristics': characteristics,
                }

            if self._is_no(normalized):
                next_question = questions[1]['question']
                return {
                    'success': True,
                    'message': f'Okay, continuing the interview. {next_question}',
                    'phase': 'interview',
                    'question_index': 2,
                    'answers': answers,
                    'characteristics': characteristics,
                }

            return {
                'success': True,
                'message': 'Please answer yes or no: do you want to take a short Slovak course now?',
                'phase': 'language_offer',
                'question_index': question_index,
                'answers': answers,
                'characteristics': characteristics,
            }

        if phase == 'interview':
            current_index = max(question_index - 1, 0)
            current_field = questions[current_index]['field']
            answer_text = (user_message or '').strip()

            if current_field in {'language', 'documents', 'residence', 'work_permit'}:
                characteristics[current_field] = 'yes' if self._is_yes(answer_text) else 'no' if self._is_no(answer_text) else 'unknown'
            elif current_field == 'concentration':
                if 'корот' in answer_text.lower() or 'кратк' in answer_text.lower() or 'short' in answer_text.lower() or 'brief' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['concentration-short']))
                if 'долго' in answer_text.lower() or 'концентр' in answer_text.lower() or 'long' in answer_text.lower() or 'focus' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['concentration-long']))
            elif current_field == 'environment':
                if 'нов' in answer_text.lower() or 'незнаком' in answer_text.lower() or 'new place' in answer_text.lower() or 'unfamiliar' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['environment-new-places']))
                if 'дальше' in answer_text.lower() or 'понимать' in answer_text.lower() or 'предсказуем' in answer_text.lower() or 'predict' in answer_text.lower() or 'what next' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['environment-predictability']))
                if 'людн' in answer_text.lower() or 'много людей' in answer_text.lower() or 'толп' in answer_text.lower() or 'crowd' in answer_text.lower() or 'many people' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['environment-crowds']))
            elif current_field == 'communication':
                if 'начать' in answer_text.lower() or 'разговор' in answer_text.lower() or 'start' in answer_text.lower() or 'conversation' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['communication-start']))
                if 'боюсь' in answer_text.lower() or 'неправиль' in answer_text.lower() or 'ошиб' in answer_text.lower() or 'afraid' in answer_text.lower() or 'wrong' in answer_text.lower() or 'mistake' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['communication-fear']))
                if 'фраз' in answer_text.lower() or 'готов' in answer_text.lower() or 'phrase' in answer_text.lower() or 'template' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['communication-phrases']))
            elif current_field == 'stress':
                if 'теря' in answer_text.lower() or 'стресс' in answer_text.lower() or 'панику' in answer_text.lower() or 'freeze' in answer_text.lower() or 'panic' in answer_text.lower() or 'stress' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['stress-lose']))
                if 'время' in answer_text.lower() or 'медлен' in answer_text.lower() or 'time' in answer_text.lower() or 'slow' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['stress-time']))
                if 'останов' in answer_text.lower() or 'не продолж' in answer_text.lower() or 'stop' in answer_text.lower() or 'continue' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['stress-stop']))

            answers.append({
                'field': current_field,
                'value': answer_text,
            })

            if current_field == 'language' and characteristics.get('language') == 'no':
                return {
                    'success': True,
                    'message': 'Understood. Before we continue, do you want to take a short Slovak learning course?',
                    'phase': 'language_offer',
                    'question_index': question_index,
                    'answers': answers,
                    'characteristics': characteristics,
                }

            if question_index < len(questions):
                next_question = questions[question_index]['question']
                return {
                    'success': True,
                    'message': next_question,
                    'phase': 'interview',
                    'question_index': question_index + 1,
                    'answers': answers,
                    'characteristics': characteristics,
                }

            plan_text = self._generate_plan(characteristics)
            return {
                'success': True,
                'message': plan_text,
                'phase': 'plan',
                'question_index': question_index,
                'answers': answers,
                'characteristics': characteristics,
            }

        if phase == 'plan':
            normalized = self._normalize(user_message)
            confirm_phrases = {'да', 'подходит', 'нравится', 'согласен', 'согласна', 'ok', 'ок', 'поехали', 'начинаем', 'yes', 'works', 'looks good', 'approve', 'approved', 'let us start', "let's start"}
            if normalized in confirm_phrases or any(phrase in normalized for phrase in ['да, план', 'план нравится', 'подходит', 'все ок', 'plan works', 'looks good', 'sounds good', 'yes, plan']):
                return {
                    'success': True,
                    'message': 'Great, the plan is confirmed. Now I will move you to resume creation.',
                    'phase': 'approved',
                    'question_index': question_index,
                    'answers': answers,
                    'characteristics': characteristics,
                }

            if 'проще' in normalized or 'короче' in normalized or 'simpler' in normalized or 'shorter' in normalized:
                simple_prompt = (
                    "Make this plan shorter and simpler. "
                    f"Profile: language={characteristics.get('language', 'unknown')}; "
                    f"documents={characteristics.get('documents', 'unknown')}; "
                    f"residence={characteristics.get('residence', 'unknown')}; "
                    f"work_permit={characteristics.get('work_permit', 'unknown')}; "
                    f"discomforts={characteristics.get('discomforts', [])}."
                )
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": simple_prompt},
                ]
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.6,
                    max_tokens=900,
                )
                message = completion.choices[0].message.content
                return {
                    'success': True,
                    'message': message,
                    'phase': 'plan',
                    'question_index': question_index,
                    'answers': answers,
                    'characteristics': characteristics,
                }

            return {
                'success': True,
                'message': 'If the plan works, write: yes, I approve the plan. If you want, I can make it shorter.',
                'phase': 'plan',
                'question_index': question_index,
                'answers': answers,
                'characteristics': characteristics,
            }

        return {
            'success': False,
            'message': 'Unknown chat state',
            'phase': phase,
            'question_index': question_index,
            'answers': answers,
            'characteristics': characteristics,
        }
