// ===== ПЕРЕМЕННЫЕ СОСТОЯНИЯ =====
const userId = generateUserId();
let userState = {
    mood: null,
    communication: null,
    simpleMode: false,
    themeChoice: 'light',
    fontSize: 'medium',
    selectedProblem: null,
    characteristics: {},
    onboardingStep: 'mood',
    onboardingComplete: false
};

// ===== ИНИЦИАЛИЗАЦИЯ =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('[INIT] Приложение загружено, user_id:', userId);
    loadUserState();
});

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

function generateUserId() {
    return 'user_' + Math.random().toString(36).substr(2, 9);
}

function loadUserState() {
    // Загрузить состояние с сервера
    fetch(`/api/onboarding/status/${userId}`)
        .then(r => r.json())
        .then(data => {
            if (data.success && data.completed) {
                userState.onboardingComplete = true;
                if (data.onboarding && data.onboarding.state_check) {
                    const stateCheck = data.onboarding.state_check;
                    userState.mood = stateCheck.mood || null;
                    userState.communication = stateCheck.communication_difficulty || null;
                    userState.simpleMode = Boolean(stateCheck.simple_mode);
                    userState.themeChoice = stateCheck.theme_choice || 'light';
                    userState.fontSize = stateCheck.font_size || 'medium';
                    applyTheme(userState.mood, userState.communication, userState.simpleMode, userState.themeChoice, userState.fontSize);
                }
                console.log('[STATE] Онбординг завершен, переход к маршруту');
                goToJobsRoute();
            } else {
                console.log('[STATE] Онбординг не завершен, начинаем с чек-ина');
                showScreen('screen-state-check');
                startOnboardingChat();
            }
        })
        .catch(e => {
            console.log('[STATE] Не удалось загрузить состояние, начинаем с чек-ина', e);
            showScreen('screen-state-check');
            startOnboardingChat();
        });
}

function showScreen(screenId) {
    // Скрыть все экраны
    document.querySelectorAll('.screen').forEach(s => s.style.display = 'none');
    // Скрыть вкладки
    document.getElementById('tabs-container').style.display = 'none';
    // Показать нужный экран
    const screen = document.getElementById(screenId);
    if (screen) {
        screen.style.display = 'block';
        screen.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function applyTheme(mood, communicationDifficulty, simpleMode, themeChoice = 'light', fontSize = 'medium') {
    const container = document.querySelector('.container');
    
    // Очистить старые классы темы
    container.classList.remove('mood-calm', 'mood-anxious', 'mood-overwhelmed');
    container.classList.remove('communication-easy', 'communication-hard');
    container.classList.remove('simple-mode');
    container.classList.remove('theme-light', 'theme-warm', 'theme-contrast');
    container.classList.remove('font-small', 'font-medium', 'font-large');
    
    // Применить новые классы
    if (mood === 'calm') container.classList.add('mood-calm');
    else if (mood === 'anxious') container.classList.add('mood-anxious');
    else if (mood === 'overwhelmed') container.classList.add('mood-overwhelmed');
    
    if (communicationDifficulty === 'hard') container.classList.add('communication-hard');
    else container.classList.add('communication-easy');
    
    if (simpleMode) container.classList.add('simple-mode');

    if (themeChoice) container.classList.add(`theme-${themeChoice}`);
    if (fontSize) container.classList.add(`font-${fontSize}`);
    
    console.log('[THEME] Применена тема:', { mood, communicationDifficulty, simpleMode, themeChoice, fontSize });
}

function startOnboardingChat() {
    const chat = document.getElementById('onboarding-chat');
    const controls = document.getElementById('onboarding-controls');
    if (!chat || !controls) return;

    userState.onboardingStep = 'mood';
    controls.innerHTML = `
        <button class="reply-btn" onclick="answerOnboarding('mood', 'calm')">😌 Спокойно</button>
        <button class="reply-btn" onclick="answerOnboarding('mood', 'anxious')">😟 Беспокойно</button>
        <button class="reply-btn" onclick="answerOnboarding('mood', 'overwhelmed')">😫 Тяжело</button>
    `;
}

function appendOnboardingMessage(role, text, toneClass = '') {
    const chat = document.getElementById('onboarding-chat');
    if (!chat) return;

    const message = document.createElement('div');
    message.className = `message ${role} ${toneClass}`.trim();
    const paragraph = document.createElement('p');
    paragraph.textContent = text;
    message.appendChild(paragraph);
    chat.appendChild(message);
    chat.scrollTop = chat.scrollHeight;
}

function renderOnboardingControls(step) {
    const controls = document.getElementById('onboarding-controls');
    if (!controls) return;

    const compact = userState.mood === 'overwhelmed' || userState.simpleMode;
    const label = compact ? 'reply-btn compact' : 'reply-btn';

    if (step === 'simple_mode') {
        controls.innerHTML = `
            <button class="${label}" onclick="answerOnboarding('simpleMode', true)">Да, нужен</button>
            <button class="${label}" onclick="answerOnboarding('simpleMode', false)">Нет, обычный</button>
        `;
        return;
    }

    if (step === 'theme') {
        controls.innerHTML = `
            <button class="${label}" onclick="answerOnboarding('themeChoice', 'light')">Светлая</button>
            <button class="${label}" onclick="answerOnboarding('themeChoice', 'warm')">Теплая</button>
            <button class="${label}" onclick="answerOnboarding('themeChoice', 'contrast')">Контрастная</button>
        `;
        return;
    }

    if (step === 'font') {
        controls.innerHTML = `
            <button class="${label}" onclick="answerOnboarding('fontSize', 'small')">Маленький</button>
            <button class="${label}" onclick="answerOnboarding('fontSize', 'medium')">Средний</button>
            <button class="${label}" onclick="answerOnboarding('fontSize', 'large')">Крупный</button>
        `;
        return;
    }

    controls.innerHTML = '';
}

async function saveOnboardingState() {
    try {
        const response = await fetch('/api/onboarding/state-check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                mood: userState.mood,
                communication_difficulty: userState.communication,
                simple_mode: userState.simpleMode,
                theme_choice: userState.themeChoice,
                font_size: userState.fontSize
            })
        });

        return await response.json();
    } catch (error) {
        console.error('[ERROR] Не удалось сохранить onboarding state', error);
        return { success: false };
    }
}

async function answerOnboarding(step, value) {
    const controls = document.getElementById('onboarding-controls');
    if (controls) {
        controls.querySelectorAll('button').forEach(button => button.disabled = true);
    }

    if (step === 'mood') {
        userState.mood = value;
        appendOnboardingMessage('user', value === 'calm' ? 'Спокойно' : value === 'anxious' ? 'Беспокойно' : 'Тяжело');

        if (value === 'calm') {
            appendOnboardingMessage('assistant', 'Хорошо. Буду говорить обычно и по делу.', 'tone-calm');
        } else if (value === 'anxious') {
            appendOnboardingMessage('assistant', 'Понял. Буду говорить спокойно и поддерживающе.', 'tone-supportive');
        } else {
            appendOnboardingMessage('assistant', 'Понял. Буду отвечать коротко и просто.', 'tone-short');
        }

        userState.onboardingStep = 'simple_mode';
        renderOnboardingControls('simple_mode');
        appendOnboardingMessage('assistant', 'Нужен ли вам очень простой режим?', 'tone-current');
        await saveOnboardingState();
        return;
    }

    if (step === 'simpleMode') {
        userState.simpleMode = Boolean(value);
        appendOnboardingMessage('user', value ? 'Да, нужен' : 'Нет, обычный');

        if (value) {
            applyTheme(userState.mood, userState.communication, true, userState.themeChoice, userState.fontSize);
            appendOnboardingMessage('assistant', 'Включаю упрощенную тему сайта.', 'tone-supportive');
        } else {
            appendOnboardingMessage('assistant', 'Оставляю обычный вид.', 'tone-calm');
        }

        userState.onboardingStep = 'theme';
        renderOnboardingControls('theme');
        appendOnboardingMessage('assistant', 'Какую цветовую тему выберете?', 'tone-current');
        await saveOnboardingState();
        return;
    }

    if (step === 'themeChoice') {
        userState.themeChoice = value;
        appendOnboardingMessage('user', value === 'light' ? 'Светлая' : value === 'warm' ? 'Теплая' : 'Контрастная');
        applyTheme(userState.mood, userState.communication, userState.simpleMode, userState.themeChoice, userState.fontSize);

        userState.onboardingStep = 'font';
        renderOnboardingControls('font');
        appendOnboardingMessage('assistant', 'Какой размер шрифта текста на странице вам комфортнее?', 'tone-current');
        await saveOnboardingState();
        return;
    }

    if (step === 'fontSize') {
        userState.fontSize = value;
        appendOnboardingMessage('user', value === 'small' ? 'Маленький' : value === 'medium' ? 'Средний' : 'Крупный');
        applyTheme(userState.mood, userState.communication, userState.simpleMode, userState.themeChoice, userState.fontSize);

        appendOnboardingMessage('assistant', 'Спасибо. Я подстроился под вас. Теперь идём к выбору задачи.', 'tone-supportive');
        renderOnboardingControls('done');
        await saveOnboardingState();

        setTimeout(() => {
            showScreen('screen-problem-choice');
            document.getElementById('tabs-container').style.display = 'none';
        }, 700);
    }
}

// ===== ЭКРАН 1: ЧЕК-ИН СОСТОЯНИЯ =====

async function goToProblems() {
    startOnboardingChat();
    showScreen('screen-state-check');
}

// ===== ЭКРАН 2: ВЫБОР ПРОБЛЕМЫ =====

function selectProblem(problem) {
    userState.selectedProblem = problem;
    console.log('[PROBLEM] Выбранная проблема:', problem);
    
    // Обновить визуальное состояние кнопок
    document.querySelectorAll('.problem-btn').forEach(btn => btn.classList.remove('active'));
    event.target.closest('.problem-btn').classList.add('active');
}

function showDemoMessage(problem) {
    alert('🚧 Этот раздел - это демонстрация. Прямо сейчас работает только путь "Найти работу".\n\n' +
          'Остальные разделы будут доступны позже: документы, язык, жилье.');
}

// ===== ЭКРАН 3: ОСОБЕННОСТИ ПОЛЬЗОВАТЕЛЯ =====

async function goToCharacteristics() {
    if (!userState.selectedProblem) {
        alert('Пожалуйста, выберите проблему');
        return;
    }
    showScreen('screen-characteristics');
}

async function goToJobsRoute() {
    // Собрать особенности
    const characteristics = {
        language: document.querySelector('input[name="language"]:checked') ? 'yes' : 'no',
        documents: document.querySelector('input[name="documents"]:checked') ? 'yes' : 'no',
        residence: document.querySelector('input[name="residence"]:checked') ? 'yes' : 'no',
        work_permit: document.querySelector('input[name="work_permit"]:checked') ? 'yes' : 'no',
        discomforts: Array.from(document.querySelectorAll('input[name="discomfort"]:checked'))
            .map(el => el.value)
    };
    
    userState.characteristics = characteristics;
    
    // Отправить на сервер
    try {
        const response = await fetch('/api/onboarding/characteristics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                ...characteristics
            })
        });
        
        const data = await response.json();
        if (data.success) {
            console.log('[ONBOARDING] Особенности пользователя сохранены');
            userState.onboardingComplete = true;
            showScreen('screen-jobs-route');
        }
    } catch (e) {
        console.error('[ERROR]', e);
        alert('Ошибка при сохранении характеристик');
    }
}

// ===== ЭКРАН 4: МАРШРУТ РАБОТЫ =====

function openTab(tabName) {
    // Показать контейнер вкладок
    document.getElementById('tabs-container').style.display = 'block';
    document.getElementById('screen-jobs-route').style.display = 'none';
    
    // Скрыть все вкладки
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    
    // Показать нужную вкладку
    const tabContent = document.getElementById(tabName);
    const tabBtn = document.querySelector(`[data-tab="${tabName}"]`);
    
    if (tabContent) tabContent.classList.add('active');
    if (tabBtn) tabBtn.classList.add('active');
    
    // Прокрутить в начало
    window.scrollTo(0, 0);
}

function stepComplete(stepNum) {
    const statusEl = document.getElementById(`status-${stepNum}`);
    if (statusEl) {
        statusEl.innerHTML = '✅ Завершено';
        statusEl.style.color = '#28a745';
    }
    console.log(`[PROGRESS] Шаг ${stepNum} завершен`);
}

// ===== ФРАЗЫ И TTS =====

function speakPhrase(phrase) {
    const utterance = new SpeechSynthesisUtterance(phrase);
    utterance.lang = 'sk-SK';
    window.speechSynthesis.speak(utterance);
    console.log('[TTS] Озвучивание фразы:', phrase);
}

// ===== ЧАТЫ =====

async function sendResumeMessage() {
    const input = document.getElementById('resume-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessageToChat('resume-chat', message, 'user');
    input.value = '';
    
    showLoadingMessage('resume-chat');
    
    try {
        const response = await fetch('/api/chat/resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });
        
        const data = await response.json();
        removeLastMessage('resume-chat');
        
        if (data.success) {
            addMessageToChat('resume-chat', data.message, 'assistant');
        } else {
            addMessageToChat('resume-chat', 'Ошибка: ' + data.message, 'assistant');
        }
    } catch (e) {
        removeLastMessage('resume-chat');
        addMessageToChat('resume-chat', 'Ошибка сервера', 'assistant');
    }
}

async function sendLanguageMessage() {
    const input = document.getElementById('language-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessageToChat('language-chat', message, 'user');
    input.value = '';
    
    showLoadingMessage('language-chat');
    
    try {
        const response = await fetch('/api/chat/language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });
        
        const data = await response.json();
        removeLastMessage('language-chat');
        
        if (data.success) {
            addMessageToChat('language-chat', data.message, 'assistant');
        } else {
            addMessageToChat('language-chat', 'Ошибка: ' + data.message, 'assistant');
        }
    } catch (e) {
        removeLastMessage('language-chat');
        addMessageToChat('language-chat', 'Ошибка сервера', 'assistant');
    }
}

async function sendJobsMessage() {
    const input = document.getElementById('jobs-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessageToChat('jobs-chat', message, 'user');
    input.value = '';
    
    showLoadingMessage('jobs-chat');
    
    try {
        const response = await fetch('/api/chat/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });
        
        const data = await response.json();
        removeLastMessage('jobs-chat');
        
        if (data.success) {
            addMessageToChat('jobs-chat', data.message, 'assistant');
        } else {
            addMessageToChat('jobs-chat', 'Ошибка: ' + data.message, 'assistant');
        }
    } catch (e) {
        removeLastMessage('jobs-chat');
        addMessageToChat('jobs-chat', 'Ошибка сервера', 'assistant');
    }
}

async function sendInitialMessage() {
    const input = document.getElementById('initial-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessageToChat('initial-chat', message, 'user');
    input.value = '';
    
    showLoadingMessage('initial-chat');
    
    try {
        const response = await fetch('/api/chat/initial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });
        
        const data = await response.json();
        removeLastMessage('initial-chat');
        
        if (data.success) {
            addMessageToChat('initial-chat', data.message, 'assistant');
        } else {
            addMessageToChat('initial-chat', 'Ошибка: ' + data.message, 'assistant');
        }
    } catch (e) {
        removeLastMessage('initial-chat');
        addMessageToChat('initial-chat', 'Ошибка сервера', 'assistant');
    }
}

function generatePDF() {
    alert('PDF будет сгенерирован на основе информации, которую вы ввели.');
}

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ЧАТА =====

function addMessageToChat(chatId, message, role) {
    const chatEl = document.getElementById(chatId);
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `<p>${escapeHtml(message)}</p>`;
    chatEl.appendChild(messageDiv);
    chatEl.scrollTop = chatEl.scrollHeight;
}

function showLoadingMessage(chatId) {
    const chatEl = document.getElementById(chatId);
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant loading';
    loadingDiv.innerHTML = '<p>⏳ Загрузка...</p>';
    loadingDiv.id = 'loading-msg';
    chatEl.appendChild(loadingDiv);
    chatEl.scrollTop = chatEl.scrollHeight;
}

function removeLastMessage(chatId) {
    const chatEl = document.getElementById(chatId);
    const loadingMsg = chatEl.querySelector('#loading-msg');
    if (loadingMsg) loadingMsg.remove();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== ОБРАБОТЧИК ENTER =====

document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        const activeElement = document.activeElement;
        if (activeElement.id === 'resume-input') {
            e.preventDefault();
            sendResumeMessage();
        } else if (activeElement.id === 'jobs-input') {
            e.preventDefault();
            sendJobsMessage();
        } else if (activeElement.id === 'language-input') {
            e.preventDefault();
            sendLanguageMessage();
        } else if (activeElement.id === 'initial-input') {
            e.preventDefault();
            sendInitialMessage();
        }
    }
});
