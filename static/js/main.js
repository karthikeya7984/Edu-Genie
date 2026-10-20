// EduGenie Core Frontend Controller

// State Management
const State = {
    token: localStorage.getItem('token') || null,
    user: null,
    currentModule: 'overview',
    quiz: {
        id: null,
        questions: [],
        currentIndex: 0,
        score: 0,
        timer: null,
        timeLeft: 0,
        userAnswers: []
    },
    flashcards: {
        cards: [],
        currentIndex: 0
    },
    settings: {
        selected_model: 'llama3.2',
        temperature: 0.7,
        max_tokens: 2048,
        theme: 'dark'
    },
    documents: [],
    currentDoc: null,
    docQuiz: {
        questions: [],
        currentIndex: 0,
        score: 0,
        userAnswers: []
    },
    docFlashcards: {
        cards: [],
        currentIndex: 0
    }
};

// Initialization on DOM Load
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

// App Router & Initializer
function initApp() {
    const path = window.location.pathname;
    
    // Check Theme
    applyTheme(localStorage.getItem('theme') || 'dark');
    
    if (path === '/dashboard') {
        if (!State.token) {
            window.location.href = '/';
            return;
        }
        setupDashboard();
    } else {
        // Landing Page Initializations
        setupLandingPage();
        if (State.token) {
            // Update CTA buttons on hero if already logged in
            const ctaBtn = document.getElementById('hero-cta-btn');
            if (ctaBtn) {
                ctaBtn.innerHTML = 'Go to Dashboard <i class="fas fa-arrow-right ms-2"></i>';
                ctaBtn.removeAttribute('data-bs-toggle');
                ctaBtn.removeAttribute('data-bs-target');
                ctaBtn.onclick = () => window.location.href = '/dashboard';
            }
        }
    }
}

// LANDING PAGE LOGIC
function setupLandingPage() {
    // Smooth scrolling header transitions
    window.addEventListener('scroll', () => {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            if (window.scrollY > 50) {
                navbar.style.padding = '10px 0';
                navbar.style.background = 'rgba(11, 16, 32, 0.95) !important';
            } else {
                navbar.style.padding = '20px 0';
                navbar.style.background = 'rgba(11, 16, 32, 0.75) !important';
            }
        }
    });

    // AOS / Scroll and GSAP animations loading triggers
    if (typeof gsap !== 'undefined') {
        gsap.from(".hero-title", {opacity: 0, y: 50, duration: 1, delay: 0.2});
        gsap.from(".hero-subtitle", {opacity: 0, y: 30, duration: 1, delay: 0.5});
        gsap.from(".hero-cta-group", {opacity: 0, y: 20, duration: 0.8, delay: 0.8});
        gsap.from(".robot-illustration", {opacity: 0, scale: 0.8, duration: 1.2, delay: 0.5});
    }
}

// Modal Helpers
function openLoginModal() {
    const modalEl = document.getElementById('loginModal');
    if (modalEl && typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
}

function openSignupModal() {
    const modalEl = document.getElementById('signupModal');
    if (modalEl && typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
}

// AUTHENTICATION LOGIC
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    toggleButtonLoading('loginBtn', true);
    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('token', data.access_token);
            showToast('Welcome back to EduGenie!', 'success');
            setTimeout(() => window.location.href = '/dashboard', 1000);
        } else {
            showToast(data.detail || 'Login failed', 'danger');
        }
    } catch (err) {
        showToast('Network error, please try again.', 'danger');
    } finally {
        toggleButtonLoading('loginBtn', false);
    }
}

async function handleQuickDemoLogin() {
    const emailInput = document.getElementById('loginEmail');
    const pwdInput = document.getElementById('loginPassword');
    if (emailInput) emailInput.value = 'demo@edugenie.com';
    if (pwdInput) pwdInput.value = 'password123';
    
    const fakeEvent = { preventDefault: () => {} };
    await handleLogin(fakeEvent);
}

async function handleSignup(e) {
    e.preventDefault();
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const role = document.getElementById('signupRole').value;
    
    toggleButtonLoading('signupBtn', true);
    try {
        const res = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, email, password, role })
        });
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('token', data.access_token);
            showToast('Account created successfully!', 'success');
            setTimeout(() => window.location.href = '/dashboard', 1000);
        } else {
            showToast(data.detail || 'Signup failed', 'danger');
        }
    } catch (err) {
        showToast('Network error during registration.', 'danger');
    } finally {
        toggleButtonLoading('signupBtn', false);
    }
}

// Google Login Simulation
function handleGoogleLogin() {
    const dummyGoogleEmail = "google_learner_" + Math.floor(Math.random() * 1000) + "@gmail.com";
    showToast('Redirecting to Google...', 'success');
    
    setTimeout(async () => {
        try {
            const res = await fetch('/api/auth/google', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    email: dummyGoogleEmail,
                    name: "Google Student"
                })
            });
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem('token', data.access_token);
                window.location.href = '/dashboard';
            } else {
                showToast('Google login simulation failed.', 'danger');
            }
        } catch (err) {
            showToast('Google authentication timeout.', 'danger');
        }
    }, 800);
}

// Forgot Password / OTP Verification Simulation
function triggerForgotPassword() {
    const email = prompt("Enter your registered email address:");
    if (!email) return;
    
    showToast('Sending OTP verification code to ' + email, 'warning');
    setTimeout(() => {
        // Show simulated OTP modal prompt
        showToast('SIMULATED OTP: Use 123456 to verify.', 'success');
        const otpCode = prompt("Enter 6-digit OTP code sent to your email:");
        if (otpCode === '123456') {
            const newPassword = prompt("Enter your new secure password:");
            if (newPassword) {
                resetPasswordRequest(email, newPassword);
            }
        } else {
            alert("Invalid OTP code. Authentication failed.");
        }
    }, 1200);
}

async function resetPasswordRequest(email, password) {
    try {
        const res = await fetch('/api/auth/reset-password', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ email, password })
        });
        if (res.ok) {
            showToast('Password reset successfully! Please login.', 'success');
        } else {
            showToast('Error resetting password.', 'danger');
        }
    } catch (err) {
        showToast('Network error during reset.', 'danger');
    }
}

// DASHBOARD STATE ENGINE
async function setupDashboard() {
    // Load profile
    await fetchUserProfile();
    // Load Settings
    await fetchUserSettings();
    // Initialize history, notes, bookmarks
    fetchHistory();
    fetchNotes();
    fetchBookmarks();
    
    // Setup Search Event
    const searchInput = document.getElementById('dashboardSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => handleGlobalSearch(e.target.value));
    }
    
    // Hook up dynamic user data in templates
    updateDashboardUIElements();
    
    // Setup Document Dropzone & load documents
    setupDocumentDropzone();
    loadUserDocuments();
}

async function fetchUserProfile() {
    try {
        const res = await fetch('/api/auth/profile', {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            State.user = await res.json();
            
            // Adjust Sidebar if admin
            const adminLink = document.getElementById('sidebar-admin-link');
            if (adminLink) {
                if (State.user.role === 'admin') {
                    adminLink.style.display = 'flex';
                } else {
                    adminLink.style.display = 'none';
                }
            }
        } else {
            logout();
        }
    } catch (err) {
        console.error('Failed to load profile.', err);
    }
}

async function fetchUserSettings() {
    try {
        // Query local Ollama models from backend
        let detectedModels = [];
        let defaultModel = "llama3.2";
        try {
            const modelsRes = await fetch('/api/ai/models');
            if (modelsRes.ok) {
                const modelsData = await modelsRes.json();
                detectedModels = modelsData.models || [];
                if (modelsData.default) defaultModel = modelsData.default;
            }
        } catch (e) {
            console.warn("Could not query /api/ai/models:", e);
        }

        const res = await fetch('/api/db/settings', {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            State.settings = await res.json();
            const modelSelect = document.getElementById('settingsModel');
            const tempSlider = document.getElementById('settingsTemp');
            const tempVal = document.getElementById('settingsTempVal');
            const maxTokensInput = document.getElementById('settingsTokens');
            const statusBadge = document.getElementById('ollamaStatusBadge');
            
            // Populate models dropdown if detected
            if (modelSelect && detectedModels.length > 0) {
                modelSelect.innerHTML = '';
                detectedModels.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = `Ollama: ${m} (Local Model)`;
                    modelSelect.appendChild(opt);
                });
                // Cloud fallback option
                const fallbackOpt = document.createElement('option');
                fallbackOpt.value = 'llama-3.3-70b-versatile';
                fallbackOpt.textContent = 'Cloud: Llama 3.3 70B (Groq)';
                modelSelect.appendChild(fallbackOpt);
            }

            // Standardize legacy / placeholder model values to local default
            let currentModel = State.settings.selected_model;
            if (!currentModel || currentModel.includes('gemini') || currentModel === 'local-llm' || currentModel === 'llama-3.3-70b-versatile') {
                currentModel = defaultModel;
            }
            State.settings.selected_model = currentModel;

            if (modelSelect) {
                modelSelect.value = currentModel;
                if (!modelSelect.value && modelSelect.options.length > 0) {
                    modelSelect.selectedIndex = 0;
                }
            }
            if (statusBadge) {
                statusBadge.innerHTML = `<i class="fas fa-check-circle me-1"></i>Ollama: ${modelSelect ? modelSelect.value : defaultModel}`;
            }

            if (tempSlider) {
                tempSlider.value = State.settings.temperature;
                if (tempVal) tempVal.innerText = State.settings.temperature;
            }
            if (maxTokensInput) maxTokensInput.value = State.settings.max_tokens;
            
            applyTheme(State.settings.theme);
        }
    } catch (err) {
        console.error(err);
    }
}

function updateDashboardUIElements() {
    if (!State.user) return;
    
    // Bind generic greeting & streak variables
    const userNames = document.querySelectorAll('.user-display-name');
    userNames.forEach(el => el.innerText = State.user.name);
    
    const userEmails = document.querySelectorAll('.user-display-email');
    userEmails.forEach(el => el.innerText = State.user.email);
    
    const streakElements = document.querySelectorAll('.streak-display');
    streakElements.forEach(el => el.innerText = State.user.learning_streak + ' Days');
    
    // Bind Profile inputs
    const profName = document.getElementById('profileName');
    const profEducation = document.getElementById('profileEducation');
    const profSkills = document.getElementById('profileSkills');
    const profAchievements = document.getElementById('profileAchievements');
    
    if (profName) profName.value = State.user.name;
    if (profEducation) profEducation.value = State.user.education || '';
    if (profSkills) profSkills.value = State.user.skills || '';
    if (profAchievements) profAchievements.value = State.user.achievements || '';
}

// ROUTING / TAB SWITCHER
function switchModule(moduleName) {
    State.currentModule = moduleName;
    
    // Deactivate all views and sidebar highlights
    document.querySelectorAll('.module-view').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('active'));
    
    // Activate target view
    const targetView = document.getElementById(`${moduleName}-module`);
    if (targetView) targetView.classList.add('active');
    
    // Activate target sidebar link
    const targetLink = document.querySelector(`[onclick="switchModule('${moduleName}')"]`);
    if (targetLink) targetLink.classList.add('active');
    
    // Trigger module specific page loading actions
    if (moduleName === 'admin') {
        loadAdminAnalytics();
    } else if (moduleName === 'profile') {
        updateDashboardUIElements();
    } else if (moduleName === 'overview') {
        updateOverviewAnalytics();
    } else if (moduleName === 'document') {
        loadUserDocuments();
    }
}

// DYNAMIC AI MODULE API CONNECTORS
async function callAI(module, promptId, resultId, extra = {}) {
    const promptInput = document.getElementById(promptId);
    if (!promptInput) return;
    const prompt = promptInput.value.trim();
    const resultBox = document.getElementById(resultId);
    const loader = document.getElementById('loader-' + module);
    
    if (!prompt) {
        showToast('Please enter a query or topic.', 'warning');
        return;
    }

    // 1. CHAT MODULE: Real-time Interactive Streaming
    if (module === 'chat') {
        const chatContainer = resultBox;
        const userBubble = document.createElement('div');
        userBubble.className = 'message-bubble user';
        userBubble.innerHTML = `
            <div class="message-content">${escapeHtml(prompt)}</div>
            <div class="message-avatar">${State.user?.name ? State.user.name.slice(0, 2).toUpperCase() : 'ME'}</div>
        `;
        chatContainer.appendChild(userBubble);
        promptInput.value = '';
        chatContainer.scrollTop = chatContainer.scrollHeight;

        const aiBubble = document.createElement('div');
        aiBubble.className = 'message-bubble assistant';
        aiBubble.innerHTML = `
            <div class="message-avatar">EG</div>
            <div class="message-content markdown-body">
                <span class="spinner-grow spinner-grow-sm text-primary me-2"></span><em>Ollama thinking...</em>
            </div>
        `;
        chatContainer.appendChild(aiBubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        const contentDiv = aiBubble.querySelector('.message-content');

        try {
            const streamRes = await fetch('/api/ai/stream/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${State.token}`
                },
                body: JSON.stringify({ prompt: prompt, ...extra })
            });

            if (streamRes.ok && streamRes.body) {
                const reader = streamRes.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let fullText = '';
                contentDiv.innerHTML = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunkStr = decoder.decode(value, { stream: true });
                    const lines = chunkStr.split('\n');
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const payload = JSON.parse(line.slice(6));
                                if (payload.chunk) {
                                    fullText += payload.chunk;
                                    contentDiv.innerHTML = parseMarkdownToHTML(fullText);
                                    chatContainer.scrollTop = chatContainer.scrollHeight;
                                }
                            } catch (e) {}
                        }
                    }
                }
                if (!fullText) {
                    contentDiv.innerHTML = '<span class="text-muted">Response completed.</span>';
                }
                fetchHistory();
                return;
            }
        } catch (err) {
            console.warn('Stream chat fallback to standard request:', err);
        }
    }

    // 2. CONCEPT EXPLAINER: Real-time Streaming & RAG Matrix
    if (module === 'explain') {
        resultBox.innerHTML = `
            <div class="p-3">
                <div class="d-flex align-items-center mb-3 text-info small">
                    <span class="spinner-grow spinner-grow-sm text-primary me-2"></span>
                    <span><i class="fas fa-bolt text-warning me-1"></i><strong>Dense Vector RAG Active</strong> — Searching vector matrix & streaming with Ollama...</span>
                </div>
                <div id="streamingExplainContent" class="markdown-body p-2" style="min-height: 80px;">
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text" style="width:75%"></div>
                </div>
            </div>
        `;
        const contentDiv = document.getElementById('streamingExplainContent');
        if (loader) loader.style.display = 'none';

        try {
            const streamRes = await fetch('/api/ai/stream/explain', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${State.token}`
                },
                body: JSON.stringify({ prompt: prompt, ...extra })
            });

            if (streamRes.ok && streamRes.body) {
                const reader = streamRes.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let fullText = '';
                let firstChunk = true;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunkStr = decoder.decode(value, { stream: true });
                    const lines = chunkStr.split('\n');
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const payload = JSON.parse(line.slice(6));
                                if (payload.chunk) {
                                    if (firstChunk) {
                                        contentDiv.innerHTML = '';
                                        firstChunk = false;
                                    }
                                    fullText += payload.chunk;
                                    contentDiv.innerHTML = parseMarkdownToHTML(fullText);
                                }
                            } catch (e) {}
                        }
                    }
                }

                if (fullText) {
                    emulateTextStreaming(fullText, resultBox, module);
                    fetchHistory();
                    return;
                }
            }
        } catch (streamErr) {
            console.warn('Stream explain fallback:', streamErr);
        }
    }
    
    // 3. STANDARD / STRUCTURED MODULES (Quiz, Roadmap, Flashcards, QA)
    resultBox.innerHTML = `
        <div class="p-3">
            <div class="d-flex align-items-center mb-2 text-info small">
                <span class="spinner-grow spinner-grow-sm text-primary me-2"></span>
                <span><i class="fas fa-brain text-warning me-1"></i>Processing with Ollama AI Engine...</span>
            </div>
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text" style="width:80%"></div>
        </div>
    `;
    if (loader) loader.style.display = 'block';
    
    try {
        const res = await fetch(`/api/ai/${module}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({ prompt: prompt, ...extra })
        });
        const data = await res.json();
        
        if (res.ok) {
            if (module === 'quiz') {
                setupQuizInterface(JSON.parse(data.data));
            } else if (module === 'roadmap') {
                renderRoadmapInterface(JSON.parse(data.data), resultBox);
            } else if (module === 'flashcards') {
                setupFlashcardInterface(JSON.parse(data.data));
            } else {
                emulateTextStreaming(data.data, resultBox, module);
            }
            fetchHistory();
        } else {
            resultBox.innerHTML = `<div class="text-danger p-3"><i class="fas fa-exclamation-triangle me-2"></i>Error: ${data.detail || 'Service issue'}</div>`;
        }
    } catch (err) {
        resultBox.innerHTML = `<div class="text-danger p-3"><i class="fas fa-wifi me-2"></i>Network connection error.</div>`;
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

// Markdown and Stream Emulator
function emulateTextStreaming(rawText, targetContainer, module) {
    targetContainer.innerHTML = '';
    
    // Convert basic markdown tags to styled HTML
    let parsedHTML = parseMarkdownToHTML(rawText);
    
    // Add wrap containers
    let wrapper = document.createElement('div');
    wrapper.className = "streaming-wrapper";
    targetContainer.appendChild(wrapper);
    
    // Add control buttons (Copy, Save Note, Bookmark)
    let controls = document.createElement('div');
    controls.className = "d-flex justify-content-end gap-2 mb-3 mt-2";
    controls.innerHTML = `
        <button class="btn btn-sm btn-outline-secondary" onclick="copyResultText(this, \`${encodeURIComponent(rawText)}\`)">
            <i class="far fa-copy me-1"></i> Copy
        </button>
        <button class="btn btn-sm btn-outline-secondary" onclick="saveAsNote(this, '${module}', \`${encodeURIComponent(rawText)}\`)">
            <i class="far fa-sticky-note me-1"></i> Save as Note
        </button>
        <button class="btn btn-sm btn-outline-secondary" onclick="bookmarkItem(this, '${module}', \`${encodeURIComponent(rawText)}\`)">
            <i class="far fa-bookmark me-1"></i> Bookmark
        </button>
    `;
    wrapper.appendChild(controls);
    
    let contentContainer = document.createElement('div');
    contentContainer.className = "content-body markdown-body";
    wrapper.appendChild(contentContainer);
    
    // Simple incremental output emulation (micro-animation)
    let words = parsedHTML.split(" ");
    let index = 0;
    
    // Output 8 words at a time for smooth streaming feel
    function streamNextChunk() {
        if (index < words.length) {
            let nextIndex = Math.min(index + 8, words.length);
            let slice = words.slice(0, nextIndex).join(" ");
            contentContainer.innerHTML = slice;
            index = nextIndex;
            setTimeout(streamNextChunk, 20);
        }
    }
    
    streamNextChunk();
}

// Basic Custom Markdown Parser
function parseMarkdownToHTML(md) {
    let html = md;
    
    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function(match, lang, code) {
        return `<pre class="bg-black p-3 rounded text-white my-3"><code class="language-${lang}">${code.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</code></pre>`;
    });
    
    // Headings
    html = html.replace(/^### (.*$)/gim, '<h4 class="mt-3 text-secondary">$1</h4>')
               .replace(/^## (.*$)/gim, '<h3 class="mt-3 border-bottom pb-2">$1</h3>')
               .replace(/^# (.*$)/gim, '<h2 class="mt-3 text-gradient-purple">$1</h2>');
               
    // Bold / Italics
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Lists
    html = html.replace(/^\s*-\s*(.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/sim, '<ul class="my-2">$1</ul>');
    
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// ACTION UTILS (Copy, Notes, Bookmarks)
function copyResultText(btn, encodedText) {
    const text = decodeURIComponent(encodedText);
    navigator.clipboard.writeText(text).then(() => {
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check text-success me-1"></i> Copied!';
        showToast('Text copied to clipboard.', 'success');
        setTimeout(() => btn.innerHTML = originalHTML, 1500);
    });
}

async function saveAsNote(btn, module, encodedText) {
    const text = decodeURIComponent(encodedText);
    const title = prompt("Enter a title for this note:", `${module.toUpperCase()} Note - ` + new Date().toLocaleDateString());
    if (!title) return;
    
    try {
        const res = await fetch('/api/db/notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({ title, content: text })
        });
        if (res.ok) {
            showToast('Saved to Notes!', 'success');
            fetchNotes();
        } else {
            showToast('Failed to save note.', 'danger');
        }
    } catch (err) {
        showToast('Error connecting to notes DB.', 'danger');
    }
}

async function bookmarkItem(btn, module, encodedText) {
    const text = decodeURIComponent(encodedText);
    const title = `${module.toUpperCase()} Result - ` + new Date().toLocaleDateString();
    
    try {
        const res = await fetch('/api/db/bookmarks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({
                target_type: module,
                title: title,
                details: text.substring(0, 150) + "..."
            })
        });
        if (res.ok) {
            showToast('Bookmarked successfully!', 'success');
            fetchBookmarks();
        } else {
            showToast('Failed to save bookmark.', 'danger');
        }
    } catch (err) {
        showToast('Error saving bookmark.', 'danger');
    }
}

// DYNAMIC INTERFACES (Quiz, Roadmaps, Flashcards)

// 1. Quiz UI Engine
function setupQuizInterface(quizData) {
    const resultBox = document.getElementById('quiz-result');
    if (!resultBox) return;
    
    // Clear any previous timer
    if (State.quiz.timer) clearInterval(State.quiz.timer);
    
    State.quiz.id = quizData.quiz_id;
    State.quiz.questions = quizData.questions;
    State.quiz.currentIndex = 0;
    State.quiz.score = 0;
    State.quiz.timeLeft = State.quiz.questions.length * 45; // 45s per question
    State.quiz.userAnswers = [];
    
    startQuizTimer();
    renderQuizQuestion();
}

function startQuizTimer() {
    const timerText = document.getElementById('quiz-timer-text');
    if (timerText) timerText.style.display = 'block';
    
    State.quiz.timer = setInterval(() => {
        State.quiz.timeLeft--;
        if (timerText) {
            const minutes = Math.floor(State.quiz.timeLeft / 60);
            const seconds = State.quiz.timeLeft % 60;
            timerText.innerHTML = `<i class="far fa-clock me-1"></i> Time: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
        }
        
        if (State.quiz.timeLeft <= 0) {
            submitQuizResults();
        }
    }, 1000);
}

function renderQuizQuestion() {
    const resultBox = document.getElementById('quiz-result');
    if (!resultBox) return;
    
    const q = State.quiz.questions[State.quiz.currentIndex];
    const total = State.quiz.questions.length;
    
    let optionsHTML = '';
    q.options.forEach((opt) => {
        optionsHTML += `
            <button class="quiz-option-btn" onclick="selectQuizOption(this, '${opt}')">
                ${opt}
            </button>
        `;
    });
    
    resultBox.innerHTML = `
        <div class="quiz-card p-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <span class="badge bg-primary">Question ${State.quiz.currentIndex + 1} of ${total}</span>
            </div>
            <h4 class="mb-4">${q.question}</h4>
            <div class="quiz-options-group">
                ${optionsHTML}
            </div>
            <div class="mt-4 d-flex justify-content-end">
                <button class="btn btn-premium btn-sm" onclick="nextQuizQuestion()" disabled id="quizNextBtn">
                    Next Question <i class="fas fa-chevron-right ms-1"></i>
                </button>
            </div>
        </div>
    `;
}

let selectedAnswerTemp = null;
function selectQuizOption(btn, answer) {
    document.querySelectorAll('.quiz-option-btn').forEach(el => el.classList.remove('selected'));
    btn.classList.add('selected');
    selectedAnswerTemp = answer;
    
    const nextBtn = document.getElementById('quizNextBtn');
    if (nextBtn) nextBtn.removeAttribute('disabled');
}

function nextQuizQuestion() {
    const q = State.quiz.questions[State.quiz.currentIndex];
    
    // Save answer
    State.quiz.userAnswers.push({
        question_id: q.id,
        selected: selectedAnswerTemp,
        correct: q.answer
    });
    
    if (selectedAnswerTemp === q.answer) {
        State.quiz.score++;
    }
    
    selectedAnswerTemp = null;
    State.quiz.currentIndex++;
    
    if (State.quiz.currentIndex < State.quiz.questions.length) {
        renderQuizQuestion();
    } else {
        submitQuizResults();
    }
}

async function submitQuizResults() {
    clearInterval(State.quiz.timer);
    const timerText = document.getElementById('quiz-timer-text');
    if (timerText) timerText.style.display = 'none';
    
    const resultBox = document.getElementById('quiz-result');
    if (!resultBox) return;
    
    resultBox.innerHTML = `
        <div class="text-center p-4">
            <div class="loader d-block"></div>
            <p>Submitting quiz results...</p>
        </div>
    `;
    
    const total = State.quiz.questions.length;
    const timeSpent = (total * 45) - State.quiz.timeLeft;
    
    try {
        const res = await fetch('/api/ai/quiz/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({
                quiz_id: State.quiz.id,
                score: State.quiz.score,
                total_questions: total,
                time_spent: timeSpent,
                answers: State.quiz.userAnswers
            })
        });
        
        if (res.ok) {
            // Render scorecard UI
            let percentage = Math.round((State.quiz.score / total) * 100);
            let rating = percentage >= 80 ? 'Masterful! 🚀' : percentage >= 50 ? 'Good Job! 👍' : 'Keep Practicing! 📚';
            
            let answersReviewHTML = '';
            State.quiz.questions.forEach((q, idx) => {
                const userAns = State.quiz.userAnswers[idx];
                const isCorrect = userAns ? userAns.selected === q.answer : false;
                answersReviewHTML += `
                    <div class="border-bottom py-3">
                        <p class="fw-bold">${idx + 1}. ${q.question}</p>
                        <div class="ps-2 border-start ${isCorrect ? 'border-success' : 'border-danger'}">
                            <span class="d-block ${isCorrect ? 'text-success' : 'text-danger'}">
                                Your answer: ${userAns ? userAns.selected : 'No Answer'} ${isCorrect ? '✓' : '✗'}
                            </span>
                            ${!isCorrect ? `<span class="d-block text-muted">Correct answer: ${q.answer}</span>` : ''}
                            <small class="text-muted mt-1 d-block">${q.explanation}</small>
                        </div>
                    </div>
                `;
            });
            
            resultBox.innerHTML = `
                <div class="quiz-results-panel p-4">
                    <div class="text-center mb-4">
                        <h2 class="text-gradient">${rating}</h2>
                        <h4 class="mt-2">You scored <span class="text-primary">${State.quiz.score}</span> out of <span class="text-primary">${total}</span></h4>
                        <div class="progress mt-3 mx-auto" style="height: 12px; max-width: 300px;">
                            <div class="progress-bar bg-primary" role="progressbar" style="width: ${percentage}%"></div>
                        </div>
                        <span class="d-block mt-2 text-muted">${percentage}% Score | Time: ${Math.floor(timeSpent / 60)}m ${timeSpent % 60}s</span>
                    </div>
                    
                    <h5 class="border-bottom pb-2 mt-5">Question Review</h5>
                    <div class="quiz-review-list">
                        ${answersReviewHTML}
                    </div>
                </div>
            `;
            showToast('Quiz complete! Scorecard loaded.', 'success');
        } else {
            resultBox.innerHTML = `<div class="text-danger p-3">Failed to save quiz results.</div>`;
        }
    } catch (err) {
        resultBox.innerHTML = `<div class="text-danger p-3">Connection error during result submittal.</div>`;
    }
}

// 2. Roadmap UI Generator
function renderRoadmapInterface(roadmap, container) {
    container.innerHTML = '';
    
    let milestonesHTML = '';
    roadmap.milestones.forEach((milestone) => {
        let topicsList = '';
        milestone.topics.forEach(t => topicsList += `<li><i class="fas fa-circle-notch text-primary me-2 font-size-xs"></i>${t}</li>`);
        
        let resourcesList = '';
        milestone.resources.forEach(r => resourcesList += `<span class="badge bg-secondary me-2 mb-2 p-2">${r}</span>`);
        
        let projectsList = '';
        milestone.projects.forEach(p => projectsList += `<li><i class="fas fa-laptop-code text-secondary me-2"></i>${p}</li>`);
        
        milestonesHTML += `
            <div class="roadmap-milestone-card glass-card p-4 mb-4">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h4 class="m-0 text-gradient-purple">Week ${milestone.week}: ${milestone.title}</h4>
                    <span class="badge bg-primary p-2">Milestone ${milestone.week}</span>
                </div>
                
                <div class="row">
                    <div class="col-md-6 mb-3 mb-md-0">
                        <h6 class="fw-bold"><i class="fas fa-book-open me-2 text-primary"></i>Core Topics</h6>
                        <ul class="list-unstyled ps-2">
                            ${topicsList}
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6 class="fw-bold"><i class="fas fa-tools me-2 text-secondary"></i>Practical Projects</h6>
                        <ul class="list-unstyled ps-2">
                            ${projectsList}
                        </ul>
                    </div>
                </div>
                
                <div class="mt-3">
                    <h6 class="fw-bold"><i class="fas fa-graduation-cap me-2 text-info"></i>Suggested Resources</h6>
                    <div class="d-flex flex-wrap mt-2">
                        ${resourcesList}
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = `
        <div class="roadmap-wrapper">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h3 class="text-gradient">Roadmap: ${roadmap.topic}Mastery</h3>
                <button class="btn btn-premium btn-sm" onclick="saveAsNote(this, 'roadmap', \`${encodeURIComponent(JSON.stringify(roadmap))}\`)">
                    <i class="far fa-save me-1"></i> Save Roadmap
                </button>
            </div>
            
            <div class="roadmap-milestones">
                ${milestonesHTML}
            </div>
            
            <div class="alert glass mt-4 border-primary">
                <h6 class="fw-bold text-gradient"><i class="fas fa-lightbulb me-2"></i>EduGenie Tips</h6>
                <p class="m-0 text-muted small">${roadmap.additional_tips}</p>
            </div>
        </div>
    `;
}

// 3. Flashcards UI Generator
function setupFlashcardInterface(flashcards) {
    const resultBox = document.getElementById('flashcard-result');
    if (!resultBox) return;
    
    State.flashcards.cards = flashcards;
    State.flashcards.currentIndex = 0;
    
    renderFlashcard();
}

function renderFlashcard() {
    const resultBox = document.getElementById('flashcard-result');
    if (!resultBox) return;
    
    const card = State.flashcards.cards[State.flashcards.currentIndex];
    const total = State.flashcards.cards.length;
    
    resultBox.innerHTML = `
        <div class="flashcard-deck">
            <div class="flashcard-inner" id="activeFlashcard" onclick="flipFlashcard()">
                <div class="flashcard-front glass">
                    <span class="badge bg-secondary mb-3">Front (Question)</span>
                    <h3>${card.front}</h3>
                    <p class="text-muted mt-4 small"><i class="fas fa-sync me-1"></i> Click card to flip</p>
                </div>
                <div class="flashcard-back">
                    <span class="badge bg-light text-dark mb-3">Back (Answer)</span>
                    <h4>${card.back}</h4>
                    <p class="text-white-50 mt-4 small"><i class="fas fa-sync me-1"></i> Click card to flip</p>
                </div>
            </div>
        </div>
        
        <div class="d-flex justify-content-between align-items-center max-width-450 mx-auto">
            <button class="btn btn-premium-outline btn-sm" onclick="prevFlashcard()" ${State.flashcards.currentIndex === 0 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left me-1"></i> Prev
            </button>
            <span class="text-muted">Card ${State.flashcards.currentIndex + 1} of ${total}</span>
            <button class="btn btn-premium-outline btn-sm" onclick="nextFlashcard()" ${State.flashcards.currentIndex === total - 1 ? 'disabled' : ''}>
                Next <i class="fas fa-chevron-right ms-1"></i>
            </button>
        </div>
    `;
}

function flipFlashcard() {
    const fc = document.getElementById('activeFlashcard');
    if (fc) fc.classList.toggle('flipped');
}

function prevFlashcard() {
    if (State.flashcards.currentIndex > 0) {
        State.flashcards.currentIndex--;
        renderFlashcard();
    }
}

function nextFlashcard() {
    if (State.flashcards.currentIndex < State.flashcards.cards.length - 1) {
        State.flashcards.currentIndex++;
        renderFlashcard();
    }
}

// STORAGE DATA RETRIEVER (History, Notes, Bookmarks)
async function fetchHistory() {
    try {
        const res = await fetch('/api/db/history', {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            const data = await res.json();
            const container = document.getElementById('history-list');
            if (container) {
                if (data.length === 0) {
                    container.innerHTML = `<p class="text-muted p-3">No activity logs recorded.</p>`;
                    return;
                }
                
                let listHTML = '';
                data.forEach((log) => {
                    listHTML += `
                        <div class="border-bottom py-3 d-flex justify-content-between align-items-center">
                            <div>
                                <span class="badge bg-secondary mb-1">${log.module.toUpperCase()}</span>
                                <h6 class="m-0">${escapeHtml(log.prompt)}</h6>
                                <small class="text-muted">${new Date(log.created_at).toLocaleString()}</small>
                            </div>
                            <button class="btn btn-sm btn-premium-outline" onclick="loadHistoryDetail(\`${encodeURIComponent(log.response)}\`)">
                                View
                            </button>
                        </div>
                    `;
                });
                container.innerHTML = listHTML;
            }
        }
    } catch (err) {
        console.error(err);
    }
}

function loadHistoryDetail(encodedRes) {
    const rawRes = decodeURIComponent(encodedRes);
    alertModal("History Response Details", parseMarkdownToHTML(rawRes));
}

async function fetchNotes() {
    try {
        const res = await fetch('/api/db/notes', {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            const data = await res.json();
            const container = document.getElementById('notes-grid');
            if (container) {
                if (data.length === 0) {
                    container.innerHTML = `<div class="col-12"><p class="text-muted p-3">No saved notes yet.</p></div>`;
                    return;
                }
                
                let gridHTML = '';
                data.forEach((note) => {
                    gridHTML += `
                        <div class="col-md-6 mb-4" id="note-card-${note.id}">
                            <div class="glass-card p-4 h-100 d-flex flex-column justify-content-between">
                                <div>
                                    <h4 class="text-gradient">${escapeHtml(note.title)}</h4>
                                    <p class="text-muted text-truncate-3 mt-3">${escapeHtml(note.content)}</p>
                                </div>
                                <div class="d-flex justify-content-between align-items-center mt-4">
                                    <small class="text-muted">${new Date(note.created_at).toLocaleDateString()}</small>
                                    <div class="d-flex gap-2">
                                        <button class="btn btn-sm btn-premium" onclick="viewFullNote(\`${encodeURIComponent(note.title)}\`, \`${encodeURIComponent(note.content)}\`)">Read</button>
                                        <button class="btn btn-sm btn-outline-danger" onclick="deleteNote(${note.id})"><i class="far fa-trash-alt"></i></button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = gridHTML;
            }
        }
    } catch (err) {
        console.error(err);
    }
}

function viewFullNote(title, content) {
    alertModal(decodeURIComponent(title), parseMarkdownToHTML(decodeURIComponent(content)));
}

async function deleteNote(id) {
    if (!confirm("Are you sure you want to delete this note?")) return;
    try {
        const res = await fetch(`/api/db/notes/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            showToast('Note deleted.', 'warning');
            fetchNotes();
        }
    } catch (err) {
        showToast('Error deleting note.', 'danger');
    }
}

async function fetchBookmarks() {
    try {
        const res = await fetch('/api/db/bookmarks', {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            const data = await res.json();
            const container = document.getElementById('bookmarks-list');
            if (container) {
                if (data.length === 0) {
                    container.innerHTML = `<p class="text-muted p-3">No bookmarks saved.</p>`;
                    return;
                }
                
                let listHTML = '';
                data.forEach((bookmark) => {
                    listHTML += `
                        <div class="border-bottom py-3 d-flex justify-content-between align-items-center" id="bookmark-row-${bookmark.id}">
                            <div>
                                <span class="badge bg-primary mb-1">${bookmark.target_type.toUpperCase()}</span>
                                <h6 class="m-0">${escapeHtml(bookmark.title)}</h6>
                                <p class="text-muted small m-0 text-truncate-1">${escapeHtml(bookmark.details)}</p>
                            </div>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteBookmark(${bookmark.id})">
                                Remove
                            </button>
                        </div>
                    `;
                });
                container.innerHTML = listHTML;
            }
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteBookmark(id) {
    try {
        const res = await fetch(`/api/db/bookmarks/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            showToast('Bookmark removed.', 'warning');
            fetchBookmarks();
        }
    } catch (err) {
        showToast('Error removing bookmark.', 'danger');
    }
}

// PROFILE & SETTINGS WRITERS
async function updateProfileDetails(e) {
    e.preventDefault();
    const education = document.getElementById('profileEducation').value;
    const skills = document.getElementById('profileSkills').value;
    const achievements = document.getElementById('profileAchievements').value;
    
    toggleButtonLoading('profileSaveBtn', true);
    try {
        const res = await fetch('/api/auth/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({ education, skills, achievements })
        });
        const data = await res.json();
        if (res.ok) {
            State.user = data;
            showToast('Profile updated!', 'success');
            updateDashboardUIElements();
        } else {
            showToast('Error updating profile.', 'danger');
        }
    } catch (err) {
        showToast('Profile save network failure.', 'danger');
    } finally {
        toggleButtonLoading('profileSaveBtn', false);
    }
}

async function saveSettings(e) {
    e.preventDefault();
    const model = document.getElementById('settingsModel').value;
    const temperature = parseFloat(document.getElementById('settingsTemp').value);
    const max_tokens = parseInt(document.getElementById('settingsTokens').value);
    
    toggleButtonLoading('settingsSaveBtn', true);
    try {
        const res = await fetch('/api/db/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({
                selected_model: model,
                temperature: temperature,
                max_tokens: max_tokens
            })
        });
        const data = await res.json();
        if (res.ok) {
            State.settings = data;
            const statusBadge = document.getElementById('ollamaStatusBadge');
            if (statusBadge) {
                statusBadge.innerHTML = `<i class="fas fa-check-circle me-1"></i>Ollama: ${data.selected_model || model}`;
            }
            showToast('AI Settings updated!', 'success');
        } else {
            showToast('Failed to save settings.', 'danger');
        }
    } catch (err) {
        showToast('Settings connection error.', 'danger');
    } finally {
        toggleButtonLoading('settingsSaveBtn', false);
    }
}

// SYSTEM THEME MANAGEMENT
function applyTheme(theme) {
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    State.settings.theme = theme;
    
    const toggleIcon = document.getElementById('theme-toggle-icon');
    if (toggleIcon) {
        if (theme === 'light') {
            toggleIcon.className = 'fas fa-moon';
        } else {
            toggleIcon.className = 'fas fa-sun';
        }
    }
}

function toggleTheme() {
    const activeTheme = State.settings.theme === 'dark' ? 'light' : 'dark';
    applyTheme(activeTheme);
    
    // Save theme setting to DB asynchronously
    fetch('/api/db/settings', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${State.token}`
        },
        body: JSON.stringify({ theme: activeTheme })
    });
}

// GLOBAL SEARCH (Dashboard Header)
function handleGlobalSearch(query) {
    const q = query.trim().toLowerCase();
    if (!q) {
        // Reload dashboard module normally
        switchModule(State.currentModule);
        return;
    }
    
    // Quick filtering bookmarks/notes on current client caches
    // Show results overlay
    const targetView = document.getElementById(`${State.currentModule}-module`);
    if (targetView) {
        // If not in search view, append a temporary results panel
        showToast(`Searching for "${query}"...`, 'success');
    }
}

// ADMIN PANEL ANALYTICS & LOGS
async function loadAdminAnalytics() {
    try {
        const res = await fetch('/api/admin/analytics', {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        
        // Render stats counters
        document.getElementById('adminTotalUsers').innerText = data.summary.total_users;
        document.getElementById('adminTotalFeedback').innerText = data.summary.total_feedback;
        document.getElementById('adminTotalQueries').innerText = data.summary.total_chats;
        document.getElementById('adminTotalQuizzes').innerText = data.summary.total_quizzes;
        
        // Render tables
        const logsContainer = document.getElementById('admin-prompt-logs');
        if (logsContainer) {
            let logsHTML = '';
            data.recent_logs.forEach((log) => {
                logsHTML += `
                    <tr>
                        <td>${log.id}</td>
                        <td>${escapeHtml(log.user_email)}</td>
                        <td><span class="badge bg-secondary">${log.module.toUpperCase()}</span></td>
                        <td>${escapeHtml(log.prompt)}</td>
                        <td>${new Date(log.timestamp).toLocaleTimeString()}</td>
                    </tr>
                `;
            });
            logsContainer.innerHTML = logsHTML;
        }
        
        // Load User details
        loadAdminUsersTable();
        // Load Feedback messages
        loadAdminFeedbackTable();
        
        // Render Charts using Chart.js
        renderAnalyticsCharts(data.charts);
    } catch (err) {
        console.error("Admin analytics failure", err);
    }
}

async function loadAdminUsersTable() {
    try {
        const res = await fetch('/api/admin/users', {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            const users = await res.json();
            const container = document.getElementById('admin-users-table');
            if (container) {
                let html = '';
                users.forEach((u) => {
                    html += `
                        <tr>
                            <td>${u.id}</td>
                            <td>${escapeHtml(u.name)}</td>
                            <td>${escapeHtml(u.email)}</td>
                            <td><span class="badge bg-primary">${u.role.toUpperCase()}</span></td>
                            <td>${u.streak} Days</td>
                            <td>${new Date(u.created_at).toLocaleDateString()}</td>
                        </tr>
                    `;
                });
                container.innerHTML = html;
            }
        }
    } catch(err) { console.error(err); }
}

async function loadAdminFeedbackTable() {
    try {
        const res = await fetch('/api/admin/feedback', {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            const list = await res.json();
            const container = document.getElementById('admin-feedback-table');
            if (container) {
                let html = '';
                list.forEach((f) => {
                    html += `
                        <tr>
                            <td>${f.id}</td>
                            <td>${escapeHtml(f.name)}</td>
                            <td>${escapeHtml(f.email)}</td>
                            <td>${escapeHtml(f.message)}</td>
                            <td>${new Date(f.created_at).toLocaleDateString()}</td>
                        </tr>
                    `;
                });
                container.innerHTML = html;
            }
        }
    } catch(err) { console.error(err); }
}

let userGrowthChartInstance = null;
let moduleCountChartInstance = null;

function renderAnalyticsCharts(chartData) {
    if (typeof Chart === 'undefined') return;
    
    // User growth chart setup
    const ctx1 = document.getElementById('userGrowthChart');
    if (ctx1) {
        if (userGrowthChartInstance) userGrowthChartInstance.destroy();
        userGrowthChartInstance = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: chartData.growth_labels,
                datasets: [{
                    label: 'New Registrations',
                    data: chartData.growth_data,
                    borderColor: '#6C63FF',
                    backgroundColor: 'rgba(108, 99, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
    
    // Module usage chart setup
    const ctx2 = document.getElementById('moduleUsageChart');
    if (ctx2) {
        if (moduleCountChartInstance) moduleCountChartInstance.destroy();
        const counts = chartData.module_counts;
        moduleCountChartInstance = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: Object.keys(counts).map(k => k.toUpperCase()),
                datasets: [{
                    label: 'Invocations',
                    data: Object.values(counts),
                    backgroundColor: ['#6C63FF', '#00D4FF', '#7B2FF7', '#FFD600', '#00E676', '#FF1744', '#FF9100'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
}

// OVERVIEW TAB ANALYTICS (User Dashboard main page)
async function updateOverviewAnalytics() {
    try {
        const res = await fetch('/api/db/history', {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            const data = await res.json();
            
            // Total tasks, streaks, recently asked question
            const totalTasksEl = document.getElementById('overviewTotalTasks');
            if (totalTasksEl) totalTasksEl.innerText = data.length + " AI Tasks";
            
            const recentPromptEl = document.getElementById('overviewRecentPrompt');
            if (recentPromptEl) {
                if (data.length > 0) {
                    recentPromptEl.innerText = `"${data[0].prompt.substring(0, 45)}..."`;
                } else {
                    recentPromptEl.innerText = "No queries yet.";
                }
            }
        }
    } catch(err) {
        console.error(err);
    }
}

// LOGOUT LOGIC
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch (err) {}
    localStorage.removeItem('token');
    window.location.href = '/';
}

// PUBLIC CONTACT FORM HANDLER
async function submitContactForm(e) {
    e.preventDefault();
    const name = document.getElementById('contactName').value;
    const email = document.getElementById('contactEmail').value;
    const message = document.getElementById('contactMessage').value;
    
    toggleButtonLoading('contactSubmitBtn', true);
    try {
        const res = await fetch('/api/db/feedback', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, email, message })
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Feedback submitted successfully!', 'success');
            document.getElementById('contactForm').reset();
        } else {
            showToast('Error: ' + data.detail, 'danger');
        }
    } catch (err) {
        showToast('Error connecting to feedback service.', 'danger');
    } finally {
        toggleButtonLoading('contactSubmitBtn', false);
    }
}

// GENERAL UI HELPERS
function showToast(message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `custom-toast ${type}`;
    
    let icon = '<i class="fas fa-check-circle text-success"></i>';
    if (type === 'danger') icon = '<i class="fas fa-times-circle text-danger"></i>';
    if (type === 'warning') icon = '<i class="fas fa-exclamation-triangle text-warning"></i>';
    
    toast.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            ${icon}
            <span>${message}</span>
        </div>
        <button class="btn-close btn-close-white" onclick="this.parentElement.remove()"></button>
    `;
    
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

function alertModal(title, htmlContent) {
    // Generate simple modular alert overlay
    let modal = document.getElementById('customAlertModal');
    if (modal) modal.remove();
    
    modal = document.createElement('div');
    modal.id = 'customAlertModal';
    modal.className = 'modal fade show';
    modal.style.display = 'block';
    modal.style.background = 'rgba(0,0,0,0.7)';
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered modal-lg">
            <div class="modal-content glass">
                <div class="modal-header border-0">
                    <h5 class="modal-title text-gradient fw-bold">${title}</h5>
                    <button type="button" class="btn-close btn-close-white" onclick="document.getElementById('customAlertModal').remove()"></button>
                </div>
                <div class="modal-body max-height-500 overflow-y-auto markdown-body">
                    ${htmlContent}
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-premium-outline btn-sm" onclick="document.getElementById('customAlertModal').remove()">Close</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function toggleButtonLoading(btnId, isLoading) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    if (isLoading) {
        btn.setAttribute('disabled', 'true');
        btn.dataset.originalHTML = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Loading...';
    } else {
        btn.removeAttribute('disabled');
        if (btn.dataset.originalHTML) {
            btn.innerHTML = btn.dataset.originalHTML;
        }
    }
}

function escapeHtml(text) {
    if (!text) return '';
    return text
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// SLIDER INTERACTIVES
const tempSlider = document.getElementById('settingsTemp');
if (tempSlider) {
    tempSlider.addEventListener('input', (e) => {
        const val = document.getElementById('settingsTempVal');
        if (val) val.innerText = e.target.value;
    });
}

// ==========================================================
// DOCUMENT & PDF AI STUDY CENTER CONTROLLER
// ==========================================================

function setupDocumentDropzone() {
    const dropZone = document.getElementById('docDropZone');
    if (!dropZone) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            const uploadBox = dropZone.querySelector('.doc-upload-box');
            if (uploadBox) uploadBox.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            const uploadBox = dropZone.querySelector('.doc-upload-box');
            if (uploadBox) uploadBox.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            uploadDocumentFile(files[0]);
        }
    }, false);
}

function handleFileSelected(event) {
    const file = event.target.files[0];
    if (file) {
        uploadDocumentFile(file);
    }
    event.target.value = '';
}

async function uploadDocumentFile(file) {
    const allowed = ['pdf', 'docx', 'doc', 'txt', 'md'];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
        showToast('Please upload a PDF, DOCX, TXT, or MD document.', 'warning');
        return;
    }

    if (file.size > 15 * 1024 * 1024) {
        showToast('File exceeds 15MB limit.', 'warning');
        return;
    }

    const progress = document.getElementById('docUploadProgress');
    if (progress) progress.style.display = 'block';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/documents/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${State.token}`
            },
            body: formData
        });

        const data = await res.json();
        if (res.ok) {
            showToast(`Document "${data.filename}" processed successfully!`, 'success');
            await loadUserDocuments();
            selectDocument(data.id);
        } else {
            showToast(data.detail || 'Upload failed.', 'danger');
        }
    } catch (err) {
        console.error(err);
        showToast('Network error while uploading document.', 'danger');
    } finally {
        if (progress) progress.style.display = 'none';
    }
}

async function loadUserDocuments() {
    try {
        const res = await fetch('/api/documents', {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            State.documents = await res.json();
            renderDocumentList(State.documents);
            if (!State.currentDoc && State.documents.length > 0) {
                selectDocument(State.documents[0].id);
            } else if (!State.currentDoc && State.documents.length === 0) {
                resetDocWorkspace();
            }
        }
    } catch (err) {
        console.error('Failed to load documents:', err);
    }
}

function renderDocumentList(docs) {
    const container = document.getElementById('documentListContainer');
    const badge = document.getElementById('docCountBadge');
    if (!container) return;

    if (badge) badge.innerText = docs.length;

    if (!docs || docs.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted small">
                <i class="fas fa-file-alt fa-2x mb-2 opacity-50"></i>
                <p>No documents uploaded yet.<br>Drag & drop a study file above to begin!</p>
            </div>
        `;
        return;
    }

    let html = '';
    docs.forEach(doc => {
        const isActive = State.currentDoc && State.currentDoc.id === doc.id;
        const sizeFormatted = doc.file_size > 1024 * 1024 
            ? `${(doc.file_size / (1024 * 1024)).toFixed(1)} MB` 
            : `${Math.round(doc.file_size / 1024)} KB`;

        let iconClass = 'fa-file-alt text-warning';
        let iconBg = 'rgba(255, 214, 0, 0.1)';
        if (doc.file_type === 'pdf') {
            iconClass = 'fa-file-pdf text-danger';
            iconBg = 'rgba(255, 23, 68, 0.1)';
        } else if (['docx', 'doc'].includes(doc.file_type)) {
            iconClass = 'fa-file-word text-info';
            iconBg = 'rgba(0, 212, 255, 0.1)';
        }

        html += `
            <div class="doc-list-item ${isActive ? 'active' : ''}" onclick="selectDocument(${doc.id})">
                <div class="d-flex align-items-center gap-2 overflow-hidden">
                    <div class="doc-icon" style="background: ${iconBg};">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <div class="overflow-hidden">
                        <div class="fw-semibold text-truncate small text-white" style="max-width: 170px;" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</div>
                        <div class="text-muted" style="font-size: 0.72rem;">${sizeFormatted} • ${doc.char_count} chars</div>
                    </div>
                </div>
                <button class="btn btn-sm btn-link text-muted p-1 hover-danger" onclick="event.stopPropagation(); deleteDocumentDirect(${doc.id}, '${encodeURIComponent(doc.filename)}')" title="Delete">
                    <i class="fas fa-trash-alt font-size-xs"></i>
                </button>
            </div>
        `;
    });

    container.innerHTML = html;
}

function filterDocumentList() {
    const q = (document.getElementById('docSearchInput')?.value || '').toLowerCase();
    const filtered = State.documents.filter(d => d.filename.toLowerCase().includes(q));
    renderDocumentList(filtered);
}

async function selectDocument(docId) {
    try {
        const res = await fetch(`/api/documents/${docId}`, {
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (!res.ok) {
            showToast('Could not load document.', 'danger');
            return;
        }

        const doc = await res.json();
        State.currentDoc = doc;

        // Render in UI
        const activeWorkspace = document.getElementById('docActiveWorkspace');
        if (activeWorkspace) activeWorkspace.style.display = 'flex';
        const delBtn = document.getElementById('activeDocDeleteBtn');
        if (delBtn) delBtn.style.display = 'inline-block';

        // Set metadata
        const titleEl = document.getElementById('activeDocTitle');
        const badgeEl = document.getElementById('activeDocBadge');
        const metaEl = document.getElementById('activeDocMeta');
        if (titleEl) titleEl.innerText = doc.filename;
        if (badgeEl) badgeEl.innerText = doc.file_type.toUpperCase();
        
        const sizeFormatted = doc.file_size > 1024 * 1024 
            ? `${(doc.file_size / (1024 * 1024)).toFixed(1)} MB` 
            : `${Math.round(doc.file_size / 1024)} KB`;
        if (metaEl) metaEl.innerText = `${sizeFormatted} • ${doc.char_count} Characters • Ready for AI Analysis`;

        // Populate Reader
        const textContainer = document.getElementById('docExtractedTextContainer');
        if (textContainer) textContainer.innerText = doc.extracted_text;

        // Populate Cached Summary if exists
        const summaryBox = document.getElementById('docSummaryResult');
        if (summaryBox) {
            if (doc.summary) {
                summaryBox.innerHTML = `
                    <div class="streaming-wrapper">
                        <div class="d-flex justify-content-end gap-2 mb-3">
                            <button class="btn btn-sm btn-outline-secondary" onclick="copyResultText(this, \`${encodeURIComponent(doc.summary)}\`)">
                                <i class="far fa-copy me-1"></i> Copy
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" onclick="saveAsNote(this, 'Document Summary (${escapeHtml(doc.filename)})', \`${encodeURIComponent(doc.summary)}\`)">
                                <i class="far fa-sticky-note me-1"></i> Save Note
                            </button>
                        </div>
                        <div class="content-body markdown-body">${parseMarkdownToHTML(doc.summary)}</div>
                    </div>
                `;
            } else {
                summaryBox.innerHTML = '<div class="text-muted p-3">Click "Generate AI Summary" above to create an in-depth breakdown of this document.</div>';
            }
        }

        // Reset Q&A Container
        const qaContainer = document.getElementById('docQAChatContainer');
        if (qaContainer) {
            qaContainer.innerHTML = `
                <div class="message-bubble assistant">
                    <div class="message-avatar">EG</div>
                    <div class="message-content">I'm ready! Ask any questions about "<strong>${escapeHtml(doc.filename)}</strong>" and I will answer with direct references to this text.</div>
                </div>
            `;
        }

        // Reset Quiz and Flashcards Containers
        const quizBox = document.getElementById('docQuizContainer');
        if (quizBox) quizBox.innerHTML = '<div class="text-muted p-3">Click "Generate Quiz" to test your comprehension on this document.</div>';

        const flashBox = document.getElementById('docFlashcardsContainer');
        if (flashBox) flashBox.innerHTML = '<div class="text-muted p-3">Click "Generate Flashcards" to create interactive study cards.</div>';

        // Default to reader tab
        switchDocTab('reader');
        renderDocumentList(State.documents);
    } catch (err) {
        console.error('Failed to select document:', err);
    }
}

async function deleteDocumentDirect(docId, encodedName) {
    const filename = decodeURIComponent(encodedName);
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

    try {
        const res = await fetch(`/api/documents/${docId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${State.token}` }
        });
        if (res.ok) {
            showToast('Document deleted.', 'success');
            if (State.currentDoc && State.currentDoc.id === docId) {
                State.currentDoc = null;
                resetDocWorkspace();
            }
            await loadUserDocuments();
        } else {
            showToast('Failed to delete document.', 'danger');
        }
    } catch (err) {
        showToast('Network error while deleting.', 'danger');
    }
}

function deleteActiveDocument() {
    if (!State.currentDoc) return;
    deleteDocumentDirect(State.currentDoc.id, encodeURIComponent(State.currentDoc.filename));
}

function resetDocWorkspace() {
    const titleEl = document.getElementById('activeDocTitle');
    const badgeEl = document.getElementById('activeDocBadge');
    const metaEl = document.getElementById('activeDocMeta');
    const delBtn = document.getElementById('activeDocDeleteBtn');
    const textContainer = document.getElementById('docExtractedTextContainer');
    const summaryBox = document.getElementById('docSummaryResult');
    const qaHistory = document.getElementById('docQAMessages');
    const quizArea = document.getElementById('docQuizQuestionsArea');
    const flashcardArea = document.getElementById('docFlashcardsArea');

    if (titleEl) titleEl.innerText = 'Document Analysis Workspace';
    if (badgeEl) badgeEl.innerText = 'Ready';
    if (metaEl) metaEl.innerText = 'Select a document from library to analyze';
    if (delBtn) delBtn.style.display = 'none';
    if (textContainer) textContainer.innerText = 'Select an uploaded file from the library on the left, or upload a new study file above to view extracted text and run AI actions.';
    if (summaryBox) summaryBox.innerHTML = '<div class="text-muted p-3">Select a document from the library to generate an AI summary.</div>';
    if (qaHistory) qaHistory.innerHTML = '<div class="text-center py-4 text-muted small"><i class="fas fa-comments fa-2x mb-2 opacity-50"></i><p>Select a document to ask specific questions.</p></div>';
    if (quizArea) quizArea.innerHTML = '<div class="text-muted p-3">Select a document to generate a comprehension quiz.</div>';
    if (flashcardArea) flashcardArea.innerHTML = '<div class="text-muted p-3">Select a document to generate interactive flashcards.</div>';
}

function switchDocTab(tabName) {
    const tabMap = {
        'reader': { pane: 'docPaneReader', tab: 'tabDocReader' },
        'summary': { pane: 'docPaneSummary', tab: 'tabDocSummary' },
        'qa': { pane: 'docPaneQA', tab: 'tabDocQA' },
        'quiz': { pane: 'docPaneQuiz', tab: 'tabDocQuiz' },
        'flashcards': { pane: 'docPaneFlashcards', tab: 'tabDocFlashcards' }
    };
    Object.keys(tabMap).forEach(key => {
        const item = tabMap[key];
        const paneEl = document.getElementById(item.pane);
        const tabBtn = document.getElementById(item.tab);
        if (paneEl) paneEl.style.display = (key === tabName) ? 'block' : 'none';
        if (tabBtn) {
            if (key === tabName) tabBtn.classList.add('active');
            else tabBtn.classList.remove('active');
        }
    });
}

function copyExtractedText() {
    if (!State.currentDoc) return;
    navigator.clipboard.writeText(State.currentDoc.extracted_text)
        .then(() => showToast('Full extracted text copied to clipboard!', 'success'))
        .catch(() => showToast('Failed to copy text.', 'danger'));
}

async function generateDocSummary() {
    if (!State.currentDoc) return;
    const summaryType = document.getElementById('docSummaryType')?.value || 'Comprehensive';
    const resultBox = document.getElementById('docSummaryResult');
    const loader = document.getElementById('loader-doc-summary');

    if (loader) loader.style.display = 'block';
    resultBox.innerHTML = `
        <div class="p-3">
            <div class="d-flex align-items-center text-primary mb-3">
                <span class="spinner-border spinner-border-sm me-2"></span>
                <span>Generating high-yield academic summary...</span>
            </div>
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text" style="width:75%"></div>
        </div>
    `;

    try {
        const streamRes = await fetch(`/api/documents/${State.currentDoc.id}/stream-summarize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({ summary_type: summaryType })
        });

        if (streamRes.ok && streamRes.body) {
            const reader = streamRes.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let fullText = '';
            let firstChunk = true;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunkStr = decoder.decode(value, { stream: true });
                const lines = chunkStr.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const payload = JSON.parse(line.slice(6));
                            if (payload.chunk) {
                                if (firstChunk) {
                                    resultBox.innerHTML = '';
                                    firstChunk = false;
                                }
                                fullText += payload.chunk;
                                resultBox.innerHTML = `
                                    <div class="streaming-wrapper">
                                        <div class="d-flex justify-content-end gap-2 mb-3">
                                            <button class="btn btn-sm btn-outline-secondary" onclick="copyResultText(this, \`${encodeURIComponent(fullText)}\`)">
                                                <i class="far fa-copy me-1"></i> Copy
                                            </button>
                                            <button class="btn btn-sm btn-outline-secondary" onclick="saveAsNote(this, 'Document Summary (${escapeHtml(State.currentDoc.filename)})', \`${encodeURIComponent(fullText)}\`)">
                                                <i class="far fa-sticky-note me-1"></i> Save Note
                                            </button>
                                        </div>
                                        <div class="content-body markdown-body">${parseMarkdownToHTML(fullText)}</div>
                                    </div>
                                `;
                            }
                        } catch (e) {}
                    }
                }
            }
            if (fullText) {
                State.currentDoc.summary = fullText;
                fetchHistory();
                if (loader) loader.style.display = 'none';
                return;
            }
        }
    } catch (streamErr) {
        console.warn('Stream doc summary fallback:', streamErr);
    }

    try {
        const res = await fetch(`/api/documents/${State.currentDoc.id}/summarize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({ summary_type: summaryType })
        });

        const data = await res.json();
        if (res.ok) {
            State.currentDoc.summary = data.data;
            resultBox.innerHTML = `
                <div class="streaming-wrapper">
                    <div class="d-flex justify-content-end gap-2 mb-3">
                        <button class="btn btn-sm btn-outline-secondary" onclick="copyResultText(this, \`${encodeURIComponent(data.data)}\`)">
                            <i class="far fa-copy me-1"></i> Copy
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="saveAsNote(this, 'Document Summary (${escapeHtml(State.currentDoc.filename)})', \`${encodeURIComponent(data.data)}\`)">
                            <i class="far fa-sticky-note me-1"></i> Save Note
                        </button>
                    </div>
                    <div class="content-body markdown-body">${parseMarkdownToHTML(data.data)}</div>
                </div>
            `;
            fetchHistory();
        } else {
            resultBox.innerHTML = `<div class="text-danger p-3">${data.detail || 'Summary generation failed.'}</div>`;
        }
    } catch (err) {
        resultBox.innerHTML = `<div class="text-danger p-3">Network error generating summary.</div>`;
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

function setDocPrompt(text) {
    const input = document.getElementById('docQAPrompt');
    if (input) {
        input.value = text;
        input.focus();
    }
}

async function askDocQuestion() {
    if (!State.currentDoc) return;
    const input = document.getElementById('docQAPrompt');
    if (!input) return;
    const question = input.value.trim();
    if (!question) {
        showToast('Please type a question about this document.', 'warning');
        return;
    }

    input.value = '';
    const chatContainer = document.getElementById('docQAChatContainer');
    const loader = document.getElementById('loader-doc-qa');

    // Append user question
    const userBubble = document.createElement('div');
    userBubble.className = 'message-bubble user';
    userBubble.innerHTML = `
        <div class="message-content">${escapeHtml(question)}</div>
        <div class="message-avatar">${State.user?.name ? State.user.name.slice(0, 2).toUpperCase() : 'ME'}</div>
    `;
    chatContainer.appendChild(userBubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if (loader) loader.style.display = 'block';

    const aiBubble = document.createElement('div');
    aiBubble.className = 'message-bubble assistant';
    aiBubble.innerHTML = `
        <div class="message-avatar">EG</div>
        <div class="message-content markdown-body" style="font-size: 0.92rem;">
            <div class="d-flex align-items-center text-info small">
                <span class="spinner-grow spinner-grow-sm text-primary me-2"></span>
                <span><i class="fas fa-bolt text-warning me-1"></i><strong>Dense Vector RAG</strong> — Searching 384-D embedding matrix...</span>
            </div>
        </div>
    `;
    chatContainer.appendChild(aiBubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    const contentDiv = aiBubble.querySelector('.message-content');

    try {
        const streamRes = await fetch(`/api/documents/${State.currentDoc.id}/stream-qa`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({ question: question })
        });

        if (streamRes.ok && streamRes.body) {
            const reader = streamRes.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let fullText = '';
            let firstChunk = true;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunkStr = decoder.decode(value, { stream: true });
                const lines = chunkStr.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const payload = JSON.parse(line.slice(6));
                            if (payload.chunk) {
                                if (firstChunk) {
                                    contentDiv.innerHTML = '';
                                    firstChunk = false;
                                }
                                fullText += payload.chunk;
                                contentDiv.innerHTML = parseMarkdownToHTML(fullText);
                                chatContainer.scrollTop = chatContainer.scrollHeight;
                            }
                        } catch (e) {}
                    }
                }
            }
            if (fullText) {
                if (loader) loader.style.display = 'none';
                fetchHistory();
                return;
            }
        }
    } catch (streamErr) {
        console.warn('Stream doc QA fallback:', streamErr);
    }

    try {
        const res = await fetch(`/api/documents/${State.currentDoc.id}/qa`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({ question: question })
        });

        const data = await res.json();
        if (res.ok) {
            contentDiv.innerHTML = parseMarkdownToHTML(data.data);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            fetchHistory();
        } else {
            showToast(data.detail || 'Failed to get answer.', 'danger');
        }
    } catch (err) {
        showToast('Network error contacting AI.', 'danger');
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

async function generateDocQuiz() {
    if (!State.currentDoc) return;
    const difficulty = document.getElementById('docQuizDifficulty')?.value || 'Medium';
    const count = parseInt(document.getElementById('docQuizCount')?.value || '5');
    const container = document.getElementById('docQuizContainer');
    const loader = document.getElementById('loader-doc-quiz');

    if (loader) loader.style.display = 'block';
    container.innerHTML = `
        <div class="p-3">
            <div class="d-flex align-items-center text-primary mb-3">
                <span class="spinner-border spinner-border-sm me-2"></span>
                <span>Synthesizing ${count} ${difficulty} comprehension questions...</span>
            </div>
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text"></div>
        </div>
    `;

    try {
        const res = await fetch(`/api/documents/${State.currentDoc.id}/quiz`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({ difficulty: difficulty, num_questions: count })
        });

        const data = await res.json();
        if (res.ok && data.questions && data.questions.length > 0) {
            State.docQuiz.questions = data.questions;
            State.docQuiz.currentIndex = 0;
            State.docQuiz.score = 0;
            State.docQuiz.userAnswers = [];
            renderDocQuizQuestion();
        } else {
            container.innerHTML = `<div class="text-danger p-3">${data.detail || 'Could not generate quiz from this document.'}</div>`;
        }
    } catch (err) {
        container.innerHTML = `<div class="text-danger p-3">Network error generating quiz.</div>`;
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

function renderDocQuizQuestion() {
    const container = document.getElementById('docQuizContainer');
    if (!container || !State.docQuiz.questions.length) return;

    const q = State.docQuiz.questions[State.docQuiz.currentIndex];
    const total = State.docQuiz.questions.length;

    let optionsHTML = '';
    q.options.forEach((opt, idx) => {
        const safeOpt = escapeHtml(opt);
        optionsHTML += `
            <div class="quiz-option p-3 mb-2 rounded-3" style="cursor: pointer; border: 1px solid var(--glass-border); transition: all 0.2s ease;" onclick="handleDocQuizAnswer('${safeOpt.replace(/'/g, "\\'")}', this)">
                <div class="d-flex align-items-center">
                    <span class="badge bg-secondary me-3" style="width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;">${String.fromCharCode(65 + idx)}</span>
                    <span class="quiz-option-text fw-medium">${safeOpt}</span>
                </div>
            </div>
        `;
    });

    container.innerHTML = `
        <div class="quiz-runner p-2">
            <div class="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom border-secondary">
                <span class="text-primary fw-bold">Question ${State.docQuiz.currentIndex + 1} of ${total}</span>
                <span class="badge bg-info">${escapeHtml(State.currentDoc.filename)}</span>
            </div>
            <h5 class="fw-semibold quiz-question-title mb-4">${escapeHtml(q.question)}</h5>
            <div class="options-group mb-3">
                ${optionsHTML}
            </div>
            <div id="docQuizFeedback" style="display: none;" class="p-3 rounded-3 mt-3"></div>
            <div class="d-flex justify-content-end mt-3">
                <button id="docQuizNextBtn" class="btn btn-premium btn-sm" style="display: none;" onclick="nextDocQuizQuestion()">
                    ${State.docQuiz.currentIndex === total - 1 ? 'Finish Quiz' : 'Next Question <i class="fas fa-arrow-right ms-1"></i>'}
                </button>
            </div>
        </div>
    `;
}

function handleDocQuizAnswer(chosenAnswer, element) {
    const q = State.docQuiz.questions[State.docQuiz.currentIndex];
    const isCorrect = chosenAnswer === q.answer;
    
    // Disable all options
    document.querySelectorAll('.quiz-option').forEach(el => {
        el.style.pointerEvents = 'none';
    });

    if (isCorrect) {
        element.style.background = 'rgba(0, 230, 118, 0.2)';
        element.style.borderColor = 'var(--success)';
        State.docQuiz.score++;
    } else {
        element.style.background = 'rgba(255, 23, 68, 0.2)';
        element.style.borderColor = 'var(--danger)';
    }

    const feedback = document.getElementById('docQuizFeedback');
    if (feedback) {
        feedback.style.display = 'block';
        feedback.style.background = isCorrect ? 'rgba(0, 230, 118, 0.1)' : 'rgba(255, 23, 68, 0.1)';
        feedback.style.border = `1px solid ${isCorrect ? 'var(--success)' : 'var(--danger)'}`;
        feedback.innerHTML = `
            <div class="fw-bold mb-1 ${isCorrect ? 'text-success' : 'text-danger'}">
                <i class="fas ${isCorrect ? 'fa-check-circle' : 'fa-times-circle'} me-1"></i>
                ${isCorrect ? 'Correct!' : 'Incorrect'}
            </div>
            <div class="small quiz-feedback-text">${escapeHtml(q.explanation || 'Answer based on document text.')}</div>
        `;
    }

    const nextBtn = document.getElementById('docQuizNextBtn');
    if (nextBtn) nextBtn.style.display = 'inline-block';
}

function nextDocQuizQuestion() {
    State.docQuiz.currentIndex++;
    if (State.docQuiz.currentIndex < State.docQuiz.questions.length) {
        renderDocQuizQuestion();
    } else {
        // Show Scorecard
        const container = document.getElementById('docQuizContainer');
        const total = State.docQuiz.questions.length;
        const pct = Math.round((State.docQuiz.score / total) * 100);
        container.innerHTML = `
            <div class="text-center p-4">
                <div class="rounded-circle bg-primary bg-opacity-20 mx-auto mb-3 d-flex align-items-center justify-content-center" style="width: 80px; height: 80px;">
                    <i class="fas fa-trophy fa-2x text-warning"></i>
                </div>
                <h3 class="fw-bold text-gradient">Quiz Completed!</h3>
                <h4 class="mt-2 quiz-question-title">Score: <span class="text-primary">${State.docQuiz.score}</span> / ${total} (${pct}%)</h4>
                <p class="text-muted small mt-2">Tested on "${escapeHtml(State.currentDoc.filename)}"</p>
                <button class="btn btn-premium btn-sm mt-3" onclick="generateDocQuiz()">
                    <i class="fas fa-redo me-1"></i> Retake / New Quiz
                </button>
            </div>
        `;
    }
}

async function generateDocFlashcards() {
    if (!State.currentDoc) return;
    const container = document.getElementById('docFlashcardsContainer');
    const loader = document.getElementById('loader-doc-flashcards');

    if (loader) loader.style.display = 'block';
    container.innerHTML = `
        <div class="p-3">
            <div class="d-flex align-items-center text-primary mb-3 justify-content-center">
                <span class="spinner-border spinner-border-sm me-2"></span>
                <span>Synthesizing high-yield study flashcards...</span>
            </div>
            <div class="skeleton skeleton-title mx-auto" style="max-width: 300px;"></div>
            <div class="skeleton skeleton-text mx-auto" style="max-width: 400px;"></div>
        </div>
    `;

    try {
        const res = await fetch(`/api/documents/${State.currentDoc.id}/flashcards`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${State.token}`
            },
            body: JSON.stringify({ num_cards: 5 })
        });

        const data = await res.json();
        if (res.ok && data.flashcards && data.flashcards.length > 0) {
            State.docFlashcards.cards = data.flashcards;
            State.docFlashcards.currentIndex = 0;
            renderDocFlashcard();
        } else {
            container.innerHTML = `<div class="text-danger p-3">${data.detail || 'Could not generate flashcards.'}</div>`;
        }
    } catch (err) {
        container.innerHTML = `<div class="text-danger p-3">Network error generating flashcards.</div>`;
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

function renderDocFlashcard() {
    const container = document.getElementById('docFlashcardsContainer');
    if (!container || !State.docFlashcards.cards.length) return;

    const card = State.docFlashcards.cards[State.docFlashcards.currentIndex];
    const total = State.docFlashcards.cards.length;

    container.innerHTML = `
        <div class="flip-card-container mb-3" onclick="this.classList.toggle('flipped')">
            <div class="flip-card-inner">
                <div class="flip-card-front glass">
                    <span class="badge bg-secondary mb-3"><i class="fas fa-question-circle me-1"></i> Front / Question</span>
                    <h5 class="fw-bold flashcard-front-title">${escapeHtml(card.front)}</h5>
                    <p class="text-muted mt-3 small"><i class="fas fa-sync-alt me-1"></i> Click card to reveal answer</p>
                </div>
                <div class="flip-card-back">
                    <span class="badge bg-primary mb-3"><i class="fas fa-check-circle me-1"></i> Back / Explanation</span>
                    <h6 class="leading-relaxed flashcard-back-text" style="line-height: 1.6;">${escapeHtml(card.back)}</h6>
                    <p class="text-white-50 mt-3 small"><i class="fas fa-sync-alt me-1"></i> Click card to flip back</p>
                </div>
            </div>
        </div>

        <div class="d-flex justify-content-between align-items-center mx-auto" style="max-width: 450px;">
            <button class="btn btn-premium-outline btn-sm" onclick="prevDocFlashcard()" ${State.docFlashcards.currentIndex === 0 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left me-1"></i> Prev
            </button>
            <span class="text-muted small">Card ${State.docFlashcards.currentIndex + 1} of ${total}</span>
            <button class="btn btn-premium-outline btn-sm" onclick="nextDocFlashcard()" ${State.docFlashcards.currentIndex === total - 1 ? 'disabled' : ''}>
                Next <i class="fas fa-chevron-right ms-1"></i>
            </button>
        </div>
    `;
}

function prevDocFlashcard() {
    if (State.docFlashcards.currentIndex > 0) {
        State.docFlashcards.currentIndex--;
        renderDocFlashcard();
    }
}


function nextDocFlashcard() {
    if (State.docFlashcards.currentIndex < State.docFlashcards.cards.length - 1) {
        State.docFlashcards.currentIndex++;
        renderDocFlashcard();
    }
}

