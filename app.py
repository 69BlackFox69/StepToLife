import os
import sys
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from agents.initial_agent import InitialAgent
from agents.language_agent import LanguageAgent
from agents.resume_agent import ResumeAgent
from agents.job_agent import JobAgent
from agents.housing_agent import HousingAgent
from agents.documents_agent import DocumentsAgent
from agents.benefits_agent import BenefitsAgent
from agents.emergency_agent import EmergencyAgent
from agents.career_agent import CareerAgent
from services import ResourceResolver, infer_city_from_message
from config import config
import json
from datetime import datetime
import traceback

load_dotenv()

# Защита от UnicodeEncodeError в Windows-консолях (cp1252/cp866).
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Инициализация Flask приложения
app = Flask(__name__)

# Конфигурация
config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Глобальная обработка ошибок
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'message': 'Неверный запрос'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Страница не найдена'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500

# Инициализация агентов (с обработкой ошибок)
try:
    initial_agent = InitialAgent()
    language_agent = LanguageAgent()
    resume_agent = ResumeAgent()
    job_agent = JobAgent()
    housing_agent = HousingAgent()
    documents_agent = DocumentsAgent()
    benefits_agent = BenefitsAgent()
    emergency_agent = EmergencyAgent()
    career_agent = CareerAgent()
    print("[INFO] Все агенты успешно инициализированы")
except Exception as e:
    print(f"[ERROR] Ошибка при инициализации агентов: {e}")
    raise

# Хранилище пользовательских сессий
user_sessions = {}
resource_resolver = ResourceResolver()


def get_or_create_user_state(user_id):
    """Инициализировать состояние пользователя"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'history': [],
            'user_info': {},
            'knows_slovak': None,
            'intake': {},
            'onboarding': {
                'state_check': {}
            }
        }
    return user_sessions[user_id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat/initial', methods=['POST'])
def chat_initial():
    """Первый агент - определение начальных целей"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Пустой запрос'}), 400
        
        user_id = data.get('user_id', 'default')
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'message': 'Сообщение не может быть пустым'}), 400
        
        if user_id not in user_sessions:
            user_sessions[user_id] = {
                'history': [],
                'user_info': {},
                'knows_slovak': None,
                'intake': {}
            }
        
        # Добавляем сообщение пользователя в историю
        user_sessions[user_id]['history'].append({
            'role': 'user',
            'content': message
        })
        
        # Получаем ответ от агента
        response = initial_agent.process(message, user_sessions[user_id]['history'])
        
        # Сохраняем ответ в историю
        user_sessions[user_id]['history'].append({
            'role': 'assistant',
            'content': response['message']
        })
        
        # Обновляем информацию о пользователе
        if 'user_info' in response:
            user_sessions[user_id]['user_info'].update(response['user_info'])
            user_sessions[user_id]['intake'].update(response['user_info'])
        
        # Проверяем, знает ли пользователь словацкий
        if 'knows_slovak' in response:
            user_sessions[user_id]['knows_slovak'] = response['knows_slovak']
        
        return jsonify(response)
    
    except Exception as e:
        print(f"[ERROR] Ошибка в chat_initial: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500

@app.route('/api/chat/language', methods=['POST'])
def chat_language():
    """Второй агент - обучение словацкому языку"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Пустой запрос'}), 400
        
        user_id = data.get('user_id', 'default')
        message = data.get('message', '')
        lesson_level = data.get('lesson_level', 'beginner')
        
        if not message:
            return jsonify({'success': False, 'message': 'Сообщение не может быть пустым'}), 400
        
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        
        # Инициализируем язык сессию если её ещё нет
        if 'language_history' not in user_sessions[user_id]:
            user_sessions[user_id]['language_history'] = []
            user_sessions[user_id]['lesson_level'] = 'beginner'
        
        user_sessions[user_id]['language_history'].append({
            'role': 'user',
            'content': message
        })
        
        response = language_agent.process(message, user_sessions[user_id]['language_history'], lesson_level)
        
        user_sessions[user_id]['language_history'].append({
            'role': 'assistant',
            'content': response['message']
        })
        
        return jsonify(response)
    
    except Exception as e:
        print(f"[ERROR] Ошибка в chat_language: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500

@app.route('/api/chat/resume', methods=['POST'])
def chat_resume():
    """Третий агент - создание резюме"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Пустой запрос'}), 400
        
        user_id = data.get('user_id', 'default')
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'message': 'Сообщение не может быть пустым'}), 400
        
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        
        # Инициализируем резюме сессию если её ещё нет
        if 'resume_history' not in user_sessions[user_id]:
            user_sessions[user_id]['resume_history'] = []
            user_sessions[user_id]['resume_data'] = {}
        
        user_sessions[user_id]['resume_history'].append({
            'role': 'user',
            'content': message
        })
        
        response = resume_agent.process(message, user_sessions[user_id]['resume_history'])
        
        user_sessions[user_id]['resume_history'].append({
            'role': 'assistant',
            'content': response['message']
        })
        
        if 'resume_data' in response:
            user_sessions[user_id]['resume_data'].update(response['resume_data'])
        
        return jsonify(response)
    
    except Exception as e:
        print(f"[ERROR] Ошибка в chat_resume: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500

@app.route('/api/generate-pdf/<user_id>', methods=['GET'])
def generate_pdf(user_id):
    """Генерация PDF резюме"""
    try:
        if user_id not in user_sessions or not user_sessions[user_id].get('resume_data'):
            return jsonify({'error': 'Резюме не найдено'}), 404
        
        pdf_path = resume_agent.generate_pdf(user_sessions[user_id]['resume_data'], user_id)
        return send_file(pdf_path, as_attachment=True, download_name=f'resume_{user_id}.pdf')
    
    except Exception as e:
        print(f"[ERROR] Ошибка в generate_pdf: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка при создании PDF: {str(e)}'}), 500

@app.route('/api/chat/jobs', methods=['POST'])
def chat_jobs():
    """Четвёртый агент - поиск работ"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Пустой запрос'}), 400
        
        user_id = data.get('user_id', 'default')
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'message': 'Сообщение не может быть пустым'}), 400
        
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        
        # Инициализируем джобс сессию если её ещё нет
        if 'jobs_history' not in user_sessions[user_id]:
            user_sessions[user_id]['jobs_history'] = []
            user_sessions[user_id]['resume_data'] = user_sessions[user_id].get('resume_data', {})
        
        user_sessions[user_id]['jobs_history'].append({
            'role': 'user',
            'content': message
        })
        
        # Передаём данные резюме в агент
        resume_data = user_sessions[user_id].get('resume_data', {})
        response = job_agent.process(message, user_sessions[user_id]['jobs_history'], resume_data)
        
        user_sessions[user_id]['jobs_history'].append({
            'role': 'assistant',
            'content': response['message']
        })
        
        return jsonify(response)
    
    except Exception as e:
        print(f"[ERROR] Ошибка в chat_jobs: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500


@app.route('/api/chat/career', methods=['POST'])
def chat_career():
    """Интервью по работе -> персональный план -> подтверждение -> резюме"""
    try:
        data = request.json or {}
        user_id = data.get('user_id', 'default')
        user_message = data.get('message', '')
        is_init = bool(data.get('is_init', False))

        user = get_or_create_user_state(user_id)
        if 'career_session' not in user:
            user['career_session'] = {
                'phase': 'interview',
                'question_index': 0,
                'answers': [],
                'characteristics': {
                    'language': 'unknown',
                    'documents': 'unknown',
                    'residence': 'unknown',
                    'work_permit': 'unknown',
                    'discomforts': [],
                },
                'history': []
            }

        session = user['career_session']

        if is_init:
            session['phase'] = 'interview'
            session['question_index'] = 0
            session['answers'] = []
            session['characteristics'] = {
                'language': 'unknown',
                'documents': 'unknown',
                'residence': 'unknown',
                'work_permit': 'unknown',
                'discomforts': [],
            }
            session['history'] = []
        elif not user_message:
            return jsonify({'success': False, 'message': 'Сообщение не может быть пустым'}), 400

        if is_init:
            session['history'].append({'role': 'assistant', 'content': '[START_CAREER_CHAT]'})
            response = career_agent.process(
                user_message='',
                conversation_history=session['history'],
                session_state=session,
                is_init=True,
            )
        else:
            session['history'].append({'role': 'user', 'content': user_message})

            # Страховка: на первом вопросе про язык при ответе "нет"
            # принудительно переводим в фазу language_offer.
            normalized = ' '.join((user_message or '').lower().replace('!', ' ').replace('.', ' ').replace(',', ' ').replace('?', ' ').replace(':', ' ').replace(';', ' ').replace('"', ' ').replace("'", ' ').replace('`', ' ').split())
            first_question_no = (
                session.get('phase') == 'interview'
                and int(session.get('question_index', 0)) == 1
                and (
                    normalized in {'нет', 'не', 'n', 'н', 'no', 'net', 'неа'}
                    or normalized.startswith('нет')
                    or normalized.startswith('не ')
                    or normalized.startswith('no')
                    or normalized.startswith('net')
                )
            )

            if first_question_no:
                session['answers'].append({'field': 'language', 'value': user_message})
                session['characteristics']['language'] = 'no'
                response = {
                    'success': True,
                    'message': 'Understood. Before we continue, do you want to take a short Slovak learning course?',
                    'phase': 'language_offer',
                    'question_index': 1,
                    'answers': session['answers'],
                    'characteristics': session['characteristics'],
                }
            else:
                response = career_agent.process(
                    user_message=user_message,
                    conversation_history=session['history'],
                    session_state=session,
                    is_init=False,
                )

        if response.get('success'):
            session['phase'] = response.get('phase', session['phase'])
            session['question_index'] = response.get('question_index', session['question_index'])
            session['answers'] = response.get('answers', session['answers'])
            session['characteristics'] = response.get('characteristics', session['characteristics'])
            session['history'].append({'role': 'assistant', 'content': response.get('message', '')})

        return jsonify(response)
    except Exception as e:
        print(f"[ERROR] Ошибка в chat_career: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500


@app.route('/api/chat/housing', methods=['POST'])
def chat_housing():
    """Специализированный агент - жилье"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Пустой запрос'}), 400

        user_id = data.get('user_id', 'default')
        message = data.get('message', '')

        if not message:
            return jsonify({'success': False, 'message': 'Сообщение не может быть пустым'}), 400

        if user_id not in user_sessions:
            user_sessions[user_id] = {}

        if 'housing_history' not in user_sessions[user_id]:
            user_sessions[user_id]['housing_history'] = []

        user_sessions[user_id]['housing_history'].append({'role': 'user', 'content': message})
        response = housing_agent.process(message, user_sessions[user_id]['housing_history'])
        user_sessions[user_id]['housing_history'].append({'role': 'assistant', 'content': response['message']})

        if 'resource_source' in response:
            user_sessions[user_id]['last_resource_source'] = response['resource_source']
            print(f"[INFO] housing source={response['resource_source']} user={user_id}")

        return jsonify(response)
    except Exception as e:
        print(f"[ERROR] Ошибка в chat_housing: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500


@app.route('/api/chat/documents', methods=['POST'])
def chat_documents():
    """Специализированный агент - документы и легализация"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Пустой запрос'}), 400

        user_id = data.get('user_id', 'default')
        message = data.get('message', '')

        if not message:
            return jsonify({'success': False, 'message': 'Сообщение не может быть пустым'}), 400

        if user_id not in user_sessions:
            user_sessions[user_id] = {}

        if 'documents_history' not in user_sessions[user_id]:
            user_sessions[user_id]['documents_history'] = []

        user_sessions[user_id]['documents_history'].append({'role': 'user', 'content': message})
        response = documents_agent.process(message, user_sessions[user_id]['documents_history'])
        user_sessions[user_id]['documents_history'].append({'role': 'assistant', 'content': response['message']})

        if 'resource_source' in response:
            user_sessions[user_id]['last_resource_source'] = response['resource_source']
            print(f"[INFO] documents source={response['resource_source']} user={user_id}")

        return jsonify(response)
    except Exception as e:
        print(f"[ERROR] Ошибка в chat_documents: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500


@app.route('/api/chat/benefits', methods=['POST'])
def chat_benefits():
    """Специализированный агент - соцподдержка и выплаты"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Пустой запрос'}), 400

        user_id = data.get('user_id', 'default')
        message = data.get('message', '')

        if not message:
            return jsonify({'success': False, 'message': 'Сообщение не может быть пустым'}), 400

        if user_id not in user_sessions:
            user_sessions[user_id] = {}

        if 'benefits_history' not in user_sessions[user_id]:
            user_sessions[user_id]['benefits_history'] = []

        user_sessions[user_id]['benefits_history'].append({'role': 'user', 'content': message})
        response = benefits_agent.process(message, user_sessions[user_id]['benefits_history'])
        user_sessions[user_id]['benefits_history'].append({'role': 'assistant', 'content': response['message']})

        if 'resource_source' in response:
            user_sessions[user_id]['last_resource_source'] = response['resource_source']
            print(f"[INFO] benefits source={response['resource_source']} user={user_id}")

        return jsonify(response)
    except Exception as e:
        print(f"[ERROR] Ошибка в chat_benefits: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500


@app.route('/api/chat/emergency', methods=['POST'])
def chat_emergency():
    """Специализированный агент - экстренная поддержка"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Пустой запрос'}), 400

        user_id = data.get('user_id', 'default')
        message = data.get('message', '')

        if not message:
            return jsonify({'success': False, 'message': 'Сообщение не может быть пустым'}), 400

        if user_id not in user_sessions:
            user_sessions[user_id] = {}

        if 'emergency_history' not in user_sessions[user_id]:
            user_sessions[user_id]['emergency_history'] = []

        user_sessions[user_id]['emergency_history'].append({'role': 'user', 'content': message})
        response = emergency_agent.process(message, user_sessions[user_id]['emergency_history'])
        user_sessions[user_id]['emergency_history'].append({'role': 'assistant', 'content': response['message']})

        if 'resource_source' in response:
            user_sessions[user_id]['last_resource_source'] = response['resource_source']
            print(f"[INFO] emergency source={response['resource_source']} user={user_id}")

        return jsonify(response)
    except Exception as e:
        print(f"[ERROR] Ошибка в chat_emergency: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500

@app.route('/api/session/<user_id>', methods=['GET'])
def get_session(user_id):
    """Получить информацию о сессии пользователя"""
    try:
        if user_id not in user_sessions:
            return jsonify({'error': 'Сессия не найдена'}), 404
        
        return jsonify(user_sessions[user_id])
    
    except Exception as e:
        print(f"[ERROR] Ошибка в get_session: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500


@app.route('/api/resources/search', methods=['GET'])
def search_resources():
    """Поиск проверенных ресурсов из локальной демо-базы (strict source)"""
    try:
        city = request.args.get('city', 'Kosice')
        category = request.args.get('category', '')
        message_hint = request.args.get('message', '')

        if message_hint:
            city = infer_city_from_message(message_hint, default_city=city)

        categories = [category] if category else []
        services = resource_resolver.find_services(categories=categories, city=city, limit=10)

        return jsonify({
            'success': True,
            'source': 'verified_db',
            'city': city,
            'count': len(services),
            'services': services,
        })

    except Exception as e:
        print(f"[ERROR] Ошибка в search_resources: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500

@app.route('/api/onboarding/state-check', methods=['POST'])
def onboarding_state_check():
    """Сохранить состояние пользователя"""
    try:
        data = request.json or {}
        user_id = data.get('user_id', 'default')
        
        state_check = {
            'mood': data.get('mood', ''),
            'communication_difficulty': data.get('communication_difficulty', ''),
            'simple_mode': data.get('simple_mode', False),
            'theme_choice': data.get('theme_choice', 'light'),
            'font_size': data.get('font_size', 'medium')
        }
        
        user = get_or_create_user_state(user_id)
        user['onboarding']['state_check'] = state_check
        
        return jsonify({
            'success': True,
            'state_check': state_check
        })
    except Exception as e:
        print(f"[ERROR] Ошибка в onboarding_state_check: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500


@app.route('/api/onboarding/status/<user_id>', methods=['GET'])
def onboarding_status(user_id):
    """Получить статус онбординга"""
    try:
        user = get_or_create_user_state(user_id)
        return jsonify({
            'success': True,
            'onboarding': user['onboarding'],
            'completed': user['onboarding'].get('completed', False)
        })
    except Exception as e:
        print(f"[ERROR] Ошибка в onboarding_status: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500


if __name__ == '__main__':
    print("[INFO] Запуск Flask приложения StepToLife")
    print(f"[INFO] Режим: {app.config.get('DEBUG')}")
    print("[INFO] Откройте браузер: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
