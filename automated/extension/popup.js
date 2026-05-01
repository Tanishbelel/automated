// -- darsh: Final integrated extension JS with Bulk Pipeline support and status polling
// ===== Configuration =====
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// ===== State =====
let selectedFiles = [];
let analysisData = null;
let authToken = null;
let currentUser = null;
let currentMode = 'analyze'; // 'analyze' or 'pipeline'
let bulkJobId = null;

// ===== DOM Elements =====
const elements = {
    // Navigation
    analyzeNavBtn: document.getElementById('analyzeNavBtn'),
    dashboardNavBtn: document.getElementById('dashboardNavBtn'),
    encryptNavBtn: document.getElementById('encryptNavBtn'),
    decryptNavBtn: document.getElementById('decryptNavBtn'),
    redactNavBtn: document.getElementById('redactNavBtn'),
    pipelineNavBtn: document.getElementById('pipelineNavBtn'),
    signatureToggle: document.getElementById('signatureToggle'),
    redactToggle: document.getElementById('redactToggle'),

    // Login
    loginSection: document.getElementById('loginSection'),
    loginUsername: document.getElementById('loginUsername'),
    loginPassword: document.getElementById('loginPassword'),
    loginBtn: document.getElementById('loginBtn'),
    signupBtn: document.getElementById('signupBtn'),
    loginMessage: document.getElementById('loginMessage'),

    // User Menu
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
    pipelineBtn: document.getElementById('pipelineBtn'),

    // Loading
    loadingSection: document.getElementById('loadingSection'),
    bulkProgressContainer: document.getElementById('bulkProgressContainer'),
    bulkProgressBar: document.getElementById('bulkProgressBar'),
    bulkProgressStats: document.getElementById('bulkProgressStats'),

    // Results
    resultsSection: document.getElementById('resultsSection'),
    riskScore: document.getElementById('riskScore'),
    metadataList: document.getElementById('metadataList'),
    cleanBtn: document.getElementById('cleanBtn'),
    shareBtn: document.getElementById('shareBtn'),
    directDownloadBtn: document.getElementById('directDownloadBtn')
};

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    loadAuthState();
    checkServerConnection();
    
    // Restore last active tab
    chrome.storage.local.get(['activeTab'], (result) => {
        if (result.activeTab) {
            setActiveNav(result.activeTab);
        } else {
            setActiveNav('analyze');
        }
    });
    
    setupEventListeners();
});

// ===== Event Listeners =====
function setupEventListeners() {
    elements.analyzeNavBtn?.addEventListener('click', () => setActiveNav('analyze'));
    elements.pipelineNavBtn?.addEventListener('click', () => setActiveNav('pipeline'));
    
    elements.dashboardNavBtn?.addEventListener('click', () => {
        if (authToken) window.location.href = 'dashboard.html';
        else showLoginSection();
    });

    elements.encryptNavBtn?.addEventListener('click', () => window.location.href = 'encrypt.html');
    elements.decryptNavBtn?.addEventListener('click', () => window.location.href = 'encrypt.html?tab=decrypt');
    elements.redactNavBtn?.addEventListener('click', () => window.location.href = 'redact.html');

    elements.loginBtn?.addEventListener('click', handleLogin);
    elements.signupBtn?.addEventListener('click', () => window.location.href = 'auth.html');
    elements.logoutBtn?.addEventListener('click', handleLogout);

    elements.uploadArea?.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput?.addEventListener('change', handleFileSelect);
    elements.removeFileBtn?.addEventListener('click', resetFileUpload);

    setupDragDrop();

    elements.analyzeBtn?.addEventListener('click', analyzeFile);
    elements.pipelineBtn?.addEventListener('click', handlePipelineExecution);

    elements.cleanBtn?.addEventListener('click', downloadCleanFile);
    elements.shareBtn?.addEventListener('click', generateShareLink);
}

// ===== Navigation =====
function setActiveNav(section) {
    chrome.storage.local.set({ activeTab: section });
    document.querySelectorAll('.nav-card').forEach(card => card.classList.remove('nav-card-active'));

    if (section === 'analyze') {
        currentMode = 'analyze';
        elements.analyzeNavBtn?.classList.add('nav-card-active');
        elements.analyzeBtn?.classList.remove('hidden');
        elements.pipelineBtn?.classList.add('hidden');
    } else if (section === 'pipeline') {
        currentMode = 'pipeline';
        elements.pipelineNavBtn?.classList.add('nav-card-active');
        elements.analyzeBtn?.classList.add('hidden');
        elements.pipelineBtn?.classList.remove('hidden');
    }
    resetFileUpload();
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
    if (currentUser) {
        const initial = (currentUser.first_name?.[0] || currentUser.username[0]).toUpperCase();
        elements.userAvatarSmall.textContent = initial;
        elements.userNameSmall.textContent = currentUser.first_name || currentUser.username;
    }
}

async function handleLogin() {
    const username = elements.loginUsername?.value.trim();
    const password = elements.loginPassword?.value;
    if (!username || !password) return showMessage('Please enter credentials', 'error');

    try {
        elements.loginBtn.disabled = true;
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
        } else showMessage(data.error || 'Login failed', 'error');
    } catch (error) {
        showMessage('Connection error', 'error');
    } finally {
        elements.loginBtn.disabled = false;
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_BASE_URL}/auth/logout/`, {
            method: 'POST',
            headers: { 'Authorization': `Token ${authToken}` }
        });
    } catch (e) {}
    authToken = null;
    currentUser = null;
    chrome.storage.local.remove(['authToken', 'currentUser'], () => {
        showLoginSection();
        showMessage('Logged out', 'success');
    });
}

function showMessage(text, type) {
    if (!elements.loginMessage) return;
    elements.loginMessage.textContent = text;
    elements.loginMessage.className = `message ${type}`;
    elements.loginMessage.classList.remove('hidden');
    setTimeout(() => elements.loginMessage.classList.add('hidden'), 3000);
}

// ===== Server Connection =====
async function checkServerConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health/`);
        updateConnectionStatus(response.ok);
    } catch (error) {
        updateConnectionStatus(false);
    }
}

function updateConnectionStatus(isConnected) {
    if (!elements.statusIndicator) return;
    elements.statusIndicator.classList.toggle('connected', isConnected);
    elements.statusText.textContent = isConnected ? 'Server connected' : 'Server disconnected';
}

// ===== File Upload =====
function setupDragDrop() {
    if (!elements.uploadArea) return;
    ['dragenter', 'dragover'].forEach(e => {
        elements.uploadArea.addEventListener(e, (ev) => {
            ev.preventDefault();
            elements.uploadArea.style.borderColor = 'var(--accent-primary)';
        });
    });
    ['dragleave', 'drop'].forEach(e => {
        elements.uploadArea.addEventListener(e, (ev) => {
            ev.preventDefault();
            elements.uploadArea.style.borderColor = '';
        });
    });
    elements.uploadArea.addEventListener('drop', (e) => {
        handleFiles(e.dataTransfer.files);
    });
}

function handleFileSelect(e) {
    handleFiles(e.target.files);
}

function handleFiles(files) {
    if (files.length === 0) return;
    
    selectedFiles = Array.from(files);
    
    elements.uploadArea?.classList.add('hidden');
    elements.fileSelected?.classList.remove('hidden');
    
    if (selectedFiles.length === 1) {
        elements.fileName.textContent = selectedFiles[0].name;
        elements.fileSize.textContent = formatFileSize(selectedFiles[0].size);
    } else {
        elements.fileName.textContent = `${selectedFiles.length} files selected`;
        const totalSize = selectedFiles.reduce((acc, f) => acc + f.size, 0);
        elements.fileSize.textContent = `Total: ${formatFileSize(totalSize)}`;
    }
    
    elements.analyzeBtn.disabled = selectedFiles.length === 0;
    elements.pipelineBtn.disabled = selectedFiles.length === 0;
}

async function fetchDownload(url, filename) {
    console.log(`📡 Starting download from: ${url} as ${filename}`);
    try {
        const headers = authToken ? { 'Authorization': `Token ${authToken}` } : {};
        const response = await fetch(url, { method: 'GET', headers: headers });
        if (!response.ok) throw new Error(`Download failed: ${response.status}`);
        
        const blob = await response.blob();
        console.log(`📦 Received blob: ${blob.size} bytes`);
        
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename.startsWith('clean_') ? filename : `clean_${filename}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
        console.log('✅ Download successful');
    } catch (error) {
        console.error('❌ Download error:', error);
        alert('Download error: ' + error.message);
    }
}

function resetFileUpload() {
    selectedFiles = [];
    if (elements.fileInput) elements.fileInput.value = '';
    elements.uploadArea?.classList.remove('hidden');
    elements.fileSelected?.classList.add('hidden');
    elements.analyzeBtn.disabled = true;
    elements.pipelineBtn.disabled = true;
    hideResults();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ===== Execution =====
async function analyzeFile() {
    if (selectedFiles.length === 0) return;
    showLoading('Analyzing metadata...');

    const formData = new FormData();
    formData.append('file', selectedFiles[0]);
    formData.append('platform', elements.platformSelect.value);

    try {
        const response = await fetch(`${API_BASE_URL}/analyze/`, {
            method: 'POST',
            headers: authToken ? { 'Authorization': `Token ${authToken}` } : {},
            body: formData
        });
        if (!response.ok) throw new Error('Analysis failed');
        const data = await response.json();
        analysisData = data;
        displayResults(data);
    } catch (error) {
        hideLoading();
        alert(error.message);
    }
}

async function handlePipelineExecution() {
    if (selectedFiles.length === 0 || elements.pipelineBtn.disabled) return;
    
    elements.pipelineBtn.disabled = true;
    elements.analyzeBtn.disabled = true;
    
    if (selectedFiles.length === 1) {
        runSinglePipeline();
    } else {
        runBulkPipeline();
    }
}

async function runSinglePipeline() {
    showLoading('Running smart pipeline...');
    const formData = new FormData();
    formData.append('file', selectedFiles[0]);
    formData.append('platform', elements.platformSelect.value);
    formData.append('apply_signature', elements.signatureToggle.checked);
    formData.append('apply_redaction', elements.redactToggle.checked);

    try {
        const response = await fetch(`${API_BASE_URL}/pipeline/`, {
            method: 'POST',
            headers: authToken ? { 'Authorization': `Token ${authToken}` } : {},
            body: formData
        });
        if (!response.ok) throw new Error('Pipeline failed');
        const data = await response.json();
        analysisData = data;
        displayResults(data);
        showCompletionMessage('✨ Smart Pipeline complete! Risk scored & metadata cleaned.');
    } catch (error) {
        hideLoading();
        alert(error.message);
    }
}

async function runBulkPipeline() {
    showLoading('Submitting bulk job...');
    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('files', file));
    formData.append('platform', elements.platformSelect.value);
    formData.append('encrypt', 'false');
    formData.append('apply_signature', elements.signatureToggle.checked);
    formData.append('apply_redaction', elements.redactToggle.checked);
    
    try {
        const response = await fetch(`${API_BASE_URL}/pipeline/bulk/`, {
            method: 'POST',
            headers: authToken ? { 'Authorization': `Token ${authToken}` } : {},
            body: formData
        });
        if (!response.ok) throw new Error('Bulk submission failed');
        const data = await response.json();
        bulkJobId = data.job_id;
        pollBulkStatus(bulkJobId);
    } catch (error) {
        hideLoading();
        alert(error.message);
    }
}

async function pollBulkStatus(jobId) {
    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/pipeline/bulk/status/${jobId}/`);
            if (!response.ok) {
                setTimeout(poll, 3000);
                return;
            }
            const data = await response.json();
            
            if (data.status === 'error') {
                setTimeout(poll, 2000);
                return;
            }
            
            if (data.status === 'completed' || data.status === 'failed') {
                hideLoading();
                displayBulkResults(jobId, data);
                showCompletionMessage(`✨ Bulk job complete! ${data.completed} files cleaned.`);
            } else {
                const total = data.total || 0;
                const completed = data.completed || 0;
                const loadingText = document.querySelector('.loading-text');
                
                // Show/Update Progress UI
                elements.bulkProgressContainer?.classList.remove('hidden');
                
                if (data.status === 'pending') {
                    if (loadingText) loadingText.textContent = `Preparing batch...`;
                    if (elements.bulkProgressStats) elements.bulkProgressStats.textContent = `Job Queued`;
                    if (elements.bulkProgressBar) elements.bulkProgressBar.style.width = '0%';
                } else {
                    const progress = total > 0 ? Math.round((completed / total) * 100) : 0;
                    if (loadingText) loadingText.textContent = `Processing bulk job...`;
                    if (elements.bulkProgressStats) elements.bulkProgressStats.textContent = `${completed} / ${total} files cleaned (${progress}%)`;
                    if (elements.bulkProgressBar) elements.bulkProgressBar.style.width = `${progress}%`;
                }
                
                setTimeout(poll, 2000);
            }
        } catch (error) {
            setTimeout(poll, 5000);
        }
    };
    poll();
}

function showLoading(text) {
    elements.loadingSection?.classList.remove('hidden');
    elements.resultsSection?.classList.add('hidden');
    elements.bulkProgressContainer?.classList.add('hidden'); // Reset progress bar
    if (text) {
        const loadingText = elements.loadingSection.querySelector('.loading-text');
        if (loadingText) loadingText.textContent = text;
    }
}

function hideLoading() {
    elements.loadingSection?.classList.add('hidden');
    if (elements.pipelineBtn) elements.pipelineBtn.disabled = false;
    if (elements.analyzeBtn) elements.analyzeBtn.disabled = false;
}

function showCompletionMessage(text) {
    const msg = document.createElement('div');
    msg.className = 'message success';
    msg.style.marginTop = '10px';
    msg.textContent = text;
    elements.metadataList.prepend(msg);
}

function displayResults(data) {
    hideLoading();
    analysisData = data;
    elements.resultsSection?.classList.remove('hidden');
    elements.riskScore.querySelector('.risk-value').textContent = data.risk_score || 0;
    
    if (elements.directDownloadBtn) {
        if (!data.job_id) {
            elements.directDownloadBtn.classList.remove('hidden');
            elements.directDownloadBtn.onclick = () => {
                const downloadUrl = `${API_BASE_URL}/analyses/${data.analysis_id}/download_clean/`;
                fetchDownload(downloadUrl, data.filename || 'cleaned_file');
            };
        } else {
            elements.directDownloadBtn.classList.add('hidden');
        }
    }

    elements.metadataList.innerHTML = '';
    let displayItems = [];
    
    if (currentMode === 'pipeline') {
        if (data.fields_removed) displayItems.push({ key: 'Stripped Metadata', value: data.fields_removed.join(', ') });
        if (data.pii_patterns_found) {
            const piiStr = data.pii_patterns_found.map(p => `${p.type} (${Math.round(p.confidence)}%)`).join(', ');
            displayItems.push({ key: 'PII Redacted', value: piiStr || 'None' });
        }
        if (data.sha256_hash) displayItems.push({ key: 'SHA256', value: data.sha256_hash.substring(0, 16) + '...' });
    } else {
        displayItems = data.metadata || data.metadata_entries || [];
    }

    renderMetadataList(displayItems);
}

function displayBulkResults(jobId, data) {
    elements.resultsSection?.classList.remove('hidden');
    elements.riskScore.classList.add('hidden');
    elements.metadataList.innerHTML = `<h4 style="margin-bottom:12px; font-weight:600; color:var(--text-primary);">Batch Process Dashboard</h4>`;
    
    const summaryGrid = document.createElement('div');
    summaryGrid.className = 'bulk-summary-grid';
    summaryGrid.innerHTML = `
        <div class="summary-card">
            <span class="value">${data.total}</span>
            <span class="label">Total</span>
        </div>
        <div class="summary-card success">
            <span class="value">${data.completed}</span>
            <span class="label">Cleaned</span>
        </div>
        <div class="summary-card failed">
            <span class="value">${data.failed}</span>
            <span class="label">Failed</span>
        </div>
    `;
    elements.metadataList.appendChild(summaryGrid);

    const zipAction = document.createElement('div');
    zipAction.style.marginBottom = '20px';
    zipAction.innerHTML = `
        <button id="downloadZipBtn" class="btn-primary" style="width:100%; background:var(--success); border:none; padding:12px; border-radius:var(--radius-md); font-weight:bold; color:white; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
            Download All Cleaned (ZIP)
        </button>
    `;
    elements.metadataList.appendChild(zipAction);

    document.getElementById('downloadZipBtn').onclick = () => {
        const zipUrl = `${API_BASE_URL}/pipeline/bulk/download-zip/${jobId}/`;
        fetchDownload(zipUrl, `batch_results_${jobId.slice(0, 8)}.zip`);
    };

    const fileList = document.createElement('div');
    fileList.className = 'bulk-file-list';
    fileList.style.maxHeight = '240px';
    fileList.style.overflowY = 'auto';

    if (data.results) {
        data.results.forEach(res => {
            const item = document.createElement('div');
            item.className = 'bulk-file-item';
            const name = res.filename || 'Unknown File';
            let statusBadge = '';
            let actionHtml = '';
            
            if (res.status === 'cleaned') {
                statusBadge = '<span class="file-status-badge badge-success">Success</span>';
                const dlId = `dl-${res.analysis_id}`;
                actionHtml = `<button id="${dlId}" class="btn-bulk-download">Download</button>`;
                setTimeout(() => {
                    document.getElementById(dlId)?.addEventListener('click', () => {
                        fetchDownload(`${API_BASE_URL}${res.download_url}`, name);
                    });
                }, 0);
            } else if (res.status === 'processing') {
                statusBadge = '<span class="file-status-badge badge-processing">Processing...</span>';
                actionHtml = `<div class="spinner-small" style="width:12px; height:12px; border:2px solid #ccc; border-top:2px solid #0369a1; border-radius:50%; animation:spin 1s linear infinite;"></div>`;
            } else {
                statusBadge = '<span class="file-status-badge badge-error">Failed</span>';
                actionHtml = `<span style="font-size:11px; color:var(--danger);">Error</span>`;
            }

            item.innerHTML = `
                <div style="display:flex; flex-direction:column; gap:4px; flex:1; overflow:hidden;">
                    <span style="font-size:13px; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${name}</span>
                    ${statusBadge}
                </div>
                <div style="margin-left:12px;">${actionHtml}</div>
            `;
            fileList.appendChild(item);
        });
    }
    
    elements.metadataList.appendChild(fileList);
    elements.directDownloadBtn?.classList.add('hidden');
}

function renderMetadataList(items) {
    const INITIAL_LIMIT = 5;
    let showingAll = false;
    
    const render = () => {
        const existingMsg = elements.metadataList.querySelector('.message.success');
        elements.metadataList.innerHTML = '';
        if (existingMsg) elements.metadataList.appendChild(existingMsg);

        const itemsToShow = showingAll ? items : items.slice(0, INITIAL_LIMIT);
        itemsToShow.forEach(item => {
            const div = document.createElement('div');
            div.className = 'metadata-item';
            div.innerHTML = `<div class="metadata-key">${escapeHtml(item.key)}</div><div class="metadata-value">${escapeHtml(item.value)}</div>`;
            elements.metadataList.appendChild(div);
        });

        if (items.length > INITIAL_LIMIT) {
            const btn = document.createElement('button');
            btn.className = 'btn-show-more';
            btn.textContent = showingAll ? 'Show Less' : `Show More (${items.length - INITIAL_LIMIT})`;
            btn.onclick = () => { showingAll = !showingAll; render(); };
            elements.metadataList.appendChild(btn);
        }
    };
    render();
}

function hideResults() {
    elements.resultsSection?.classList.add('hidden');
    elements.riskScore.classList.remove('hidden');
    elements.cleanBtn.classList.remove('hidden');
}

async function downloadCleanFile() {
    if (!analysisData) return;
    try {
        elements.cleanBtn.disabled = true;
        elements.cleanBtn.textContent = 'Downloading...';
        const analysisId = analysisData.analysis_id || analysisData.id;
        const response = await fetch(`${API_BASE_URL}/clean/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...(authToken ? { 'Authorization': `Token ${authToken}` } : {}) },
            body: JSON.stringify({ analysis_id: analysisId })
        });
        if (!response.ok) throw new Error('Download failed');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `clean_${selectedFiles[0].name}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        elements.cleanBtn.textContent = 'Downloaded!';
        setTimeout(() => { elements.cleanBtn.textContent = 'Clean & Download'; elements.cleanBtn.disabled = false; }, 2000);
    } catch (error) {
        alert(error.message);
        elements.cleanBtn.disabled = false;
        elements.cleanBtn.textContent = 'Clean & Download';
    }
}

async function generateShareLink() {
    if (!analysisData) return;
    const shareUrl = `${API_BASE_URL.replace('/api', '')}/share.html?token=${analysisData.share_token}`;
    try {
        await navigator.clipboard.writeText(shareUrl);
        elements.shareBtn.textContent = 'Link Copied!';
        setTimeout(() => elements.shareBtn.textContent = 'Generate Share Link', 2000);
    } catch (e) { 
        if (analysisData.share_token) prompt('Copy link:', shareUrl); 
        else alert('No share token available');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
