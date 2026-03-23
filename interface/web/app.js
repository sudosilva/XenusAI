/**
 * XenusAI — Frontend Application
 * Handles chat interaction, ingestion, and knowledge base management via Eel.
 */

// ─── State ────────────────────────────────────────────────────

const state = {
    messages: [],
    isProcessing: false,
    isAborted: false,
    loadingId: null
};

const SEND_ICON = `
    <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
    </svg>
`;

const STOP_ICON = `
    <svg stroke="currentColor" fill="currentColor" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">
        <rect x="6" y="6" width="12" height="12"></rect>
    </svg>
`;

// ─── DOM Elements ─────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const els = {
    welcomeScreen: $('#welcome-screen'),
    chatMessages: $('#chat-messages'),
    messagesContainer: $('#messages-container'),
    queryInput: $('#query-input'),
    sendBtn: $('#send-btn'),
    micBtn: $('#mic-btn'),
    ingestInput: $('#ingest-input'),
    ingestBtn: $('#ingest-btn'),
    ingestStatus: $('#ingest-status'),
    statChunks: $('#stat-chunks'),
    statSources: $('#stat-sources'),
    sourcesList: $('#sources-list'),
    newChatBtn: $('#new-chat-btn'),
    sidebar: $('#sidebar'),
    sidebarToggle: $('#sidebar-toggle'),
    micSelect: $('#mic-select'),
};

// ─── Initialization ───────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    refreshStats();
    loadMicrophones();
});

function loadMicrophones() {
    if (!els.micSelect) return;
    eel.py_get_microphones()().then(response => {
        if (response.status === 'success' && response.mics.length > 0) {
            els.micSelect.innerHTML = '';
            response.mics.forEach(mic => {
                const opt = document.createElement('option');
                opt.value = mic.id;
                opt.textContent = mic.name;
                if (mic.id === response.default) opt.selected = true;
                els.micSelect.appendChild(opt);
            });
            els.micSelect.style.display = 'inline-block';
        }
    });
}

function setupEventListeners() {
    // Microphone (STT)
    if (els.micBtn) els.micBtn.addEventListener('click', toggleDictation);

    // Send message
    els.sendBtn.addEventListener('click', () => {
        if (state.isProcessing) abortGeneration();
        else sendMessage();
    });
    els.queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    els.queryInput.addEventListener('input', () => {
        autoResize(els.queryInput);
        els.sendBtn.disabled = !els.queryInput.value.trim();
    });

    // Ingest
    els.ingestBtn.addEventListener('click', handleIngest);
    els.ingestInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleIngest();
    });

    // New chat
    els.newChatBtn.addEventListener('click', newChat);
}

// ─── Chat Functions ───────────────────────────────────────────

async function sendMessage() {
    const query = els.queryInput.value.trim();
    if (!query || state.isProcessing) return;

    state.isProcessing = true;
    state.isAborted = false;

    // Trigger glide-down animation by removing empty state
    const mainArea = document.getElementById('main-area');
    if (mainArea && mainArea.classList.contains('empty')) {
        mainArea.classList.remove('empty');
    }

    els.chatMessages.classList.remove('hidden');

    // Add user message
    addMessage('user', query);
    state.messages.push({role: 'user', content: query});

    // Clear input
    els.queryInput.value = '';
    autoResize(els.queryInput);
    
    // Morph button into STOP
    els.sendBtn.innerHTML = STOP_ICON;
    els.sendBtn.disabled = false;
    els.sendBtn.classList.add('stop-mode');

    // Show loading
    state.loadingId = addLoadingMessage();

    try {
        const history = state.messages.slice(0, -1);
        const response = await eel.py_search(query, history)();

        if (state.isAborted) return; // User cancelled visually

        if (response.type === 'error') {
            morphMessage(state.loadingId, `<div class="no-results" style="color: var(--error)">${escapeHtml(response.message)}</div>`);
            autoReadAloud("An error occurred generating my response.");
        } else if (response.type === 'conversational') {
            morphMessage(state.loadingId, `<p>${escapeHtml(response.message).replace(/\\n/g, '<br>')}</p>`, true);
            state.messages.push({role: 'assistant', content: response.message});
            autoReadAloud(response.message);
        } else if (response.type === 'no_results') {
            morphMessage(state.loadingId, createNoResultsHTML());
            autoReadAloud("I couldn't find any relevant data regarding that in my local knowledge base.");
        } else {
            morphAIResponse(state.loadingId, response);
            state.messages.push({role: 'assistant', content: response.message});
            
            // Clean markdown asterisks purely for the voice synthesizer so it doesn't say "star star"
            let spokenText = response.message.replace(/\*/g, '').trim(); 
            autoReadAloud(spokenText);
        }
        state.loadingId = null;
    } catch (error) {
        if (state.isAborted) return;
        morphMessage(state.loadingId, `<div class="no-results">An error occurred: ${escapeHtml(error.toString())}</div>`);
        state.loadingId = null;
    }

    resetSendBtn();
}

function abortGeneration() {
    state.isAborted = true;
    if (state.loadingId) {
        removeMessage(state.loadingId);
        state.loadingId = null;
    }
    resetSendBtn();
}

function resetSendBtn() {
    state.isProcessing = false;
    els.sendBtn.innerHTML = SEND_ICON;
    els.sendBtn.classList.remove('stop-mode');
    els.sendBtn.disabled = !els.queryInput.value.trim();
}

function addMessage(type, content) {
    const id = 'msg-' + Date.now() + Math.random().toString(36).slice(2, 6);
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}-message`;
    messageEl.id = id;

    // Pure absolute minimalist text, no avatars
    messageEl.innerHTML = `
        <div class="message-inner">
            <div class="message-content">
                ${type === 'user' ? `<p class="user-text">${escapeHtml(content)}</p>` : content}
            </div>
        </div>
    `;

    els.chatMessages.appendChild(messageEl);
    scrollToBottom();
    return id;
}

function morphMessage(id, newHTML, addActions = false) {
    const el = document.getElementById(id);
    if (!el) return;
    
    const contentDiv = el.querySelector('.message-content');
    if (!contentDiv) return;

    // Smooth CSS Opacity Morph
    contentDiv.style.opacity = '0';
    
    setTimeout(() => {
        contentDiv.innerHTML = newHTML;
        
        // Append Action Toolbars after AI messages load
        if (addActions && el.classList.contains('ai-message')) {
            const inner = el.querySelector('.message-inner');
            if (!inner.querySelector('.message-actions')) {
                const actions = document.createElement('div');
                actions.className = 'message-actions';
                actions.innerHTML = `
                    <button class="action-btn copy-btn" onclick="copyText(this)" data-tooltip="Copy">
                        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="15" width="15" xmlns="http://www.w3.org/2000/svg"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    </button>
                    <button class="action-btn reply-btn" onclick="replyToText(this)" data-tooltip="Reply">
                        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="15" width="15" xmlns="http://www.w3.org/2000/svg"><polyline points="9 17 4 12 9 7"></polyline><path d="M20 18v-2a4 4 0 0 0-4-4H4"></path></svg>
                    </button>
                    <button class="action-btn speaker-btn" onclick="readAloud(this)" data-tooltip="Read Aloud">
                        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="15" width="15" xmlns="http://www.w3.org/2000/svg"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
                    </button>
                `;
                inner.appendChild(actions);
            }
        }
        
        contentDiv.style.opacity = '1';
        scrollToBottom();
    }, 250); // wait for 0.25s CSS opacity fade
}

function morphAIResponse(id, response) {
    let summaryHtml = escapeHtml(response.message)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
        
    let html = `<p>${summaryHtml}</p>`;

    if (response.results && response.results.length > 0) {
        response.results.forEach((result) => {
            const score = Math.round(result.score * 100);
            let scoreClass = 'low';
            if (score >= 65) scoreClass = 'high';
            else if (score >= 40) scoreClass = 'medium';

            const title = result.title || 'Untitled';
            const text = result.document || '';
            const source = result.source || 'Unknown';

            html += `
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-title">${escapeHtml(title)}</span>
                        <span class="result-score ${scoreClass}">${score}% match</span>
                    </div>
                    <div class="result-text">${escapeHtml(text)}</div>
                    <div class="result-source" title="${escapeHtml(source)}">${escapeHtml(truncateSource(source))}</div>
                </div>
            `;
        });
    }

    morphMessage(id, html, true);
}

function addLoadingMessage() {
    const phrases = [
        "Thinking", 
        "Pondering", 
        "Extending", 
        "Researching",
        "Finding",
        "Intriguing"
    ];
    const randomPhrase = phrases[Math.floor(Math.random() * phrases.length)];
    
    return addMessage('ai', `
        <div class="loading-wrapper">
            <span class="loading-state-text">${randomPhrase}...</span>
        </div>
    `);
}

function addAIResponse(response) {
    // Convert markdown bold to HTML strong for the summary message
    let summaryHtml = escapeHtml(response.message)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
        
    let html = `<p>${summaryHtml}</p>`;

    if (response.results && response.results.length > 0) {
        response.results.forEach((result, i) => {
            const score = Math.round(result.score * 100);
            let scoreClass = 'low';
            if (score >= 65) scoreClass = 'high';
            else if (score >= 40) scoreClass = 'medium';

            const title = result.title || 'Untitled';
            const text = result.document || '';
            const source = result.source || 'Unknown';

            html += `
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-title">${escapeHtml(title)}</span>
                        <span class="result-score ${scoreClass}">${score}% match</span>
                    </div>
                    <div class="result-text">${escapeHtml(text)}</div>
                    <div class="result-source" title="${escapeHtml(source)}">${escapeHtml(truncateSource(source))}</div>
                </div>
            `;
        });
    }

    addMessage('ai', html);
}

function createNoResultsHTML() {
    return `
        <div class="no-results">
            <p>No relevant results found in the knowledge base.</p>
            <p style="margin-top: 8px; font-size: 13px; color: var(--text-muted);">
                Try ingesting some data first using the sidebar.
            </p>
        </div>
    `;
}

// ─── Interaction Actions ─────────────────────────────────────

async function copyText(btn) {
    const messageContent = btn.closest('.message-inner').querySelector('.message-content').innerText;
    try {
        await navigator.clipboard.writeText(messageContent.trim());
        const originalHTML = btn.innerHTML;
        btn.innerHTML = `<svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="15" width="15" xmlns="http://www.w3.org/2000/svg"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
        btn.dataset.tooltip = "Copied!";
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.dataset.tooltip = "Copy";
        }, 2000);
    } catch (e) {
        console.error("Copy failed", e);
    }
}

function replyToText(btn) {
    const messageContent = btn.closest('.message-inner').querySelector('.message-content').innerText;
    // Extract the first 100 characters for a clean quote block reference
    const excerpt = messageContent.trim().substring(0, 100).replace(/\n/g, ' ') + (messageContent.length > 100 ? '...' : '');
    
    // Inject custom reply block formatting
    els.queryInput.value = `> "${excerpt}"\n\n`;
    autoResize(els.queryInput);
    els.queryInput.focus();
    els.sendBtn.disabled = false;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function newChat() {
    state.messages = [];
    els.chatMessages.innerHTML = '';
    els.chatMessages.classList.add('hidden');
    
    // Restore empty state to slide input back to middle
    const mainArea = document.getElementById('main-area');
    if (mainArea) mainArea.classList.add('empty');
    
    els.queryInput.value = '';
    autoResize(els.queryInput);
    els.sendBtn.disabled = true;
}

// ─── Ingest Functions ─────────────────────────────────────────

async function handleIngest() {
    const source = els.ingestInput.value.trim();
    if (!source) return;

    els.ingestBtn.disabled = true;
    showIngestStatus('loading', 'Ingesting...');

    try {
        const result = await eel.py_ingest(source)();

        if (result.status === 'success') {
            showIngestStatus('success',
                `Done! ${result.chunks_stored} chunks from ${result.documents_processed} doc(s) in ${result.elapsed_seconds}s`
            );
            els.ingestInput.value = '';
            refreshStats();
        } else {
            showIngestStatus('error', result.message || 'Ingestion failed');
        }
    } catch (error) {
        showIngestStatus('error', `Error: ${error.toString()}`);
    }

    els.ingestBtn.disabled = false;
}

function showIngestStatus(type, message) {
    els.ingestStatus.className = `ingest-status ${type}`;
    els.ingestStatus.textContent = message;
    els.ingestStatus.classList.remove('hidden');

    if (type !== 'loading') {
        setTimeout(() => {
            els.ingestStatus.classList.add('hidden');
        }, 6000);
    }
}

// ─── Stats & Sources ─────────────────────────────────────────

async function refreshStats() {
    try {
        const stats = await eel.py_get_stats()();
        els.statChunks.textContent = stats.total_chunks.toLocaleString();
        els.statSources.textContent = stats.unique_sources.toLocaleString();

        // Update sources list
        if (stats.sources && stats.sources.length > 0) {
            els.sourcesList.innerHTML = stats.sources
                .map(s => `<div class="source-item" title="${escapeHtml(s)}">${escapeHtml(truncateSource(s))}</div>`)
                .join('');
        } else {
            els.sourcesList.innerHTML = '<div class="empty-state-small">No sources yet</div>';
        }
    } catch (e) {
        console.error('Failed to refresh stats:', e);
    }
}

// ─── Utility Functions ────────────────────────────────────────

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 180) + 'px';
}

function scrollToBottom() {
    els.messagesContainer.scrollTop = els.messagesContainer.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateSource(source) {
    if (source.length <= 40) return source;
    // Show domain for URLs
    try {
        const url = new URL(source);
        return url.hostname + url.pathname.slice(0, 30) + '...';
    } catch {
        // File path - show last part
        const parts = source.replace(/\\/g, '/').split('/');
        return '...' + parts.slice(-2).join('/');
    }
}

// ─── Voice API (Python STT & Browser TTS) ──────────────────

let isRecording = false;

function toggleDictation() {
    if (isRecording) {
        // Stop dictation
        isRecording = false;
        els.micBtn.classList.remove('mic-recording');
        els.queryInput.placeholder = "Transcribing...";
        
        eel.py_stop_dictation()().then((response) => {
            if (response.status === 'success' && response.text) {
                const currentVal = els.queryInput.value;
                els.queryInput.value = currentVal + (currentVal ? ' ' : '') + response.text;
                autoResize(els.queryInput);
                els.sendBtn.disabled = false;
                
                // Autonomous execution upon transcription finish
                if (!state.isProcessing) sendMessage();
            } else {
                els.queryInput.placeholder = response.message || "Failed to transcribe.";
                setTimeout(() => { els.queryInput.placeholder = "Message XenusAI..."; }, 3000);
            }
        });
    } else {
        // Start dictation via Python using explicitly targeted hardware index
        const micId = els.micSelect ? els.micSelect.value : null;
        eel.py_start_dictation(micId)().then(() => {
            isRecording = true;
            els.micBtn.classList.add('mic-recording');
            els.queryInput.placeholder = "Listening... (Click Mic again to stop)";
        });
    }
}

function autoReadAloud(textLine) {
    if (!('speechSynthesis' in window)) return;
    
    window.speechSynthesis.cancel(); // Stop current speech
    
    // Quick sanitization of code blocks / hash symbols that disrupt TTS flow
    let cleanText = textLine.replace(/```[\s\S]*?```/g, " [Here is a code block] ");
    cleanText = cleanText.replace(/#/g, "");
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'en-US';
    utterance.rate = 1.05; // Slightly faster for intelligence
    
    const voices = window.speechSynthesis.getVoices();
    const premiumVoice = voices.find(v => v.name.includes("Natural") || v.name.includes("Aria")) || voices[0];
    if (premiumVoice) utterance.voice = premiumVoice;
    
    window.speechSynthesis.speak(utterance);
}

function readAloud(btn) {
    const textNode = btn.closest('.message-inner').querySelector('.message-content').innerText;
    autoReadAloud(textNode);
    
    const originalHTML = btn.innerHTML;
    btn.dataset.tooltip = "Playing...";
    btn.innerHTML = `<svg stroke="currentColor" fill="currentColor" stroke-width="2" viewBox="0 0 24 24" height="15" width="15" xmlns="http://www.w3.org/2000/svg"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`;
    
    // Simulate duration roughly if we don't hook utterance.onend globally
    setTimeout(() => {
        btn.innerHTML = originalHTML;
        btn.dataset.tooltip = "Read Aloud";
    }, 3000); 
}

// Global function for hint cards
function setQuery(text) {
    els.queryInput.value = text;
    autoResize(els.queryInput);
    els.sendBtn.disabled = false;
    els.queryInput.focus();
}
