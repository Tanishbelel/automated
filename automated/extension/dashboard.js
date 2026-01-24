// -- darsh: Extension dashboard using existing REST API with proper response handling

const API_BASE_URL = 'http://127.0.0.1:8000/api';

let authToken = null;
let currentUser = null;

// DOM Elements
const elements = {
    logoutBtn: document.getElementById('logoutBtn'),
    loadingSection: document.getElementById('loadingSection'),
    dashboardContent: document.getElementById('dashboardContent'),
    errorSection: document.getElementById('errorSection'),
    errorMessage: document.getElementById('errorMessage'),
    retryBtn: document.getElementById('retryBtn'),
    userAvatar: document.getElementById('userAvatar'),
    userName: document.getElementById('userName'),
    userEmail: document.getElementById('userEmail'),
    totalFiles: document.getElementById('totalFiles'),
    filesCleaned: document.getElementById('filesCleaned'),
    filesEncrypted: document.getElementById('filesEncrypted'),
    metadataRemoved: document.getElementById('metadataRemoved'),
    recentFiles: document.getElementById('recentFiles')
};

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    loadAuthState();
    setupEventListeners();
});

function setupEventListeners() {
    elements.logoutBtn?.addEventListener('click', logout);
    elements.retryBtn?.addEventListener('click', loadDashboard);
}

// Auth State
function loadAuthState() {
    chrome.storage.local.get(['authToken', 'currentUser'], (result) => {
        if (result.authToken && result.currentUser) {
            authToken = result.authToken;
            currentUser = result.currentUser;
            loadDashboard();
        } else {
            showError('Please login to view dashboard');
            setTimeout(() => {
                window.location.href = 'popup.html';
            }, 2000);
        }
    });
}

// -- darsh: Load Dashboard using existing /api/analyses/ endpoint
async function loadDashboard() {
    showLoading();

    try {
        // Fetch all user's file analyses
        const response = await fetch(`${API_BASE_URL}/analyses/`, {
            headers: { 'Authorization': `Token ${authToken}` }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch data');
        }

        const data = await response.json();
        console.log('API Response:', data); // Debug log

        // -- darsh: Fetch encrypted count from chrome storage (more reliable)
        chrome.storage.local.get(['encryptedFilesCount'], (result) => {
            const analyses = Array.isArray(data) ? data : (data.results || []);
            const stats = calculateStats(analyses, result.encryptedFilesCount || 0);
            displayDashboard(stats, analyses);
        });
    } catch (error) {
        console.error('Dashboard error:', error);
        showError(error.message || 'Failed to load dashboard');
    }
}

// -- darsh: Calculate stats from analyses array
function calculateStats(analyses, encryptedCount = 0) {
    const totalFiles = analyses.length;

    // -- darsh: Count files that have been cleaned (properly check cleaned_file_url)
    const filesCleaned = analyses.filter(a => a.cleaned_file_url || a.status === 'cleaned').length;

    // -- darsh: Sum all metadata fields found across all files
    let totalMetadata = 0;
    analyses.forEach(analysis => {
        const entries = analysis.metadata_entries || analysis.metadata || [];
        if (Array.isArray(entries) && entries.length > 0) {
            totalMetadata += entries.length;
        } else if (analysis.metadata_count) {
            totalMetadata += analysis.metadata_count;
        }
    });

    // -- darsh: Use passed encrypted count (from storage)
    const filesEncrypted = encryptedCount || 0;

    return {
        total_files: totalFiles,
        files_cleaned: filesCleaned,
        files_encrypted: filesEncrypted,
        total_metadata_removed: totalMetadata
    };
}

function displayDashboard(stats, analyses) {
    hideLoading();
    elements.dashboardContent?.classList.remove('hidden');

    // User info
    if (currentUser) {
        const initial = (currentUser.first_name?.[0] || currentUser.username[0]).toUpperCase();
        elements.userAvatar.textContent = initial;
        elements.userName.textContent = currentUser.first_name || currentUser.username;
        elements.userEmail.textContent = currentUser.email || '';
    }

    // Stats
    elements.totalFiles.textContent = stats.total_files || 0;
    elements.filesCleaned.textContent = stats.files_cleaned || 0;
    elements.filesEncrypted.textContent = stats.files_encrypted || 0;
    elements.metadataRemoved.textContent = stats.total_metadata_removed || 0;

    // Recent files
    if (analyses && analyses.length > 0) {
        elements.recentFiles.innerHTML = '';
        const recentAnalyses = analyses.slice(0, 10);
        recentAnalyses.forEach(analysis => {
            const item = createRecentItem(analysis);
            // -- darsh: Open comparison modal on click
            item.addEventListener('click', () => showComparisonModal(analysis));
            elements.recentFiles.appendChild(item);
        });
    } else {
        elements.recentFiles.innerHTML = '<p style="text-align:center;color:var(--text-muted);font-size:12px;padding:20px;">No files processed yet</p>';
    }
}

// -- darsh: Comparison Modal Functions
function showComparisonModal(analysis) {
    const modal = document.getElementById('comparisonModal');
    const filename = document.getElementById('modalFilename');
    const riskScore = document.getElementById('modalRiskScore');
    const body = document.getElementById('comparisonBody');
    const closeBtn = document.getElementById('closeModal');

    filename.textContent = analysis.original_filename;
    riskScore.textContent = `${analysis.risk_score || 0}%`;

    // Set risk color
    riskScore.className = 'summary-value risk-badge';
    if (analysis.risk_score >= 70) riskScore.style.background = '#fee2e2', riskScore.style.color = '#dc2626';
    else if (analysis.risk_score >= 40) riskScore.style.background = '#fef3c7', riskScore.style.color = '#d97706';
    else riskScore.style.background = '#d1fae5', riskScore.style.color = '#059669';

    // Populate table
    body.innerHTML = '';
    const metadata = analysis.metadata_entries || analysis.metadata || [];

    if (metadata.length === 0) {
        body.innerHTML = '<tr><td colspan="3" style="text-align:center;padding:20px;color:var(--text-muted);">No metadata found</td></tr>';
    } else {
        metadata.forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td style="font-weight:500;">${entry.key}</td>
                <td style="color:var(--text-secondary);max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${entry.value}">${entry.value}</td>
                <td><span class="status-tag ${entry.is_removed ? 'removed' : 'kept'}">${entry.is_removed ? 'REMOVED' : 'KEPT'}</span></td>
            `;
            body.appendChild(row);
        });
    }



    modal.classList.remove('hidden');

    // Close modal handlers
    const closeModal = () => modal.classList.add('hidden');
    closeBtn.onclick = closeModal;
    modal.onclick = (e) => { if (e.target === modal) closeModal(); };
}

function createRecentItem(analysis) {
    const item = document.createElement('div');
    item.className = 'recent-item';

    const riskLevel = analysis.risk_score >= 70 ? 'high' : analysis.risk_score >= 40 ? 'medium' : 'low';
    const date = new Date(analysis.created_at).toLocaleDateString();

    // Count metadata
    let metadataCount = 0;
    if (analysis.metadata && Array.isArray(analysis.metadata)) {
        metadataCount = analysis.metadata.length;
    } else if (analysis.metadata_entries && Array.isArray(analysis.metadata_entries)) {
        metadataCount = analysis.metadata_entries.length;
    }

    item.innerHTML = `
        <svg class="recent-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M13 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V9L13 2Z" stroke="currentColor" stroke-width="2"/>
            <path d="M13 2V9H20" stroke="currentColor" stroke-width="2"/>
        </svg>
        <div class="recent-info">
            <div class="recent-name">${escapeHtml(analysis.original_filename || 'Unknown')}</div>
            <div class="recent-meta">${date} • ${metadataCount} metadata</div>
        </div>
        <span class="recent-badge ${riskLevel}">${analysis.risk_score || 0}%</span>
    `;

    return item;
}

// Logout
async function logout() {
    try {
        await fetch(`${API_BASE_URL}/auth/logout/`, {
            method: 'POST',
            headers: { 'Authorization': `Token ${authToken}` }
        });
    } catch (error) {
        console.error('Logout error:', error);
    }

    chrome.storage.local.remove(['authToken', 'currentUser'], () => {
        window.location.href = 'popup.html';
    });
}

// UI States
function showLoading() {
    elements.loadingSection?.classList.remove('hidden');
    elements.dashboardContent?.classList.add('hidden');
    elements.errorSection?.classList.add('hidden');
}

function hideLoading() {
    elements.loadingSection?.classList.add('hidden');
}

function showError(message) {
    hideLoading();
    elements.errorSection?.classList.remove('hidden');
    elements.dashboardContent?.classList.add('hidden');
    elements.errorMessage.textContent = message;
}

// Utility
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
