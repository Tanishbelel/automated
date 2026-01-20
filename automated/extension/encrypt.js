/**
 * Encryption Page Logic
 * Handles file encryption and decryption using the CryptoUtils
 */

// ===== State =====
let encryptFile = null;
let decryptFile = null;

// ===== DOM Elements =====
const elements = {
    // Tab Navigation
    tabBtns: document.querySelectorAll('.tab-btn[data-tab]'),
    tabContents: document.querySelectorAll('.tab-content'),

    // Encrypt Tab
    encryptUploadArea: document.getElementById('encryptUploadArea'),
    encryptFileInput: document.getElementById('encryptFileInput'),
    encryptSelectedFile: document.getElementById('encryptSelectedFile'),
    encryptFileName: document.getElementById('encryptFileName'),
    encryptFileSize: document.getElementById('encryptFileSize'),
    encryptRemoveFile: document.getElementById('encryptRemoveFile'),
    encryptPassword: document.getElementById('encryptPassword'),
    encryptPasswordConfirm: document.getElementById('encryptPasswordConfirm'),
    encryptBtn: document.getElementById('encryptBtn'),
    encryptError: document.getElementById('encryptError'),
    encryptSuccess: document.getElementById('encryptSuccess'),
    strengthFill: document.getElementById('strengthFill'),
    strengthText: document.getElementById('strengthText'),

    // Decrypt Tab
    decryptUploadArea: document.getElementById('decryptUploadArea'),
    decryptFileInput: document.getElementById('decryptFileInput'),
    decryptSelectedFile: document.getElementById('decryptSelectedFile'),
    decryptFileName: document.getElementById('decryptFileName'),
    decryptFileSize: document.getElementById('decryptFileSize'),
    decryptRemoveFile: document.getElementById('decryptRemoveFile'),
    decryptPassword: document.getElementById('decryptPassword'),
    decryptBtn: document.getElementById('decryptBtn'),
    decryptError: document.getElementById('decryptError'),
    decryptSuccess: document.getElementById('decryptSuccess'),

    // Loading
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText'),

    // Password toggles
    togglePasswordBtns: document.querySelectorAll('.toggle-password')
};

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    setupTabNavigation();
    setupEncryptTab();
    setupDecryptTab();
    setupPasswordToggles();
});

// ===== Tab Navigation =====
function setupTabNavigation() {
    elements.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');

            // Update button states
            elements.tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update content visibility
            elements.tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${tabId}Tab`) {
                    content.classList.add('active');
                }
            });

            // Clear messages
            hideAllMessages();
        });
    });
}

// ===== Encrypt Tab Setup =====
function setupEncryptTab() {
    // Upload area click
    elements.encryptUploadArea.addEventListener('click', () => {
        elements.encryptFileInput.click();
    });

    // File input change
    elements.encryptFileInput.addEventListener('change', (e) => {
        handleEncryptFileSelect(e.target.files[0]);
    });

    // Drag and drop
    setupDragDrop(elements.encryptUploadArea, handleEncryptFileSelect);

    // Remove file
    elements.encryptRemoveFile.addEventListener('click', () => {
        resetEncryptFile();
    });

    // Password input
    elements.encryptPassword.addEventListener('input', () => {
        updatePasswordStrength();
        validateEncryptForm();
    });

    elements.encryptPasswordConfirm.addEventListener('input', () => {
        validateEncryptForm();
    });

    // Encrypt button
    elements.encryptBtn.addEventListener('click', performEncryption);
}

// ===== Decrypt Tab Setup =====
function setupDecryptTab() {
    // Upload area click
    elements.decryptUploadArea.addEventListener('click', () => {
        elements.decryptFileInput.click();
    });

    // File input change
    elements.decryptFileInput.addEventListener('change', (e) => {
        handleDecryptFileSelect(e.target.files[0]);
    });

    // Drag and drop
    setupDragDrop(elements.decryptUploadArea, handleDecryptFileSelect);

    // Remove file
    elements.decryptRemoveFile.addEventListener('click', () => {
        resetDecryptFile();
    });

    // Password input
    elements.decryptPassword.addEventListener('input', () => {
        validateDecryptForm();
    });

    // Decrypt button
    elements.decryptBtn.addEventListener('click', performDecryption);
}

// ===== Password Toggle =====
function setupPasswordToggles() {
    elements.togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);

            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = '🙈';
            } else {
                input.type = 'password';
                btn.textContent = '👁️';
            }
        });
    });
}

// ===== Drag and Drop Setup =====
function setupDragDrop(uploadArea, handler) {
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        handler(e.dataTransfer.files[0]);
    });
}

// ===== File Handling =====
function handleEncryptFileSelect(file) {
    if (!file) return;

    // Check file size (100MB max)
    if (file.size > 104857600) {
        showError('encrypt', 'File too large. Maximum size is 100MB.');
        return;
    }

    encryptFile = file;
    hideAllMessages();

    // Update UI
    elements.encryptUploadArea.classList.add('hidden');
    elements.encryptSelectedFile.classList.remove('hidden');
    elements.encryptFileName.textContent = file.name;
    elements.encryptFileSize.textContent = formatFileSize(file.size);

    validateEncryptForm();
}

function handleDecryptFileSelect(file) {
    if (!file) return;

    // Check if it's an .enc file
    if (!file.name.endsWith('.enc')) {
        showError('decrypt', 'Please upload an encrypted (.enc) file.');
        return;
    }

    // Check file size
    if (file.size > 104857600) {
        showError('decrypt', 'File too large. Maximum size is 100MB.');
        return;
    }

    decryptFile = file;
    hideAllMessages();

    // Update UI
    elements.decryptUploadArea.classList.add('hidden');
    elements.decryptSelectedFile.classList.remove('hidden');
    elements.decryptFileName.textContent = file.name;
    elements.decryptFileSize.textContent = formatFileSize(file.size);

    validateDecryptForm();
}

function resetEncryptFile() {
    encryptFile = null;
    elements.encryptFileInput.value = '';
    elements.encryptUploadArea.classList.remove('hidden');
    elements.encryptSelectedFile.classList.add('hidden');
    elements.encryptPassword.value = '';
    elements.encryptPasswordConfirm.value = '';
    elements.strengthFill.className = 'strength-fill';
    elements.strengthText.textContent = 'Password strength';
    elements.strengthText.className = 'strength-text';
    validateEncryptForm();
    hideAllMessages();
}

function resetDecryptFile() {
    decryptFile = null;
    elements.decryptFileInput.value = '';
    elements.decryptUploadArea.classList.remove('hidden');
    elements.decryptSelectedFile.classList.add('hidden');
    elements.decryptPassword.value = '';
    validateDecryptForm();
    hideAllMessages();
}

// ===== Form Validation =====
function validateEncryptForm() {
    const password = elements.encryptPassword.value;
    const confirmPassword = elements.encryptPasswordConfirm.value;

    const isValid = encryptFile &&
        password.length >= 6 &&
        password === confirmPassword;

    elements.encryptBtn.disabled = !isValid;
}

function validateDecryptForm() {
    const password = elements.decryptPassword.value;
    const isValid = decryptFile && password.length > 0;
    elements.decryptBtn.disabled = !isValid;
}

// ===== Password Strength =====
function updatePasswordStrength() {
    const password = elements.encryptPassword.value;
    let strength = 0;
    let label = 'Password strength';

    if (password.length >= 6) strength++;
    if (password.length >= 10) strength++;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    elements.strengthFill.className = 'strength-fill';
    elements.strengthText.className = 'strength-text';

    if (password.length === 0) {
        label = 'Password strength';
    } else if (strength <= 1) {
        elements.strengthFill.classList.add('weak');
        elements.strengthText.classList.add('weak');
        label = 'Weak';
    } else if (strength <= 2) {
        elements.strengthFill.classList.add('fair');
        elements.strengthText.classList.add('fair');
        label = 'Fair';
    } else if (strength <= 3) {
        elements.strengthFill.classList.add('good');
        elements.strengthText.classList.add('good');
        label = 'Good';
    } else {
        elements.strengthFill.classList.add('strong');
        elements.strengthText.classList.add('strong');
        label = 'Strong';
    }

    elements.strengthText.textContent = label;
}

// ===== Encryption =====
async function performEncryption() {
    const password = elements.encryptPassword.value;
    const confirmPassword = elements.encryptPasswordConfirm.value;

    // Validate
    if (!encryptFile) {
        showError('encrypt', 'Please select a file to encrypt.');
        return;
    }

    if (password.length < 6) {
        showError('encrypt', 'Password must be at least 6 characters.');
        return;
    }

    if (password !== confirmPassword) {
        showError('encrypt', 'Passwords do not match.');
        return;
    }

    try {
        showLoading('Encrypting file...');

        // Read file
        const fileData = await CryptoUtils.readFileAsArrayBuffer(encryptFile);

        // Encrypt
        const encryptedData = await CryptoUtils.encrypt(fileData, password);

        // Download
        const encryptedFilename = CryptoUtils.getEncryptedFilename(encryptFile.name);
        CryptoUtils.downloadFile(encryptedData, encryptedFilename);

        hideLoading();
        showSuccess('encrypt', `File encrypted successfully! Saved as "${encryptedFilename}"`);

        // Reset form
        setTimeout(() => {
            resetEncryptFile();
        }, 3000);

    } catch (error) {
        hideLoading();
        console.error('Encryption error:', error);
        showError('encrypt', 'Encryption failed. Please try again.');
    }
}

// ===== Decryption =====
async function performDecryption() {
    const password = elements.decryptPassword.value;

    // Validate
    if (!decryptFile) {
        showError('decrypt', 'Please select an encrypted file.');
        return;
    }

    if (!password) {
        showError('decrypt', 'Please enter the password.');
        return;
    }

    try {
        showLoading('Decrypting file...');

        // Read file
        const encryptedData = await CryptoUtils.readFileAsArrayBuffer(decryptFile);

        // Decrypt
        const decryptedData = await CryptoUtils.decrypt(encryptedData, password);

        // Get original filename
        const originalFilename = CryptoUtils.getOriginalFilename(decryptFile.name);

        // Download
        CryptoUtils.downloadFile(decryptedData, originalFilename);

        hideLoading();
        showSuccess('decrypt', `File decrypted successfully! Saved as "${originalFilename}"`);

        // Reset form
        setTimeout(() => {
            resetDecryptFile();
        }, 3000);

    } catch (error) {
        hideLoading();
        console.error('Decryption error:', error);
        showError('decrypt', 'Decryption failed. Wrong password or corrupted file.');
    }
}

// ===== UI Helpers =====
function showLoading(text) {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
}

function showError(tab, message) {
    const errorEl = tab === 'encrypt' ? elements.encryptError : elements.decryptError;
    errorEl.textContent = `❌ ${message}`;
    errorEl.classList.remove('hidden');
}

function showSuccess(tab, message) {
    const successEl = tab === 'encrypt' ? elements.encryptSuccess : elements.decryptSuccess;
    successEl.textContent = `✅ ${message}`;
    successEl.classList.remove('hidden');
}

function hideAllMessages() {
    elements.encryptError.classList.add('hidden');
    elements.encryptSuccess.classList.add('hidden');
    elements.decryptError.classList.add('hidden');
    elements.decryptSuccess.classList.add('hidden');
}

function formatFileSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) {
        bytes /= 1024;
        i++;
    }
    return `${bytes.toFixed(2)} ${units[i]}`;
}
