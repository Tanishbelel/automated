// -- darsh: Extension auth JavaScript for login and signup

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// DOM Elements
const loginTab = document.getElementById('loginTab');
const signupTab = document.getElementById('signupTab');
const loginContent = document.getElementById('loginContent');
const signupContent = document.getElementById('signupContent');
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const loginMessage = document.getElementById('loginMessage');
const signupMessage = document.getElementById('signupMessage');

// Tab switching
loginTab.addEventListener('click', () => {
    loginTab.classList.add('active');
    signupTab.classList.remove('active');
    loginContent.classList.add('active');
    signupContent.classList.remove('active');
});

signupTab.addEventListener('click', () => {
    signupTab.classList.add('active');
    loginTab.classList.remove('active');
    signupContent.classList.add('active');
    loginContent.classList.remove('active');
});

// Login Form
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    if (!username || !password) {
        showMessage(loginMessage, 'Please enter username and password', 'error');
        return;
    }

    const loginBtn = document.getElementById('loginBtn');
    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Store auth data
            chrome.storage.local.set({
                authToken: data.token,
                currentUser: data.user
            }, () => {
                showMessage(loginMessage, 'Login successful! Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = 'popup.html';
                }, 1000);
            });
        } else {
            showMessage(loginMessage, data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage(loginMessage, 'Connection error. Please try again.', 'error');
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login';
    }
});

// Signup Form
signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('signupUsername').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('signupConfirmPassword').value;

    // Validation
    if (!username || !email || !password || !confirmPassword) {
        showMessage(signupMessage, 'Please fill in all fields', 'error');
        return;
    }

    if (password !== confirmPassword) {
        showMessage(signupMessage, 'Passwords do not match', 'error');
        return;
    }

    if (password.length < 6) {
        showMessage(signupMessage, 'Password must be at least 6 characters', 'error');
        return;
    }

    const signupBtn = document.getElementById('signupBtn');
    signupBtn.disabled = true;
    signupBtn.textContent = 'Creating account...';

    try {
        const response = await fetch(`${API_BASE_URL}/auth/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                email,
                password,
                password2: confirmPassword
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Auto-login after signup
            chrome.storage.local.set({
                authToken: data.token,
                currentUser: data.user
            }, () => {
                showMessage(signupMessage, 'Account created! Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = 'popup.html';
                }, 1000);
            });
        } else {
            const errorMsg = data.username?.[0] || data.email?.[0] || data.error || 'Signup failed';
            showMessage(signupMessage, errorMsg, 'error');
        }
    } catch (error) {
        showMessage(signupMessage, 'Connection error. Please try again.', 'error');
    } finally {
        signupBtn.disabled = false;
        signupBtn.textContent = 'Sign Up';
    }
});

// Helper function
function showMessage(element, text, type) {
    element.textContent = text;
    element.className = `auth-message ${type}`;
    element.classList.remove('hidden');

    if (type === 'success') {
        setTimeout(() => {
            element.classList.add('hidden');
        }, 3000);
    }
}
