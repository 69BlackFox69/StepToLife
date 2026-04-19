import re
from agents.base_agent import BaseAgent


class CareerAgent(BaseAgent):
    """Агент, который проводит короткое интервью, формирует план и подтверждает старт"""

    def __init__(self):
        system_prompt = """Ты - AI-агент StepToLife для поиска работы.

Твоя цель:
- после короткого интервью составить персональный план поиска работы;
- отвечать коротко, ясно и по делу;
- после подтверждения плана сказать, что можно переходить к созданию резюме.

Когда интервью завершено, составь план на русском языке, 3-5 шагов, с учетом ответов пользователя.
План должен быть конкретным, поддерживающим и без канцелярита.
"""
        super().__init__(system_prompt)

    def get_questions(self):
        return [
            {
                'field': 'language',
                'question': 'Первый вопрос: вы знаете словацкий язык?'
            },
            {
                'field': 'documents',
                'question': 'У вас есть документы?'
            },
            {
                'field': 'residence',
                'question': 'У вас есть место проживания?'
            },
            {
                'field': 'work_permit',
                'question': 'У вас есть разрешение на работу?'
            },
            {
                'field': 'concentration',
                'question': 'Блок про концентрацию: вам сложно долго концентрироваться или вам удобнее, когда информация короткая?'
            },
            {
                'field': 'environment',
                'question': 'Блок про окружающую среду: вам сложно в новых местах, важно понимать, что будет дальше, или некомфортно в людных местах?'
            },
            {
                'field': 'communication',
                'question': 'Блок про общение: вам сложно начать разговор, вы боитесь сказать что-то неправильно или вам помогают готовые фразы?'
            },
            {
                'field': 'stress',
                'question': 'Блок про стресс: в стрессовой ситуации вы теряетесь, вам нужно больше времени на решения или вы можете остановиться и не продолжить?'
            },
        ]

    def _normalize(self, text):
        return ' '.join((text or '').lower().replace('!', ' ').replace('.', ' ').replace(',', ' ').replace('?', ' ').replace(':', ' ').replace(';', ' ').replace('"', ' ').replace("'", ' ').replace('`', ' ').split())

    def _is_yes(self, text):
        normalized = self._normalize(text)
        yes_tokens = [
            'да', 'есть', 'знаю', 'имею', 'конечно', 'ok', 'okay', 'ок', 'yes', 'yep',
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
            'нет', 'не имею', 'не знаю', 'no', 'nope', 'нету', 'неа', 'net', 'ð½ðµñ‚'
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
            'concentration-short': ['коротк', 'кратк', 'короткая информация', 'информация короткая'],
            'environment-new-places': ['новых местах', 'новые места', 'незнаком'],
            'environment-predictability': ['что будет дальше', 'понимать, что будет', 'предсказуем'],
            'environment-crowds': ['людных', 'много людей', 'толп', 'crowd'],
            'communication-start': ['начать разговор', 'сложно начать', 'как начать'],
            'communication-fear': ['боюсь', 'неправильно', 'ошиб', 'страшно сказать'],
            'communication-phrases': ['готовые фразы', 'фразы', 'шаблоны фраз'],
            'stress-lose': ['теряюсь', 'стресс', 'панику', 'теряюсь'],
            'stress-time': ['больше времени', 'нужно время', 'медленно'],
            'stress-stop': ['остановиться', 'не продолжить', 'не смогу продолжить'],
        }

        for key, keywords in mapping.items():
            if any(keyword in normalized for keyword in keywords):
                discomforts.append(key)
        return discomforts

    def _build_plan_prompt(self, characteristics):
        return (
            "Составь персональный план поиска работы на русском языке. "
            "Нужно 3-5 коротких шагов. "
            "Учитывай профиль пользователя: "
            f"language={characteristics.get('language', 'unknown')}; "
            f"documents={characteristics.get('documents', 'unknown')}; "
            f"residence={characteristics.get('residence', 'unknown')}; "
            f"work_permit={characteristics.get('work_permit', 'unknown')}; "
            f"discomforts={characteristics.get('discomforts', [])}. "
            "В конце спроси, подходит ли такой план."
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
                'message': f'Давайте коротко уточним вашу ситуацию. {first_question}',
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
                    'message': 'Отличный выбор. Перевожу вас на короткий языковой курс.',
                    'phase': 'redirect_language',
                    'question_index': question_index,
                    'answers': answers,
                    'characteristics': characteristics,
                }

            if self._is_no(normalized):
                next_question = questions[1]['question']
                return {
                    'success': True,
                    'message': f'Хорошо, продолжаем интервью. {next_question}',
                    'phase': 'interview',
                    'question_index': 2,
                    'answers': answers,
                    'characteristics': characteristics,
                }

            return {
                'success': True,
                'message': 'Напишите, пожалуйста, да или нет: хотите пройти короткий курс словацкого сейчас?',
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
                if 'корот' in answer_text.lower() or 'кратк' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['concentration-short']))
                if 'долго' in answer_text.lower() or 'концентр' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['concentration-long']))
            elif current_field == 'environment':
                if 'нов' in answer_text.lower() or 'незнаком' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['environment-new-places']))
                if 'дальше' in answer_text.lower() or 'понимать' in answer_text.lower() or 'предсказуем' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['environment-predictability']))
                if 'людн' in answer_text.lower() or 'много людей' in answer_text.lower() or 'толп' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['environment-crowds']))
            elif current_field == 'communication':
                if 'начать' in answer_text.lower() or 'разговор' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['communication-start']))
                if 'боюсь' in answer_text.lower() or 'неправиль' in answer_text.lower() or 'ошиб' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['communication-fear']))
                if 'фраз' in answer_text.lower() or 'готов' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['communication-phrases']))
            elif current_field == 'stress':
                if 'теря' in answer_text.lower() or 'стресс' in answer_text.lower() or 'панику' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['stress-lose']))
                if 'время' in answer_text.lower() or 'медлен' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['stress-time']))
                if 'останов' in answer_text.lower() or 'не продолж' in answer_text.lower():
                    characteristics['discomforts'] = list(dict.fromkeys(characteristics.get('discomforts', []) + ['stress-stop']))

            answers.append({
                'field': current_field,
                'value': answer_text,
            })

            if current_field == 'language' and characteristics.get('language') == 'no':
                return {
                    'success': True,
                    'message': 'Понял. Хотите перед продолжением пройти короткий обучающий курс словацкого?',
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
            confirm_phrases = {'да', 'подходит', 'нравится', 'согласен', 'согласна', 'ok', 'ок', 'поехали', 'начинаем'}
            if normalized in confirm_phrases or any(phrase in normalized for phrase in ['да, план', 'план нравится', 'подходит', 'все ок']):
                return {
                    'success': True,
                    'message': 'Отлично, план подтвержден. Сейчас переведу вас к созданию резюме.',
                    'phase': 'approved',
                    'question_index': question_index,
                    'answers': answers,
                    'characteristics': characteristics,
                }

            if 'проще' in normalized or 'короче' in normalized:
                simple_prompt = (
                    "Сделай этот план еще короче и проще. "
                    f"Профиль: language={characteristics.get('language', 'unknown')}; "
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
                'message': 'Если план подходит, напишите: да, план нравится. Если хотите, я могу сделать его короче.',
                'phase': 'plan',
                'question_index': question_index,
                'answers': answers,
                'characteristics': characteristics,
            }

        return {
            'success': False,
            'message': 'Неизвестное состояние чата',
            'phase': phase,
            'question_index': question_index,
            'answers': answers,
            'characteristics': characteristics,
        }
