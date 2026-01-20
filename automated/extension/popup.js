// ===== Configuration =====
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// ===== State =====
let selectedFile = null;
let analysisData = null;
let showAllMetadata = false;

// ===== DOM Elements =====
const elements = {
    // Connection
    connectionStatus: document.getElementById('connectionStatus'),

    // Upload Section
    uploadSection: document.getElementById('uploadSection'),
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    selectedFileDiv: document.getElementById('selectedFile'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    removeFile: document.getElementById('removeFile'),
    platform: document.getElementById('platform'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    errorMessage: document.getElementById('errorMessage'),

    // Loading Section
    loadingSection: document.getElementById('loadingSection'),

    // Results Section
    resultsSection: document.getElementById('resultsSection'),
    newAnalysis: document.getElementById('newAnalysis'),
    riskCard: document.getElementById('riskCard'),
    riskScore: document.getElementById('riskScore'),
    riskLabel: document.getElementById('riskLabel'),
    riskMeterFill: document.getElementById('riskMeterFill'),
    riskRecommendation: document.getElementById('riskRecommendation'),
    metadataCount: document.getElementById('metadataCount'),
    highRiskCount: document.getElementById('highRiskCount'),
    metadataList: document.getElementById('metadataList'),
    toggleMetadata: document.getElementById('toggleMetadata'),
    downloadClean: document.getElementById('downloadClean'),
    shareBtn: document.getElementById('shareBtn'),

    // Share Modal
    shareModal: document.getElementById('shareModal'),
    shareLink: document.getElementById('shareLink'),
    copyLink: document.getElementById('copyLink'),
    closeModal: document.getElementById('closeModal')
};

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    checkServerConnection();
    setupEventListeners();
});

// ===== Server Connection =====
async function checkServerConnection() {
    const statusDot = elements.connectionStatus.querySelector('.status-dot');
    const statusText = elements.connectionStatus.querySelector('.status-text');

    try {
        const response = await fetch(`${API_BASE_URL}/health/`);
        if (response.ok) {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Server connected';
        } else {
            throw new Error('Server error');
        }
    } catch (error) {
        statusDot.className = 'status-dot disconnected';
        statusText.textContent = 'Server offline - Start Django server';
    }
}

// ===== Event Listeners =====
function setupEventListeners() {
    // Upload area click
    elements.uploadArea.addEventListener('click', () => {
        elements.fileInput.click();
    });

    // File input change
    elements.fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });

    // Drag and drop
    elements.uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.add('drag-over');
    });

    elements.uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.remove('drag-over');
    });

    elements.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.remove('drag-over');
        handleFileSelect(e.dataTransfer.files[0]);
    });

    // Remove file
    elements.removeFile.addEventListener('click', () => {
        resetFileSelection();
    });

    // Analyze button
    elements.analyzeBtn.addEventListener('click', analyzeFile);

    // New analysis
    elements.newAnalysis.addEventListener('click', resetToUpload);

    // Toggle metadata
    elements.toggleMetadata.addEventListener('click', () => {
        showAllMetadata = !showAllMetadata;
        elements.toggleMetadata.textContent = showAllMetadata ? 'Show Less' : 'Show All';
        renderMetadataList();
    });

    // Download clean file
    elements.downloadClean.addEventListener('click', downloadCleanFile);

    // Share button
    elements.shareBtn.addEventListener('click', showShareModal);

    // Copy link
    elements.copyLink.addEventListener('click', copyShareLink);

    // Close modal
    elements.closeModal.addEventListener('click', () => {
        elements.shareModal.classList.add('hidden');
    });

    // Close modal on outside click
    elements.shareModal.addEventListener('click', (e) => {
        if (e.target === elements.shareModal) {
            elements.shareModal.classList.add('hidden');
        }
    });
}

// ===== File Handling =====
function handleFileSelect(file) {
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/tiff', 'application/pdf'];
    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please upload an image or PDF.');
        return;
    }

    // Validate file size (50MB max)
    if (file.size > 52428800) {
        showError('File too large. Maximum size is 50MB.');
        return;
    }

    selectedFile = file;
    hideError();

    // Update UI
    elements.uploadArea.classList.add('hidden');
    elements.selectedFileDiv.classList.remove('hidden');
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);
    elements.analyzeBtn.disabled = false;
}

function resetFileSelection() {
    selectedFile = null;
    elements.fileInput.value = '';
    elements.uploadArea.classList.remove('hidden');
    elements.selectedFileDiv.classList.add('hidden');
    elements.analyzeBtn.disabled = true;
    hideError();
}

// ===== API Calls =====
async function analyzeFile() {
    if (!selectedFile) return;

    // Show loading
    elements.uploadSection.classList.add('hidden');
    elements.loadingSection.classList.remove('hidden');

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('platform', elements.platform.value);

        const response = await fetch(`${API_BASE_URL}/analyze/`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }

        analysisData = data;
        showResults();

    } catch (error) {
        console.error('Analysis error:', error);
        elements.loadingSection.classList.add('hidden');
        elements.uploadSection.classList.remove('hidden');
        showError(error.message || 'Failed to analyze file. Is the server running?');
    }
}

async function downloadCleanFile() {
    if (!analysisData) return;

    try {
        const response = await fetch(`${API_BASE_URL}/clean/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ analysis_id: analysisData.analysis_id })
        });

        if (!response.ok) {
            throw new Error('Download failed');
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `clean_${analysisData.filename}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Download error:', error);
        showError('Failed to download clean file');
    }
}

async function showShareModal() {
    if (!analysisData) return;

    try {
        // Make the file public first
        const response = await fetch(`${API_BASE_URL}/make-public/${analysisData.analysis_id}/`, {
            method: 'POST'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate share link');
        }

        elements.shareLink.value = data.share_url;
        elements.shareModal.classList.remove('hidden');

    } catch (error) {
        console.error('Share error:', error);
        showError('Failed to generate share link');
    }
}

function copyShareLink() {
    elements.shareLink.select();
    document.execCommand('copy');

    // Visual feedback
    const originalText = elements.copyLink.textContent;
    elements.copyLink.textContent = '✓';
    setTimeout(() => {
        elements.copyLink.textContent = originalText;
    }, 1500);
}

// ===== UI Updates =====
function showResults() {
    elements.loadingSection.classList.add('hidden');
    elements.resultsSection.classList.remove('hidden');
    elements.resultsSection.classList.add('fade-in');

    // Update risk score
    const riskScore = analysisData.risk_score || 0;
    elements.riskScore.textContent = riskScore;
    elements.riskMeterFill.style.width = `${riskScore}%`;

    // Set risk level class
    let riskLevel = 'low';
    if (riskScore >= 70) riskLevel = 'high';
    else if (riskScore >= 40) riskLevel = 'medium';

    elements.riskCard.className = `risk-card ${riskLevel}`;
    elements.riskRecommendation.textContent = analysisData.risk_recommendation || '';

    // Update stats
    const metadataEntries = analysisData.metadata_entries || [];
    elements.metadataCount.textContent = metadataEntries.length;

    const highRiskCount = metadataEntries.filter(
        e => e.risk_level === 'high'
    ).length;
    elements.highRiskCount.textContent = highRiskCount;

    // Render metadata list
    renderMetadataList();
}

function renderMetadataList() {
    const entries = analysisData.metadata_entries || [];

    if (entries.length === 0) {
        elements.metadataList.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🎉</div>
        <p>No metadata detected!</p>
      </div>
    `;
        elements.toggleMetadata.classList.add('hidden');
        return;
    }

    elements.toggleMetadata.classList.remove('hidden');

    // Sort by risk level
    const sortedEntries = [...entries].sort((a, b) => {
        const riskOrder = { high: 0, medium: 1, low: 2 };
        return (riskOrder[a.risk_level] || 3) - (riskOrder[b.risk_level] || 3);
    });

    const displayEntries = showAllMetadata ? sortedEntries : sortedEntries.slice(0, 5);

    elements.metadataList.innerHTML = displayEntries.map(entry => `
    <div class="metadata-item">
      <span class="metadata-risk-badge ${entry.risk_level || 'low'}">${entry.risk_level || 'low'}</span>
      <div class="metadata-content">
        <div class="metadata-key">${escapeHtml(entry.key)}</div>
        <div class="metadata-value">${escapeHtml(truncate(entry.value, 100))}</div>
        <div class="metadata-category">${entry.category || 'other'}</div>
      </div>
    </div>
  `).join('');

    if (!showAllMetadata && entries.length > 5) {
        elements.toggleMetadata.textContent = `Show All (${entries.length})`;
    }
}

function resetToUpload() {
    analysisData = null;
    showAllMetadata = false;
    elements.toggleMetadata.textContent = 'Show All';
    elements.resultsSection.classList.add('hidden');
    elements.uploadSection.classList.remove('hidden');
    resetFileSelection();
    checkServerConnection();
}

// ===== Error Handling =====
function showError(message) {
    elements.errorMessage.textContent = `❌ ${message}`;
    elements.errorMessage.classList.remove('hidden');
}

function hideError() {
    elements.errorMessage.classList.add('hidden');
}

// ===== Utilities =====
function formatFileSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) {
        bytes /= 1024;
        i++;
    }
    return `${bytes.toFixed(2)} ${units[i]}`;
}

function truncate(str, maxLength) {
    if (!str) return '';
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
