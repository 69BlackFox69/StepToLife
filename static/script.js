// ===== STATE =====
const userId = generateUserId();

let userState = {
    mood: null,
    communication: null,
    simpleMode: false,
    themeChoice: 'light',
    fontSize: 'medium',
    selectedProblem: null,
    onboardingStep: 'mood',
    onboardingComplete: false,
    careerPhase: 'interview',
    planApproved: false
};

// ===== INIT =====
document.addEventListener('DOMContentLoaded', function() {
    loadUserState();
});

function generateUserId() {
    return 'user_' + Math.random().toString(36).substr(2, 9);
}

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.style.display = 'none';
    });

    document.getElementById('tabs-container').style.display = 'none';

    const screen = document.getElementById(screenId);
    if (screen) {
        screen.style.display = 'block';
    }
}

function showCareerTabs(tabName = 'resume-step') {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.style.display = 'none';
    });
    document.getElementById('tabs-container').style.display = 'block';
    openTab(tabName);
}

function applyTheme(mood, communicationDifficulty, simpleMode, themeChoice = 'light', fontSize = 'medium') {
    const container = document.querySelector('.container');
    if (!container) return;

    container.classList.remove('mood-calm', 'mood-anxious', 'mood-overwhelmed');
    container.classList.remove('communication-easy', 'communication-hard');
    container.classList.remove('simple-mode');
    container.classList.remove('theme-light', 'theme-warm', 'theme-contrast');
    container.classList.remove('font-small', 'font-medium', 'font-large');

    if (mood === 'calm') container.classList.add('mood-calm');
    else if (mood === 'anxious') container.classList.add('mood-anxious');
    else if (mood === 'overwhelmed') container.classList.add('mood-overwhelmed');

    if (communicationDifficulty === 'hard') container.classList.add('communication-hard');
    else container.classList.add('communication-easy');

    if (simpleMode) container.classList.add('simple-mode');
    if (themeChoice) container.classList.add(`theme-${themeChoice}`);
    if (fontSize) container.classList.add(`font-${fontSize}`);
}

function loadUserState() {
    fetch(`/api/onboarding/status/${userId}`)
        .then(r => r.json())
        .then(data => {
            if (data.success && data.completed) {
                userState.onboardingComplete = true;
                if (data.onboarding && data.onboarding.state_check) {
                    const state = data.onboarding.state_check;
                    userState.mood = state.mood || null;
                    userState.communication = state.communication_difficulty || null;
                    userState.simpleMode = Boolean(state.simple_mode);
                    userState.themeChoice = state.theme_choice || 'light';
                    userState.fontSize = state.font_size || 'medium';
                    applyTheme(userState.mood, userState.communication, userState.simpleMode, userState.themeChoice, userState.fontSize);
                }
                showScreen('screen-problem-choice');
                return;
            }

            showScreen('screen-state-check');
            startOnboardingChat();
        })
        .catch(() => {
            showScreen('screen-state-check');
            startOnboardingChat();
        });
}

// ===== ONBOARDING =====

function appendOnboardingMessage(role, text, toneClass = '') {
    const chat = document.getElementById('onboarding-chat');
    if (!chat) return;

    const div = document.createElement('div');
    div.className = `message ${role} ${toneClass}`.trim();
    div.innerHTML = `<p>${escapeHtml(text)}</p>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function startOnboardingChat() {
    const controls = document.getElementById('onboarding-controls');
    if (!controls) return;

    controls.innerHTML = `
        <button class="reply-btn" onclick="answerOnboarding('mood', 'calm')">😌 Спокойно</button>
        <button class="reply-btn" onclick="answerOnboarding('mood', 'anxious')">😟 Беспокойно</button>
        <button class="reply-btn" onclick="answerOnboarding('mood', 'overwhelmed')">😫 Тяжело</button>
    `;
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
    } catch (e) {
        return { success: false };
    }
}

async function answerOnboarding(step, value) {
    const controls = document.getElementById('onboarding-controls');
    if (controls) controls.querySelectorAll('button').forEach(button => button.disabled = true);

    if (step === 'mood') {
        userState.mood = value;
        appendOnboardingMessage('user', value === 'calm' ? 'Спокойно' : value === 'anxious' ? 'Беспокойно' : 'Тяжело');
        appendOnboardingMessage('assistant', value === 'overwhelmed' ? 'Понял. Буду отвечать коротко и просто.' : 'Понял. Подстрою стиль под вас.');
        renderOnboardingControls('simple_mode');
        appendOnboardingMessage('assistant', 'Нужен ли вам очень простой режим?');
        await saveOnboardingState();
        return;
    }

    if (step === 'simpleMode') {
        userState.simpleMode = Boolean(value);
        appendOnboardingMessage('user', value ? 'Да, нужен' : 'Нет, обычный');
        renderOnboardingControls('theme');
        appendOnboardingMessage('assistant', 'Какую цветовую тему выберете?');
        await saveOnboardingState();
        return;
    }

    if (step === 'themeChoice') {
        userState.themeChoice = value;
        appendOnboardingMessage('user', value === 'light' ? 'Светлая' : value === 'warm' ? 'Теплая' : 'Контрастная');
        applyTheme(userState.mood, userState.communication, userState.simpleMode, userState.themeChoice, userState.fontSize);
        renderOnboardingControls('font');
        appendOnboardingMessage('assistant', 'Какой размер шрифта вам комфортнее?');
        await saveOnboardingState();
        return;
    }

    if (step === 'fontSize') {
        userState.fontSize = value;
        appendOnboardingMessage('user', value === 'small' ? 'Маленький' : value === 'medium' ? 'Средний' : 'Крупный');
        applyTheme(userState.mood, userState.communication, userState.simpleMode, userState.themeChoice, userState.fontSize);
        renderOnboardingControls('done');
        appendOnboardingMessage('assistant', 'Спасибо. Идем дальше к выбору задачи.');
        await saveOnboardingState();

        setTimeout(() => {
            showScreen('screen-problem-choice');
        }, 600);
    }
}

async function goToProblems() {
    showScreen('screen-state-check');
    startOnboardingChat();
}

// ===== PROBLEM CHOICE =====

function selectProblem(problem) {
    userState.selectedProblem = problem;
    document.querySelectorAll('.problem-btn').forEach(btn => btn.classList.remove('active'));

    if (problem === 'jobs') {
        goToJobsRoute();
        return;
    }

    showDemoMessage(problem);
}

function showDemoMessage() {
    alert('Этот раздел скоро будет доступен. Сейчас работает путь поиска работы.');
}

async function goToCharacteristics() {
    if (!userState.selectedProblem) {
        alert('Пожалуйста, выберите проблему');
        return;
    }

    await goToJobsRoute();
}

// ===== UNIFIED CAREER CHAT =====

function appendPlanChatMessage(role, text) {
    const chat = document.getElementById('career-chat');
    if (!chat) return;

    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<p>${escapeHtml(text)}</p>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

async function requestUnifiedCareer(message, isInit = false) {
    const response = await fetch('/api/chat/career', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            message,
            is_init: isInit
        })
    });

    return await response.json();
}

function setPlanActionsVisible(visible) {
    const actions = document.getElementById('plan-actions');
    if (actions) actions.style.display = visible ? 'flex' : 'none';
}

async function goToJobsRoute() {
    showScreen('screen-career-chat');

    const careerChat = document.getElementById('career-chat');
    if (careerChat) careerChat.innerHTML = '';

    userState.careerPhase = 'interview';
    userState.planApproved = false;

    appendPlanChatMessage('assistant', 'Начинаю короткое интервью, чтобы составить персональный план.');

    try {
        const data = await requestUnifiedCareer('', true);
        if (data.success) {
            userState.careerPhase = data.phase || 'interview';
            appendPlanChatMessage('assistant', data.message);
        } else {
            appendPlanChatMessage('assistant', `Ошибка: ${data.message}`);
        }
    } catch (e) {
        appendPlanChatMessage('assistant', 'Ошибка сервера. Попробуйте еще раз.');
    }
}

async function sendPlanMessage() {
    const input = document.getElementById('career-input');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    appendPlanChatMessage('user', message);
    input.value = '';

    try {
        const data = await requestUnifiedCareer(message, false);

        if (!data.success) {
            appendPlanChatMessage('assistant', `Ошибка: ${data.message}`);
            return;
        }

        userState.careerPhase = data.phase || userState.careerPhase;
        appendPlanChatMessage('assistant', data.message);

        if (data.phase === 'approved' || data.plan_confirmed === true) {
            approvePlanAndStart(false);
        }
    } catch (e) {
        appendPlanChatMessage('assistant', 'Ошибка сервера. Попробуйте еще раз.');
    }
}

function requestPlanSimplify() {
    const input = document.getElementById('career-input');
    if (!input) return;
    input.value = 'Сделайте план проще и короче';
    sendPlanMessage();
}

async function sendCareerMessage() {
    return sendPlanMessage();
}

function approvePlanAndStart(sendToAgent = true) {
    if (sendToAgent) {
        const input = document.getElementById('career-input');
        if (input) {
            input.value = 'Мне нравится план';
            sendPlanMessage();
        }
        return;
    }

    userState.planApproved = true;
    showCareerTabs('resume-step');
}

// ===== TABS =====

function openTab(tabName) {
    document.getElementById('tabs-container').style.display = 'block';

    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    const tabContent = document.getElementById(tabName);
    const tabBtn = document.querySelector(`[data-tab="${tabName}"]`);

    if (tabContent) tabContent.classList.add('active');
    if (tabBtn) tabBtn.classList.add('active');

    window.scrollTo(0, 0);
}

function stepComplete(stepNum) {
    const statusEl = document.getElementById(`status-${stepNum}`);
    if (statusEl) {
        statusEl.innerHTML = '✅ Завершено';
        statusEl.style.color = '#28a745';
    }
}

function speakPhrase(phrase) {
    const utterance = new SpeechSynthesisUtterance(phrase);
    utterance.lang = 'sk-SK';
    window.speechSynthesis.speak(utterance);
}

// ===== OTHER CHATS =====

async function sendResumeMessage() {
    await sendGenericChatMessage('resume-input', 'resume-chat', '/api/chat/resume');
}

async function sendLanguageMessage() {
    await sendGenericChatMessage('language-input', 'language-chat', '/api/chat/language');
}

async function sendJobsMessage() {
    await sendGenericChatMessage('jobs-input', 'jobs-chat', '/api/chat/jobs');
}

async function sendInitialMessage() {
    await sendGenericChatMessage('initial-input', 'initial-chat', '/api/chat/initial');
}

async function sendGenericChatMessage(inputId, chatId, endpoint) {
    const input = document.getElementById(inputId);
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    addMessageToChat(chatId, message, 'user');
    input.value = '';
    showLoadingMessage(chatId);

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });

        const data = await response.json();
        removeLastMessage(chatId);

        if (data.success) {
            addMessageToChat(chatId, data.message, 'assistant');
        } else {
            addMessageToChat(chatId, 'Ошибка: ' + data.message, 'assistant');
        }
    } catch (e) {
        removeLastMessage(chatId);
        addMessageToChat(chatId, 'Ошибка сервера', 'assistant');
    }
}

function generatePDF() {
    window.open(`/api/generate-pdf/${encodeURIComponent(userId)}`, '_blank');
}

function addMessageToChat(chatId, message, role) {
    const chatEl = document.getElementById(chatId);
    if (!chatEl) return;

    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<p>${escapeHtml(message)}</p>`;
    chatEl.appendChild(div);
    chatEl.scrollTop = chatEl.scrollHeight;
}

function showLoadingMessage(chatId) {
    const chatEl = document.getElementById(chatId);
    if (!chatEl) return;

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant loading';
    loadingDiv.id = 'loading-msg';
    loadingDiv.innerHTML = '<p>⏳ Загрузка...</p>';
    chatEl.appendChild(loadingDiv);
    chatEl.scrollTop = chatEl.scrollHeight;
}

function removeLastMessage(chatId) {
    const chatEl = document.getElementById(chatId);
    if (!chatEl) return;

    const loadingMsg = chatEl.querySelector('#loading-msg');
    if (loadingMsg) loadingMsg.remove();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== ENTER HANDLER =====

document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        const active = document.activeElement;
        if (!active) return;

        if (active.id === 'career-input') {
            e.preventDefault();
            sendCareerMessage();
        } else if (active.id === 'resume-input') {
            e.preventDefault();
            sendResumeMessage();
        } else if (active.id === 'jobs-input') {
            e.preventDefault();
            sendJobsMessage();
        } else if (active.id === 'language-input') {
            e.preventDefault();
            sendLanguageMessage();
        } else if (active.id === 'initial-input') {
            e.preventDefault();
            sendInitialMessage();
        }
    }
});
