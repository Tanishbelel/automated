// -- darsh: Updated extension JavaScript for redesigned UI with Show More and fixed download

// ===== Configuration =====
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// ===== State =====
let selectedFile = null;
let analysisData = null;
let authToken = null;
let currentUser = null;

// ===== DOM Elements =====
const elements = {
    // Navigation
    analyzeNavBtn: document.getElementById('analyzeNavBtn'),
    dashboardNavBtn: document.getElementById('dashboardNavBtn'),
    encryptNavBtn: document.getElementById('encryptNavBtn'),
    decryptNavBtn: document.getElementById('decryptNavBtn'),

    // Login
    loginSection: document.getElementById('loginSection'),
    loginUsername: document.getElementById('loginUsername'),
    loginPassword: document.getElementById('loginPassword'),
    loginBtn: document.getElementById('loginBtn'),
    signupBtn: document.getElementById('signupBtn'),
    loginMessage: document.getElementById('loginMessage'),

    // -- darsh: User Menu
    userMenu: document.getElementById('userMenu'),
    userAvatarSmall: document.getElementById('userAvatarSmall'),
    userNameSmall: document.getElementById('userNameSmall'),
    logoutBtn: document.getElementById('logoutBtn'),

    // Status
    statusIndicator: document.getElementById('statusIndicator'),
    statusText: document.getElementById('statusText'),

    // Upload
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    fileSelected: document.getElementById('fileSelected'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    removeFileBtn: document.getElementById('removeFileBtn'),
    platformSelect: document.getElementById('platformSelect'),
    analyzeBtn: document.getElementById('analyzeBtn'),

    // Loading
    loadingSection: document.getElementById('loadingSection'),

    // Results
    resultsSection: document.getElementById('resultsSection'),
    riskScore: document.getElementById('riskScore'),
    metadataList: document.getElementById('metadataList'),
    cleanBtn: document.getElementById('cleanBtn'),
    shareBtn: document.getElementById('shareBtn')
};

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    loadAuthState();
    checkServerConnection();
    setupEventListeners();
});

// ===== Event Listeners =====
function setupEventListeners() {
    // -- darsh: Navigation buttons
    elements.analyzeNavBtn?.addEventListener('click', () => {
        setActiveNav('analyze');
    });

    elements.dashboardNavBtn?.addEventListener('click', () => {
        if (authToken) {
            window.location.href = 'dashboard.html';
        } else {
            showLoginSection();
        }
    });

    elements.encryptNavBtn?.addEventListener('click', () => {
        window.location.href = 'encrypt.html';
    });

    elements.decryptNavBtn?.addEventListener('click', () => {
        window.location.href = 'encrypt.html?tab=decrypt';
    });

    // -- darsh: Login/Signup
    elements.loginBtn?.addEventListener('click', handleLogin);
    elements.signupBtn?.addEventListener('click', () => {
        window.location.href = 'auth.html';
    });

    // -- darsh: Logout
    elements.logoutBtn?.addEventListener('click', handleLogout);

    // -- darsh: File upload
    elements.uploadArea?.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput?.addEventListener('change', handleFileSelect);
    elements.removeFileBtn?.addEventListener('click', resetFileUpload);

    // -- darsh: Drag and drop
    setupDragDrop();

    // -- darsh: Analyze button
    elements.analyzeBtn?.addEventListener('click', analyzeFile);

    // -- darsh: Results actions
    elements.cleanBtn?.addEventListener('click', downloadCleanFile);
    elements.shareBtn?.addEventListener('click', generateShareLink);
}

// ===== Navigation =====
function setActiveNav(section) {
    document.querySelectorAll('.nav-card').forEach(card => {
        card.classList.remove('nav-card-active');
    });
    if (section === 'analyze') {
        elements.analyzeNavBtn?.classList.add('nav-card-active');
    }
}

// ===== Authentication =====
function loadAuthState() {
    chrome.storage.local.get(['authToken', 'currentUser'], (result) => {
        if (result.authToken && result.currentUser) {
            authToken = result.authToken;
            currentUser = result.currentUser;
            hideLoginSection();
        } else {
            showLoginSection();
        }
    });
}

function showLoginSection() {
    elements.loginSection?.classList.remove('hidden');
    elements.userMenu?.classList.add('hidden');
}

function hideLoginSection() {
    elements.loginSection?.classList.add('hidden');
    elements.userMenu?.classList.remove('hidden');

    // -- darsh: Update user menu with current user info
    if (currentUser) {
        const initial = (currentUser.first_name?.[0] || currentUser.username[0]).toUpperCase();
        elements.userAvatarSmall.textContent = initial;
        elements.userNameSmall.textContent = currentUser.first_name || currentUser.username;
    }
}

async function handleLogin() {
    const username = elements.loginUsername?.value.trim();
    const password = elements.loginPassword?.value;

    if (!username || !password) {
        showMessage('Please enter username and password', 'error');
        return;
    }

    try {
        elements.loginBtn.disabled = true;
        elements.loginBtn.textContent = 'Logging in...';

        const response = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;

            chrome.storage.local.set({ authToken, currentUser }, () => {
                hideLoginSection();
                showMessage('Login successful!', 'success');
            });
        } else {
            showMessage(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage('Connection error. Please try again.', 'error');
    } finally {
        elements.loginBtn.disabled = false;
        elements.loginBtn.textContent = 'Login';
    }
}

// -- darsh: Handle Logout
async function handleLogout() {
    try {
        // Call backend logout endpoint
        await fetch(`${API_BASE_URL}/auth/logout/`, {
            method: 'POST',
            headers: { 'Authorization': `Token ${authToken}` }
        });
    } catch (error) {
        console.error('Logout error:', error);
    }

    // Clear local state
    authToken = null;
    currentUser = null;

    // Clear chrome storage
    chrome.storage.local.remove(['authToken', 'currentUser'], () => {
        showLoginSection();
        showMessage('Logged out successfully', 'success');
    });
}


function showMessage(text, type) {
    if (!elements.loginMessage) return;
    elements.loginMessage.textContent = text;
    elements.loginMessage.className = `message ${type}`;
    elements.loginMessage.classList.remove('hidden');
    setTimeout(() => {
        elements.loginMessage.classList.add('hidden');
    }, 3000);
}

// ===== Server Connection =====
async function checkServerConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/analysis/`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok || response.status === 405) {
            updateConnectionStatus(true);
        } else {
            updateConnectionStatus(false);
        }
    } catch (error) {
        updateConnectionStatus(false);
    }
}

function updateConnectionStatus(isConnected) {
    if (!elements.statusIndicator) return;

    if (isConnected) {
        elements.statusIndicator.classList.add('connected');
        elements.statusText.textContent = 'Server connected';
    } else {
        elements.statusIndicator.classList.remove('connected');
        elements.statusText.textContent = 'Server connected';
    }
}

// ===== File Upload =====
function setupDragDrop() {
    if (!elements.uploadArea) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        elements.uploadArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            elements.uploadArea.style.borderColor = 'var(--accent-primary)';
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        elements.uploadArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            elements.uploadArea.style.borderColor = '';
        });
    });

    elements.uploadArea.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    if (file.size > 50 * 1024 * 1024) {
        alert('File too large. Maximum size is 50MB.');
        return;
    }

    selectedFile = file;

    // Update UI
    elements.uploadArea?.classList.add('hidden');
    elements.fileSelected?.classList.remove('hidden');
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);
    elements.analyzeBtn.disabled = false;
}

function resetFileUpload() {
    selectedFile = null;
    elements.fileInput.value = '';
    elements.uploadArea?.classList.remove('hidden');
    elements.fileSelected?.classList.add('hidden');
    elements.analyzeBtn.disabled = true;
    hideResults();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// ===== Analysis =====
async function analyzeFile() {
    if (!selectedFile) return;

    showLoading();

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('platform', elements.platformSelect.value);

    const headers = {};
    if (authToken) {
        headers['Authorization'] = `Token ${authToken}`;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/analyze/`, {
            method: 'POST',
            headers: headers,
            body: formData
        });

        if (!response.ok) {
            throw new Error('Analysis failed');
        }

        const data = await response.json();
        analysisData = data;
        displayResults(data);
    } catch (error) {
        hideLoading();
        alert('Error analyzing file: ' + error.message);
    }
}

function showLoading() {
    elements.loadingSection?.classList.remove('hidden');
    elements.resultsSection?.classList.add('hidden');
}

function hideLoading() {
    elements.loadingSection?.classList.add('hidden');
}

function displayResults(data) {
    hideLoading();
    elements.resultsSection?.classList.remove('hidden');

    // -- darsh: Display risk score
    const riskValue = elements.riskScore.querySelector('.risk-value');
    if (riskValue) {
        riskValue.textContent = data.risk_score || 0;

        // Color code the risk
        if (data.risk_score >= 70) {
            riskValue.style.color = 'var(--danger)';
        } else if (data.risk_score >= 40) {
            riskValue.style.color = 'var(--warning)';
        } else {
            riskValue.style.color = 'var(--success)';
        }
    }

    // -- darsh: Display metadata with Show More/Less functionality
    elements.metadataList.innerHTML = '';
    const metadataArray = data.metadata || data.metadata_entries || [];

    if (metadataArray.length > 0) {
        let showingAll = false;
        const INITIAL_LIMIT = 5;

        function renderMetadata() {
            elements.metadataList.innerHTML = '';
            const itemsToShow = showingAll ? metadataArray : metadataArray.slice(0, INITIAL_LIMIT);

            itemsToShow.forEach(item => {
                const metadataItem = document.createElement('div');
                metadataItem.className = 'metadata-item';
                metadataItem.innerHTML = `
                    <div class="metadata-key">${escapeHtml(item.key)}</div>
                    <div class="metadata-value">${escapeHtml(item.value)}</div>
                `;
                elements.metadataList.appendChild(metadataItem);
            });

            // Add Show More/Less button if there are more items than the limit
            if (metadataArray.length > INITIAL_LIMIT) {
                const btnContainer = document.createElement('div');
                btnContainer.style.cssText = 'text-align:center;margin-top:8px;';
                const toggleBtn = document.createElement('button');
                toggleBtn.className = 'btn-show-more';
                toggleBtn.textContent = showingAll ? 'Show Less' : `Show More (${metadataArray.length - INITIAL_LIMIT} more)`;
                toggleBtn.onclick = () => {
                    showingAll = !showingAll;
                    renderMetadata();
                };
                btnContainer.appendChild(toggleBtn);
                elements.metadataList.appendChild(btnContainer);
            }
        }

        renderMetadata();
    } else {
        elements.metadataList.innerHTML = '<p style="text-align:center;color:var(--text-muted);font-size:12px;">No metadata found</p>';
    }
}

function hideResults() {
    elements.resultsSection?.classList.add('hidden');
}

// ===== Download Clean File =====
async function downloadCleanFile() {
    if (!analysisData) return;

    try {
        elements.cleanBtn.disabled = true;
        elements.cleanBtn.textContent = 'Downloading...';

        // -- darsh: Use correct REST API endpoint
        const headers = {};
        if (authToken) {
            headers['Authorization'] = `Token ${authToken}`;
        }

        const analysisId = analysisData.analysis_id || analysisData.id; const response = await fetch(`${API_BASE_URL}/clean/`, { method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' }, body: JSON.stringify({ analysis_id: analysisId }) });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || 'Download failed');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `clean_${selectedFile.name}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        elements.cleanBtn.textContent = 'Downloaded!';
        setTimeout(() => {
            elements.cleanBtn.textContent = 'Clean & Download';
            elements.cleanBtn.disabled = false;
        }, 2000);
    } catch (error) {
        alert('Error downloading file: ' + error.message);
        elements.cleanBtn.textContent = 'Clean & Download';
        elements.cleanBtn.disabled = false;
    }
}

// ===== Share Link =====
async function generateShareLink() {
    if (!analysisData) return;

    const shareUrl = `${API_BASE_URL.replace('/api', '')}/share.html?token=${analysisData.share_token}`;

    try {
        await navigator.clipboard.writeText(shareUrl);
        elements.shareBtn.textContent = 'Link Copied!';
        setTimeout(() => {
            elements.shareBtn.textContent = 'Generate Share Link';
        }, 2000);
    } catch (error) {
        // Fallback: show alert with link
        prompt('Copy this link:', shareUrl);
    }
}

// ===== Utility Functions =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
