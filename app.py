import os
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
from services import ResourceResolver, infer_city_from_message
from config import config
import json
from datetime import datetime
import traceback

load_dotenv()

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
    print("[INFO] Все агенты успешно инициализированы")
except Exception as e:
    print(f"[ERROR] Ошибка при инициализации агентов: {e}")
    raise

# Хранилище пользовательских сессий
user_sessions = {}
resource_resolver = ResourceResolver()

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

if __name__ == '__main__':
    print("[INFO] Запуск Flask приложения StepToLife")
    print(f"[INFO] Режим: {app.config.get('DEBUG')}")
    print("[INFO] Откройте браузер: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
