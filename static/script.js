// Переменные
const userId = generateUserId();
let knowsSlovak = null;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    setupTabsNavigation();
    setupEnterKeyListeners();
});

// ===== FUNCTIONS =====

function generateUserId() {
    return 'user_' + Math.random().toString(36).substr(2, 9);
}

function setupTabsNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');

            // Remove active class from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked tab
            this.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        });
    });
}

function setupEnterKeyListeners() {
    const inputs = document.querySelectorAll('.chat-input');
    inputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                // Determine which tab this input belongs to
                if (this.id === 'initial-input') {
                    sendInitialMessage();
                } else if (this.id === 'language-input') {
                    sendLanguageMessage();
                } else if (this.id === 'resume-input') {
                    sendResumeMessage();
                } else if (this.id === 'jobs-input') {
                    sendJobsMessage();
                }
            }
        });
    });
}

// ===== TAB 1: INITIAL CONSULTATION =====

async function sendInitialMessage() {
    const input = document.getElementById('initial-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessageToChat('initial-chat', message, 'user');
    input.value = '';

    // Show loading
    showLoadingMessage('initial-chat');

    try {
        const response = await fetch('/api/chat/initial', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });

        const data = await response.json();

        // Remove loading message
        removeLastMessage('initial-chat');

        if (data.success) {
            addMessageToChat('initial-chat', data.message, 'assistant');

            // Показываем пошаговый план если он был сгенерирован
            if (data.plan_generated && data.action_plan) {
                displayActionPlan('initial-chat', data.action_plan);
            }

        } else {
            addMessageToChat('initial-chat', 'Ошибка: ' + data.message, 'assistant');
        }
    } catch (error) {
        removeLastMessage('initial-chat');
        addMessageToChat('initial-chat', 'Ошибка подключения: ' + error.message, 'assistant');
    }
}

// ===== TAB 2: LANGUAGE LEARNING =====

async function sendLanguageMessage() {
    const input = document.getElementById('language-input');
    const levelSelect = document.getElementById('language-level');
    const message = input.value.trim();
    const level = levelSelect.value;

    if (!message) return;

    addMessageToChat('language-chat', message, 'user');
    input.value = '';

    showLoadingMessage('language-chat');

    try {
        const response = await fetch('/api/chat/language', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                message: message,
                lesson_level: level
            })
        });

        const data = await response.json();
        removeLastMessage('language-chat');

        if (data.success) {
            addMessageToChat('language-chat', data.message, 'assistant');
        } else {
            addMessageToChat('language-chat', 'Ошибка: ' + data.message, 'assistant');
        }
    } catch (error) {
        removeLastMessage('language-chat');
        addMessageToChat('language-chat', 'Ошибка подключения: ' + error.message, 'assistant');
    }
}

// ===== TAB 3: RESUME CREATION =====

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
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });

        const data = await response.json();
        removeLastMessage('resume-chat');

        if (data.success) {
            addMessageToChat('resume-chat', data.message, 'assistant');

            // If resume is ready, show PDF button
            if (data.resume_ready) {
                showPDFButton();
            }
        } else {
            addMessageToChat('resume-chat', 'Ошибка: ' + data.message, 'assistant');
        }
    } catch (error) {
        removeLastMessage('resume-chat');
        addMessageToChat('resume-chat', 'Ошибка подключения: ' + error.message, 'assistant');
    }
}

function showPDFButton() {
    const pdfBtn = document.getElementById('pdf-btn');
    pdfBtn.style.display = 'block';
}

function generatePDF() {
    window.location.href = `/api/generate-pdf/${userId}`;
}

// ===== TAB 4: JOB SEARCH =====

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
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });

        const data = await response.json();
        removeLastMessage('jobs-chat');

        if (data.success) {
            addMessageToChat('jobs-chat', data.message, 'assistant');

            // Display job suggestions if available
            if (data.job_suggestions && data.job_suggestions.length > 0) {
                displayJobSuggestions(data.job_suggestions);
            }
        } else {
            addMessageToChat('jobs-chat', 'Ошибка: ' + data.message, 'assistant');
        }
    } catch (error) {
        removeLastMessage('jobs-chat');
        addMessageToChat('jobs-chat', 'Ошибка подключения: ' + error.message, 'assistant');
    }
}

function displayJobSuggestions(suggestions) {
    const jobsList = document.getElementById('jobs-list');
    const jobsResults = document.getElementById('jobs-results');

    jobsResults.innerHTML = '';

    suggestions.forEach(job => {
        const jobCard = document.createElement('div');
        jobCard.className = 'job-card';
        jobCard.innerHTML = `
            <h4>${job}</h4>
            <p>Введите подробный поиск в чате для получения информации о конкретных вакансиях</p>
        `;
        jobsResults.appendChild(jobCard);
    });

    jobsList.style.display = 'block';
}

function displayActionPlan(chatId, plan) {
    const chatMessages = document.getElementById(chatId);
    const planDiv = document.createElement('div');
    planDiv.className = 'action-plan';
    
    // Заголовок плана
    let planHTML = `
        <div class="plan-header">
            <h3>${plan.title}</h3>
            <p class="plan-intro">${plan.intro}</p>
        </div>
        <div class="plan-steps">
    `;
    
    // Шаги плана
    plan.steps.forEach((step, index) => {
        planHTML += `
            <div class="plan-step">
                <div class="step-badge">${step.number}</div>
                <div class="step-content">
                    <h4>
                        <span class="step-tab-badge">${step.tab}</span>
                        ${step.title}
                    </h4>
                    <p>${step.description}</p>
                </div>
            </div>
        `;
    });
    
    planHTML += `</div>`;
    
    // Время выполнения
    planHTML += `<div class="plan-time">⏱️ Примерное время: ${plan.estimated_time}</div>`;
    
    // Специальный совет если есть
    if (plan.special_advice) {
        planHTML += `<div class="plan-advice">${plan.special_advice}</div>`;
    }
    
    planDiv.innerHTML = planHTML;
    chatMessages.appendChild(planDiv);
    
    // Auto scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ===== CHAT UTILITIES =====

function addMessageToChat(chatId, message, role) {
    const chatMessages = document.getElementById(chatId);
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const p = document.createElement('p');
    p.textContent = message;

    messageDiv.appendChild(p);
    chatMessages.appendChild(messageDiv);

    // Auto scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showLoadingMessage(chatId) {
    const chatMessages = document.getElementById(chatId);
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant loading-message';

    const p = document.createElement('p');
    const span = document.createElement('span');
    span.className = 'loading';
    p.appendChild(span);
    p.textContent = ' Обработка...';

    loadingDiv.appendChild(p);
    chatMessages.appendChild(loadingDiv);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeLastMessage(chatId) {
    const chatMessages = document.getElementById(chatId);
    const lastMessage = chatMessages.lastChild;
    if (lastMessage && lastMessage.classList.contains('loading-message')) {
        lastMessage.remove();
    }
}
