/**
 * Financial AI Analyst - Frontend Application
 * Handles API communication, UI interactions, and state management
 */

// =====================================================
// CONFIGURATION
// =====================================================

const CONFIG = {
    // Update this URL when deploying backend
    // NOTE: Use the direct .hf.space URL, not the huggingface.co/spaces URL
    API_BASE_URL: 'https://prudhvirajchalapaka-ai-financial-analyst-rag-model.hf.space',
    POLLING_INTERVAL: 2000,
    MAX_POLL_ATTEMPTS: 450, // 15 minutes max (increased from 5 min)
};

// =====================================================
// STATE MANAGEMENT
// =====================================================

const state = {
    sessionId: null,
    isProcessing: false,
    isReady: false,
    selectedFile: null,
    chatHistory: [],
    theme: localStorage.getItem('theme') || 'light',
};

// =====================================================
// DOM ELEMENTS
// =====================================================

const elements = {
    // Sidebar
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    mobileMenuBtn: document.getElementById('mobileMenuBtn'),

    // Upload
    uploadZone: document.getElementById('uploadZone'),
    uploadContent: document.getElementById('uploadContent'),
    fileInput: document.getElementById('fileInput'),
    fileSelected: document.getElementById('fileSelected'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    removeFile: document.getElementById('removeFile'),
    processBtn: document.getElementById('processBtn'),

    // Status
    statusIndicator: document.getElementById('statusIndicator'),
    statusText: document.getElementById('statusText'),
    statusDetail: document.getElementById('statusDetail'),

    // Session
    clearBtn: document.getElementById('clearBtn'),
    sessionInfo: document.getElementById('sessionInfo'),

    // Chat
    welcomeMessage: document.getElementById('welcomeMessage'),
    chatMessages: document.getElementById('chatMessages'),
    chatForm: document.getElementById('chatForm'),
    chatInput: document.getElementById('chatInput'),
    sendBtn: document.getElementById('sendBtn'),

    // Theme
    themeToggle: document.getElementById('themeToggle'),

    // Toast
    toastContainer: document.getElementById('toastContainer'),
};

// =====================================================
// INITIALIZATION
// =====================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializeEventListeners();
    checkExistingSession();
});

function initializeTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    updateThemeIcon();
}

function initializeEventListeners() {
    // Upload Zone
    elements.uploadZone.addEventListener('click', () => elements.fileInput.click());
    elements.uploadZone.addEventListener('dragover', handleDragOver);
    elements.uploadZone.addEventListener('dragleave', handleDragLeave);
    elements.uploadZone.addEventListener('drop', handleDrop);
    elements.fileInput.addEventListener('change', handleFileSelect);
    elements.removeFile.addEventListener('click', handleRemoveFile);
    elements.processBtn.addEventListener('click', handleProcessPDF);

    // Session
    elements.clearBtn.addEventListener('click', handleClearSession);

    // Chat
    elements.chatForm.addEventListener('submit', handleChatSubmit);
    elements.chatInput.addEventListener('input', autoResizeTextarea);
    elements.chatInput.addEventListener('keydown', handleChatKeydown);

    // Theme
    elements.themeToggle.addEventListener('click', toggleTheme);

    // Sidebar
    elements.mobileMenuBtn?.addEventListener('click', () => {
        elements.sidebar.classList.toggle('open');
    });

    elements.sidebarToggle?.addEventListener('click', () => {
        elements.sidebar.classList.toggle('open');
    });

    // Close sidebar on outside click (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 &&
            !elements.sidebar.contains(e.target) &&
            !elements.mobileMenuBtn.contains(e.target)) {
            elements.sidebar.classList.remove('open');
        }
    });
}

function checkExistingSession() {
    // Check session storage (clears on tab close)
    const savedSession = sessionStorage.getItem('currentSession');
    if (savedSession) {
        try {
            const session = JSON.parse(savedSession);
            state.sessionId = session.sessionId;
            pollProcessingStatus();
        } catch (e) {
            sessionStorage.removeItem('currentSession');
        }
    }
}

// =====================================================
// THEME HANDLING
// =====================================================

function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('theme', state.theme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const sunIcon = elements.themeToggle.querySelector('.sun-icon');
    const moonIcon = elements.themeToggle.querySelector('.moon-icon');

    if (state.theme === 'dark') {
        sunIcon.classList.add('hidden');
        moonIcon.classList.remove('hidden');
    } else {
        sunIcon.classList.remove('hidden');
        moonIcon.classList.add('hidden');
    }
}

// =====================================================
// FILE UPLOAD HANDLING
// =====================================================

function handleDragOver(e) {
    e.preventDefault();
    elements.uploadZone.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.uploadZone.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    elements.uploadZone.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

function handleFile(file) {
    if (!file.type.includes('pdf')) {
        showToast('Please select a PDF file', 'error');
        return;
    }

    state.selectedFile = file;

    // Update UI
    elements.uploadContent.classList.add('hidden');
    elements.fileSelected.classList.remove('hidden');
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);
    elements.processBtn.disabled = false;
}

function handleRemoveFile(e) {
    e.stopPropagation();
    state.selectedFile = null;
    elements.fileInput.value = '';
    elements.uploadContent.classList.remove('hidden');
    elements.fileSelected.classList.add('hidden');
    elements.processBtn.disabled = true;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// =====================================================
// PDF PROCESSING
// =====================================================

async function handleProcessPDF() {
    if (!state.selectedFile || state.isProcessing) return;

    state.isProcessing = true;
    updateProcessButton(true);
    updateStatus('processing', 'Uploading document...');

    try {
        const formData = new FormData();
        formData.append('file', state.selectedFile);

        const response = await fetch(`${CONFIG.API_BASE_URL}/api/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const data = await response.json();
        state.sessionId = data.session_id;

        // Save session (clears when tab closes)
        sessionStorage.setItem('currentSession', JSON.stringify({
            sessionId: state.sessionId,
            fileName: state.selectedFile.name,
            timestamp: Date.now(),
        }));

        // Start polling for status
        pollProcessingStatus();

    } catch (error) {
        console.error('Upload error:', error);
        showToast(error.message || 'Failed to upload document', 'error');
        state.isProcessing = false;
        updateProcessButton(false);
        updateStatus('error', 'Upload failed');
    }
}

async function pollProcessingStatus() {
    let attempts = 0;

    const poll = async () => {
        if (attempts >= CONFIG.MAX_POLL_ATTEMPTS) {
            showToast('Processing timeout. Please try again.', 'error');
            state.isProcessing = false;
            updateProcessButton(false);
            updateStatus('error', 'Processing timeout');
            return;
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/status/${state.sessionId}`);

            if (!response.ok) {
                throw new Error('Failed to get status');
            }

            const data = await response.json();

            updateStatus(data.status, data.message);

            if (data.status === 'ready') {
                state.isProcessing = false;
                state.isReady = true;
                updateProcessButton(false);
                enableChat();
                showToast('Document processed successfully!', 'success');
                elements.sessionInfo.textContent = `Document: ${data.document_name}`;
                return;
            }

            if (data.status === 'error') {
                state.isProcessing = false;
                updateProcessButton(false);
                showToast(data.message || 'Processing failed', 'error');
                return;
            }

            attempts++;
            setTimeout(poll, CONFIG.POLLING_INTERVAL);

        } catch (error) {
            console.error('Polling error:', error);
            attempts++;
            setTimeout(poll, CONFIG.POLLING_INTERVAL);
        }
    };

    poll();
}

function updateProcessButton(loading) {
    const btnText = elements.processBtn.querySelector('.btn-text');
    const btnLoader = elements.processBtn.querySelector('.btn-loader');

    if (loading) {
        btnText.textContent = 'Processing...';
        btnLoader.classList.remove('hidden');
        elements.processBtn.disabled = true;
    } else {
        btnText.textContent = 'Process Document';
        btnLoader.classList.add('hidden');
        elements.processBtn.disabled = !state.selectedFile || state.isReady;
    }
}

function updateStatus(status, message, detail = '') {
    elements.statusIndicator.className = 'status-indicator ' + status;
    elements.statusText.textContent = message;
    elements.statusDetail.textContent = detail;
}

// =====================================================
// CHAT HANDLING
// =====================================================

function enableChat() {
    elements.chatInput.disabled = false;
    elements.chatInput.placeholder = 'Ask about revenue, risks, or specific charts...';
    elements.sendBtn.disabled = false;
    elements.clearBtn.disabled = false;
    elements.welcomeMessage.classList.add('hidden');
}

function disableChat() {
    elements.chatInput.disabled = true;
    elements.chatInput.placeholder = 'Upload and process a document first...';
    elements.sendBtn.disabled = true;
}

function autoResizeTextarea() {
    elements.chatInput.style.height = 'auto';
    elements.chatInput.style.height = Math.min(elements.chatInput.scrollHeight, 150) + 'px';
}

function handleChatKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        elements.chatForm.dispatchEvent(new Event('submit'));
    }
}

async function handleChatSubmit(e) {
    e.preventDefault();

    const message = elements.chatInput.value.trim();
    if (!message || !state.isReady) return;

    // Add user message to UI
    addMessage('user', message);
    elements.chatInput.value = '';
    autoResizeTextarea();

    // Show typing indicator
    const typingId = addTypingIndicator();

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: state.sessionId,
                message: message,
            }),
        });

        // Remove typing indicator
        removeTypingIndicator(typingId);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Chat request failed');
        }

        const data = await response.json();
        addMessage('assistant', data.answer, data.sources);

    } catch (error) {
        removeTypingIndicator(typingId);
        console.error('Chat error:', error);
        addMessage('assistant', 'Sorry, I encountered an error processing your request. Please try again.');
        showToast(error.message || 'Chat error', 'error');
    }
}

function addMessage(role, content, sources = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const avatarText = role === 'user' ? 'You' : 'AI';

    let sourcesHTML = '';
    if (sources && sources.length > 0) {
        sourcesHTML = `
            <button class="sources-toggle" onclick="toggleSources(this)">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M3 5L6 8L9 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                View ${sources.length} source${sources.length > 1 ? 's' : ''}
            </button>
            <div class="sources-list">
                ${sources.map((source, i) => `
                    <div class="source-item">
                        <div class="source-label">Source ${i + 1} (${source.source_type})</div>
                        <div class="source-content">${escapeHTML(source.content)}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatarText.charAt(0).toUpperCase()}</div>
        <div class="message-content">
            <div class="message-bubble">${formatMessage(content)}</div>
            ${sourcesHTML}
        </div>
    `;

    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'chat-message assistant';
    typingDiv.innerHTML = `
        <div class="message-avatar">A</div>
        <div class="message-content">
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;

    elements.chatMessages.appendChild(typingDiv);
    scrollToBottom();

    return id;
}

function removeTypingIndicator(id) {
    const typingDiv = document.getElementById(id);
    if (typingDiv) {
        typingDiv.remove();
    }
}

function toggleSources(button) {
    button.classList.toggle('expanded');
    const sourcesList = button.nextElementSibling;
    sourcesList.classList.toggle('expanded');
}

function formatMessage(content) {
    // Basic markdown-like formatting
    return escapeHTML(content)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// =====================================================
// SESSION MANAGEMENT
// =====================================================

async function handleClearSession() {
    if (!state.sessionId) return;

    try {
        await fetch(`${CONFIG.API_BASE_URL}/api/session/${state.sessionId}`, {
            method: 'DELETE',
        });
    } catch (error) {
        console.error('Error deleting session:', error);
    }

    // Reset state
    state.sessionId = null;
    state.isProcessing = false;
    state.isReady = false;
    state.selectedFile = null;
    state.chatHistory = [];

    // Clear storage
    sessionStorage.removeItem('currentSession');

    // Reset UI
    elements.uploadContent.classList.remove('hidden');
    elements.fileSelected.classList.add('hidden');
    elements.fileInput.value = '';
    elements.processBtn.disabled = true;
    elements.clearBtn.disabled = true;
    elements.sessionInfo.textContent = '';

    updateStatus('waiting', 'Waiting for document...');
    disableChat();

    elements.chatMessages.innerHTML = '';
    elements.welcomeMessage.classList.remove('hidden');

    showToast('Session cleared', 'success');
}

// =====================================================
// TOAST NOTIFICATIONS
// =====================================================

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const iconPaths = {
        success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
        error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
        warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
        info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    };

    toast.innerHTML = `
        <div class="toast-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="${iconPaths[type] || iconPaths.info}"/>
            </svg>
        </div>
        <span class="toast-message">${escapeHTML(message)}</span>
        <button class="toast-close" onclick="this.closest('.toast').remove()">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
        </button>
    `;

    elements.toastContainer.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Make toggleSources available globally
window.toggleSources = toggleSources;
