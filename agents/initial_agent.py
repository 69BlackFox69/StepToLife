import re
from agents.base_agent import BaseAgent


class InitialAgent(BaseAgent):
    """Первый агент - intake, маршрутизация и оркестрация проблемных агентов"""

    def __init__(self):
        system_prompt = """Ты - первый координационный агент StepToLife.

Твоя задача:
- коротко понять ситуацию пользователя,
- определить основной тип проблемы,
- направить к правильному специализированному агенту,
- дать адаптивный пошаговый план.

Проблемные направления:
1) employment - трудоустройство
2) housing - жилье
3) documents - документы/легализация
4) benefits - соцподдержка и выплаты
5) emergency - экстренный случай

Правила общения:
- используй мягкий, неосуждающий тон,
- задавай только нужные уточняющие вопросы,
- не перегружай длинными ответами,
- если ситуация рискованная, приоритет - безопасность.

Помни про intake-поля:
- has_documents
- has_stable_address
- language_level
- urgency

Язык: русский."""
        super().__init__(system_prompt)

    def process(self, user_message, conversation_history):
        """Обработать сообщение и построить адаптивный маршрут"""

        response = super().process(user_message, conversation_history)

        if not response['success']:
            return response

        message = response['message']
        user_info = self._extract_user_info(user_message)

        # Сохраняем совместимость со старым флагом
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
        """Извлечь intake-данные и тип проблемы"""
        text = user_message.lower()
        user_info = {}

        problem_keywords = {
            'emergency': [
                'срочно', 'экстренно', 'опасно', 'насилие', 'угроза',
                'голод', 'нет еды', 'на улице', 'боюсь', 'emergency', 'danger'
            ],
            'housing': [
                'жиль', 'квартир', 'общежит', 'ночлег', 'приют', 'shelter', 'homeless'
            ],
            'documents': [
                'документ', 'паспорт', 'виза', 'внж', 'легализац', 'permit', 'residence'
            ],
            'benefits': [
                'пособи', 'выплат', 'соц', 'помощ', 'субсид', 'benefit', 'allowance'
            ],
            'employment': [
                'работ', 'ваканс', 'трудоустро', 'собесед', 'резюме', 'job', 'work'
            ],
        }

        for problem_type, keywords in problem_keywords.items():
            if any(word in text for word in keywords):
                user_info['problem_type'] = problem_type
                break

        # Intake: документы
        if any(w in text for w in ['нет документов', 'без документов', 'потерял паспорт', 'undocumented']):
            user_info['has_documents'] = 'no'
        elif any(w in text for w in ['есть документы', 'все документы', 'документы в порядке']):
            user_info['has_documents'] = 'yes'

        # Intake: стабильный адрес
        if any(w in text for w in ['нет жилья', 'нет адреса', 'живу на улице', 'без жилья', 'no address']):
            user_info['has_stable_address'] = 'no'
        elif any(w in text for w in ['есть жилье', 'есть адрес', 'стабильный адрес', 'снимаю квартиру']):
            user_info['has_stable_address'] = 'yes'

        # Intake: уровень языка
        if any(w in text for w in ['не знаю словацкий', 'плохо знаю словацкий', 'совсем не знаю']):
            user_info['language_level'] = 'none'
        elif any(w in text for w in ['базовый словацкий', 'немного знаю словацкий']):
            user_info['language_level'] = 'basic'
        elif any(w in text for w in ['хорошо знаю словацкий', 'говорю по-словацки', 'свободно']):
            user_info['language_level'] = 'intermediate'

        # Intake: срочность
        if any(w in text for w in ['срочно', 'прямо сейчас', 'экстренно', 'опасно', 'насилие']):
            user_info['urgency'] = 'high'
        elif any(w in text for w in ['скоро', 'в ближайшие дни', 'критично', 'очень нужно']):
            user_info['urgency'] = 'medium'
        else:
            user_info['urgency'] = 'low'

        # Старое поле для совместимости
        if user_info.get('problem_type') == 'employment':
            user_info['goal'] = 'employment'

        return user_info

    def _detect_knows_slovak(self, user_message, user_info):
        text = user_message.lower()
        if user_info.get('language_level') in ['none', 'basic']:
            return False
        if user_info.get('language_level') == 'intermediate':
            return True

        if any(word in text for word in ['да, знаю', 'знаю словацкий', 'говорю по-словацки', 'yes']):
            return True
        if any(word in text for word in ['нет, не знаю', 'не знаю', 'плохо знаю', 'не говорю', 'no']):
            return False
        return None

    def _should_create_plan(self, conversation_history, user_info):
        """План создаем быстро в emergency и после короткого intake в остальных"""
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
                'agent_role': '🔍 Консультант по трудоустройству',
                'agent_api': '/api/chat/jobs'
            },
            'housing': {
                'agent_name': 'HousingAgent',
                'agent_role': '🏠 Консультант по жилью',
                'agent_api': '/api/chat/housing'
            },
            'documents': {
                'agent_name': 'DocumentsAgent',
                'agent_role': '🪪 Консультант по документам',
                'agent_api': '/api/chat/documents'
            },
            'benefits': {
                'agent_name': 'BenefitsAgent',
                'agent_role': '💶 Консультант по соцподдержке',
                'agent_api': '/api/chat/benefits'
            },
            'emergency': {
                'agent_name': 'EmergencyAgent',
                'agent_role': '🚨 Агент экстренной помощи',
                'agent_api': '/api/chat/emergency'
            },
        }

        primary_agent = agent_map.get(problem, agent_map['employment'])

        if problem == 'emergency' or urgency == 'high':
            steps = [
                {
                    'tab': 'Экстренная помощь',
                    'number': 1,
                    'title': 'Стабилизируйте безопасность прямо сейчас',
                    'description': 'Сделайте одно безопасное действие в ближайшие 5 минут.',
                    'agent_name': 'EmergencyAgent',
                    'agent_role': '🚨 Агент экстренной помощи',
                    'agent_api': '/api/chat/emergency',
                    'action_card': self._action_card(
                        do_now='Перейдите в безопасное место или позвоните 112, если есть прямая угроза.',
                        where='Ближайшее безопасное место: полицейский участок, больница, социальный центр.',
                        what_to_say='Мне нужна срочная помощь. Я сейчас в опасности и мне нужно безопасное место.',
                        bring_with_you='Телефон, любой документ, необходимые лекарства.',
                        if_refused='Попросите соединить со старшим сотрудником и позвоните 112 повторно.'
                    )
                },
                {
                    'tab': 'Документы',
                    'number': 2,
                    'title': 'Подготовьте минимальные данные для обращения',
                    'description': 'Даже при отсутствии полного пакета документов можно начать оформление помощи.',
                    'agent_name': 'DocumentsAgent',
                    'agent_role': '🪪 Консультант по документам',
                    'agent_api': '/api/chat/documents',
                    'action_card': self._action_card(
                        do_now='Соберите имя, дату рождения, гражданство и любой имеющийся документ.',
                        where='Муниципальная служба или миграционный офис.',
                        what_to_say='Мне нужна первичная помощь и консультация по временной легализации.',
                        bring_with_you='Любая справка, фото документа, контакты свидетеля/родственника.',
                        if_refused='Попросите письменный отказ и обратитесь через НКО или бесплатную юрпомощь.'
                    )
                },
            ]
            estimated_time = '1-24 часа (экстренный режим)'
        elif problem == 'housing':
            steps = [
                {
                    'tab': 'Жилье',
                    'number': 1,
                    'title': 'Найдите временное безопасное размещение',
                    'description': 'Начните с временного решения, чтобы стабилизировать ситуацию.',
                    'agent_name': 'HousingAgent',
                    'agent_role': '🏠 Консультант по жилью',
                    'agent_api': '/api/chat/housing',
                    'action_card': self._action_card(
                        do_now='Свяжитесь с ближайшим shelter/кризисным центром и уточните место на сегодня.',
                        where='Shelter, кризисный центр, муниципальный соцотдел.',
                        what_to_say='Мне нужно временное безопасное жилье на ближайшие дни.',
                        bring_with_you='Документ (если есть), телефон, базовые вещи.',
                        if_refused='Запросите альтернативный адрес/контакт и обратитесь в НКО-партнер.'
                    )
                },
                {
                    'tab': 'Документы',
                    'number': 2,
                    'title': 'Подготовьте документы для долгосрочного размещения',
                    'description': 'Проверьте, какие документы нужны для аренды или поддержки.',
                    'agent_name': 'DocumentsAgent',
                    'agent_role': '🪪 Консультант по документам',
                    'agent_api': '/api/chat/documents',
                    'action_card': self._action_card(
                        do_now='Составьте список доступных документов и недостающих позиций.',
                        where='Миграционный офис/муниципалитет/бесплатная юрконсультация.',
                        what_to_say='Нужен список документов для легального проживания и аренды.',
                        bring_with_you='Паспорт/ID, регистрация, подтверждение дохода (если есть).',
                        if_refused='Попросите чек-лист письменно и обратитесь в НКО для сопровождения.'
                    )
                }
            ]
            estimated_time = '1-7 дней на стабилизацию жилья'
        elif problem == 'documents':
            steps = [
                {
                    'tab': 'Документы',
                    'number': 1,
                    'title': 'Определите приоритетный пакет документов',
                    'description': 'Сначала соберите минимум, который позволяет запустить процесс.',
                    'agent_name': 'DocumentsAgent',
                    'agent_role': '🪪 Консультант по документам',
                    'agent_api': '/api/chat/documents',
                    'action_card': self._action_card(
                        do_now='Сфотографируйте/перепишите все доступные документы.',
                        where='Дома или в офисе НКО с консультантом.',
                        what_to_say='Помогите определить, какие документы нужны в первую очередь.',
                        bring_with_you='Все имеющиеся документы и их копии.',
                        if_refused='Попросите письменную причину и список, чего не хватает.'
                    )
                },
                {
                    'tab': 'Соцподдержка',
                    'number': 2,
                    'title': 'Параллельно запустите доступную поддержку',
                    'description': 'Пока идут документы, важно подключить базовые выплаты/помощь.',
                    'agent_name': 'BenefitsAgent',
                    'agent_role': '💶 Консультант по соцподдержке',
                    'agent_api': '/api/chat/benefits',
                    'action_card': self._action_card(
                        do_now='Уточните временные виды помощи, доступные без полного пакета документов.',
                        where='Соцслужба или НКО.',
                        what_to_say='Какая срочная помощь доступна мне на этапе оформления документов?',
                        bring_with_you='Подтверждение личности/статуса (если есть).',
                        if_refused='Попросите альтернативные программы или направления в партнерские организации.'
                    )
                }
            ]
            estimated_time = '3-14 дней на первичное оформление'
        elif problem == 'benefits':
            steps = [
                {
                    'tab': 'Соцподдержка',
                    'number': 1,
                    'title': 'Проверьте доступные выплаты и льготы',
                    'description': 'Сфокусируйтесь на реальных программах под вашу ситуацию.',
                    'agent_name': 'BenefitsAgent',
                    'agent_role': '💶 Консультант по соцподдержке',
                    'agent_api': '/api/chat/benefits',
                    'action_card': self._action_card(
                        do_now='Составьте короткий профиль дохода, состава семьи и текущих расходов.',
                        where='Соцслужба/центр помощи/бесплатная консультация.',
                        what_to_say='Хочу проверить, на какие выплаты и помощь я могу претендовать.',
                        bring_with_you='ID, документы семьи, подтверждение доходов (если есть).',
                        if_refused='Попросите основания отказа и список альтернативных программ.'
                    )
                },
                {
                    'tab': 'Документы',
                    'number': 2,
                    'title': 'Закройте недостающие документы для заявки',
                    'description': 'Подготовьте недостающие бумаги, чтобы не потерять срок подачи.',
                    'agent_name': 'DocumentsAgent',
                    'agent_role': '🪪 Консультант по документам',
                    'agent_api': '/api/chat/documents',
                    'action_card': self._action_card(
                        do_now='Сверьте чек-лист заявки и отметьте, чего не хватает.',
                        where='Офис подачи заявок/НКО.',
                        what_to_say='Мне нужен точный список документов для завершения заявки.',
                        bring_with_you='Черновик заявки, копии имеющихся документов.',
                        if_refused='Попросите принять частичный пакет и назначить дату донесения.'
                    )
                }
            ]
            estimated_time = '2-10 дней до подачи заявки'
        else:
            steps = [
                {
                    'tab': 'Словацкий язык' if language_level in ['none', 'basic'] else 'Резюме',
                    'number': 1,
                    'title': 'Подготовьте базу для трудоустройства',
                    'description': 'При слабом языке начните с мини-уроков, иначе переходите к резюме.',
                    'agent_name': 'LanguageAgent' if language_level in ['none', 'basic'] else 'ResumeAgent',
                    'agent_role': '🎓 Учитель словацкого языка' if language_level in ['none', 'basic'] else '👨‍💼 Консультант по резюме',
                    'agent_api': '/api/chat/language' if language_level in ['none', 'basic'] else '/api/chat/resume',
                    'action_card': self._action_card(
                        do_now='Определите 1 ближайшую цель: язык (20 минут) или черновик резюме (10 строк).',
                        where='Соответствующая вкладка StepToLife.',
                        what_to_say='Хочу быстро подготовиться к трудоустройству по шагам.',
                        bring_with_you='Список навыков, опыт, уровень языка.',
                        if_refused='Спросите упрощенный путь из 2-3 шагов.'
                    )
                },
                {
                    'tab': 'Работа',
                    'number': 2,
                    'title': 'Запустите целевой поиск работы',
                    'description': 'Ищите вакансии под ваш текущий профиль и ограничения.',
                    'agent_name': 'JobAgent',
                    'agent_role': '🔍 Консультант по трудоустройству',
                    'agent_api': '/api/chat/jobs',
                    'action_card': self._action_card(
                        do_now='Выберите 2 роли и 1 город/регион для старта поиска.',
                        where='Вкладка "Работа" в StepToLife.',
                        what_to_say='Подберите мне 3 реалистичные вакансии и план откликов на неделю.',
                        bring_with_you='Черновик резюме, предпочтения по графику и локации.',
                        if_refused='Сузьте фильтр и запросите альтернативные стартовые позиции.'
                    )
                }
            ]
            estimated_time = '3-14 дней до первых откликов'

        plan = {
            'title': '🧭 Адаптивный план действий',
            'intro': 'План построен под вашу ситуацию: тип проблемы + доступные ресурсы + срочность.',
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
            plan['special_advice'] = '✓ Высокая срочность: начните с экстренной помощи и одного безопасного шага прямо сейчас.'
        elif has_documents == 'no':
            plan['special_advice'] = '✓ Нет документов: параллельно решайте базовую безопасность и первичную легализацию через DocumentsAgent.'
        elif has_address == 'no':
            plan['special_advice'] = '✓ Нет стабильного адреса: сначала временное размещение, затем долгосрочное решение.'

        return plan
