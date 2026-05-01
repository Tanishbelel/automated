// redact.js — external script for redact.html (required by Chrome MV3 CSP)

const API = 'http://127.0.0.1:8000/api';

let selectedFile = null;

// DOM refs
const uploadArea     = document.getElementById('uploadArea');
const fileInput      = document.getElementById('fileInput');
const fileSelected   = document.getElementById('fileSelected');
const fileNameEl     = document.getElementById('fileName');
const fileSizeEl     = document.getElementById('fileSize');
const removeFileBtn  = document.getElementById('removeFileBtn');
const redactBtn      = document.getElementById('redactBtn');
const loadingSection = document.getElementById('loadingSection');
const resultBox      = document.getElementById('redactResult');
const redactSummary  = document.getElementById('redactSummary');
const redactTags     = document.getElementById('redactTags');
const errorDiv       = document.getElementById('redactError');

// ── Nav buttons ───────────────────────────────────────────────────────────
document.getElementById('analyzeNavBtn').addEventListener('click', () => {
    window.location.href = 'popup.html';
});
document.getElementById('dashboardNavBtn').addEventListener('click', () => {
    window.location.href = 'dashboard.html';
});
document.getElementById('encryptNavBtn').addEventListener('click', () => {
    window.location.href = 'encrypt.html';
});
document.getElementById('decryptNavBtn').addEventListener('click', () => {
    window.location.href = 'encrypt.html?tab=decrypt';
});
// redactNavBtn — already on this page, do nothing

// ── Upload — same pattern as popup.js (confirmed working) ────────────────
uploadArea.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) handleFile(file);
});

// Drag & drop
['dragenter', 'dragover'].forEach(ev =>
    uploadArea.addEventListener(ev, e => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--accent-primary)';
    })
);
['dragleave', 'drop'].forEach(ev =>
    uploadArea.addEventListener(ev, e => {
        e.preventDefault();
        uploadArea.style.borderColor = '';
    })
);
uploadArea.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
});

function handleFile(file) {
    if (file.size > 20 * 1024 * 1024) {
        showError('File too large. Maximum size is 20 MB.');
        return;
    }
    selectedFile = file;
    uploadArea.classList.add('hidden');
    fileSelected.classList.remove('hidden');
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatSize(file.size);
    redactBtn.disabled = false;
    resultBox.classList.add('hidden');
    hideError();
}

removeFileBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    uploadArea.classList.remove('hidden');
    fileSelected.classList.add('hidden');
    redactBtn.disabled = true;
    resultBox.classList.add('hidden');
    hideError();
});

// ── Redact button ─────────────────────────────────────────────────────────
redactBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    hideError();
    resultBox.classList.add('hidden');
    loadingSection.classList.remove('hidden');
    redactBtn.disabled = true;
    redactBtn.textContent = 'Redacting…';

    const fd = new FormData();
    fd.append('file', selectedFile);

    try {
        const resp = await fetch(`${API}/redact/`, { method: 'POST', body: fd });

        if (!resp.ok) {
            let msg = 'Redaction failed.';
            try { msg = (await resp.json()).error || msg; } catch (_) {}
            throw new Error(msg);
        }

        const labelsRaw = resp.headers.get('X-Redacted-Fields') || '[]';
        let labels = [];
        try { labels = JSON.parse(labelsRaw); } catch (_) {}

        // Download the redacted file
        const blob = await resp.blob();
        const ext  = selectedFile.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'png';
        const name = selectedFile.name.replace(/\.[^.]+$/, `_redacted.${ext}`);
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href = url;
        a.download = name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        if (labels.length > 0) {
            redactSummary.textContent = `${labels.length} type(s) of sensitive data found and redacted.`;
            redactTags.innerHTML = labels.map(l =>
                `<span class="redact-tag tag-${l}">${l}</span>`
            ).join('');
        } else {
            redactSummary.textContent = 'No sensitive data detected — file returned unchanged.';
            redactTags.innerHTML = '';
        }
        resultBox.classList.remove('hidden');

    } catch (err) {
        showError(err.message || 'An unexpected error occurred.');
    } finally {
        loadingSection.classList.add('hidden');
        redactBtn.disabled = false;
        redactBtn.textContent = 'Redact & Download';
    }
});

// ── Helpers ───────────────────────────────────────────────────────────────
function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}
function showError(msg) {
    errorDiv.textContent = '⚠ ' + msg;
    errorDiv.classList.remove('hidden');
}
function hideError() {
    errorDiv.classList.add('hidden');
}
