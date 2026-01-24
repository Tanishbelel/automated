const API = "http://127.0.0.1:8000/api";
const token = localStorage.getItem("token");

if (!token) {
    window.location.href = "auth.html";
}

const authHeaders = {
    "Authorization": `Token ${token}`,
    "Content-Type": "application/json"
};

let fileHistory = [];
let currentFilter = 'all';

// Load profile data
async function loadProfile() {
    try {
        const response = await fetch(`${API}/auth/profile/`, {
            headers: authHeaders
        });
        
        if (!response.ok) throw new Error("Failed to load profile");
        
        const user = await response.json();
        
        document.getElementById("profileName").textContent = 
            user.first_name && user.last_name 
                ? `${user.first_name} ${user.last_name}` 
                : user.username;
        
        document.getElementById("profileEmail").textContent = user.email;
        document.getElementById("username").textContent = user.username;
        
        const joined = new Date(user.date_joined);
        document.getElementById("memberSince").textContent = joined.toLocaleDateString();
        
        // Set avatar initial
        const initial = (user.first_name?.[0] || user.username[0]).toUpperCase();
        document.getElementById("avatar").textContent = initial;
        
        // Populate update form
        document.getElementById("updateEmail").value = user.email;
        document.getElementById("updateFirstName").value = user.first_name || "";
        document.getElementById("updateLastName").value = user.last_name || "";
        
    } catch (error) {
        console.error(error);
        if (error.message.includes("401") || error.message.includes("403")) {
            localStorage.removeItem("token");
            window.location.href = "auth.html";
        }
    }
}

// Load file history
async function loadFileHistory() {
    try {
        const response = await fetch(`${API}/analyses/`, {
            headers: authHeaders
        });
        
        if (!response.ok) throw new Error("Failed to load history");
        
        const data = await response.json();
        fileHistory = data.results || data;
        
        // Update stats
        document.getElementById("totalFiles").textContent = fileHistory.length;
        
        const totalMetadata = fileHistory.reduce((sum, file) => sum + (file.metadata_count || 0), 0);
        document.getElementById("totalMetadata").textContent = totalMetadata;
        
        renderHistory();
        
    } catch (error) {
        console.error('History error:', error);
        document.getElementById("historyContent").innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">❌</div>
                <h3>Failed to load history</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// Render history
function renderHistory() {
    let filteredFiles = fileHistory;
    
    if (currentFilter !== 'all') {
        filteredFiles = fileHistory.filter(file => {
            if (currentFilter === 'low') return file.risk_score < 40;
            if (currentFilter === 'medium') return file.risk_score >= 40 && file.risk_score < 70;
            if (currentFilter === 'high') return file.risk_score >= 70;
            return true;
        });
    }
    
    if (filteredFiles.length === 0) {
        document.getElementById("historyContent").innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <h3>No files found</h3>
                <p>Upload and analyze files to see them here</p>
            </div>
        `;
        return;
    }
    
    const grid = document.createElement('div');
    grid.className = 'history-grid';
    
    filteredFiles.forEach(file => {
        const riskLevel = file.risk_score >= 70 ? 'high' : file.risk_score >= 40 ? 'medium' : 'low';
        const fileIcon = getFileIcon(file.file_type);
        const date = new Date(file.created_at).toLocaleString();
        
        const card = document.createElement('div');
        card.className = 'history-item';
        card.innerHTML = `
            <div class="history-header">
                <div class="file-icon-large">${fileIcon}</div>
                <div class="history-info">
                    <h4>${escapeHtml(file.original_filename)}</h4>
                    <div class="history-date">${date}</div>
                </div>
            </div>
            
            <span class="risk-badge risk-${riskLevel}">
  ${riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)} Risk
</span>
            
            <div class="stats-row">
                <div class="stat-mini">
                    <div class="label">Risk Score</div>
                    <div class="value">${file.risk_score || 0}</div>
                </div>
                <div class="stat-mini">
                    <div class="label">Metadata</div>
                    <div class="value">${file.metadata_count || 0}</div>
                </div>
            </div>
            
            <div class="history-actions">
                <button class="btn-secondary btn-small">Compare</button>
<button class="btn-secondary btn-small">Download</button>
            </div>
        `;
        
        grid.appendChild(card);
    });
    
    document.getElementById("historyContent").innerHTML = '';
    document.getElementById("historyContent").appendChild(grid);
}

// View comparison
async function viewComparison(fileId) {
    const modal = document.getElementById("comparisonModal");
    const content = document.getElementById("comparisonContent");
    
    modal.classList.add("show");
    content.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading comparison...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${API}/analyses/${fileId}/`, {
            headers: authHeaders
        });
        
        if (!response.ok) throw new Error("Failed to load file details");
        
        const file = await response.json();
        const metadata = file.metadata_entries || [];
        
        // Calculate stats
        const beforeCount = metadata.length;
        const afterCount = 0; // All metadata removed
        const removedCount = beforeCount;
        
        content.innerHTML = `
            <div style="background:#f8fafc;padding:20px;border-radius:18px;margin-bottom:24px;border:1px solid #e5e7eb">
                <h4 style="margin-bottom:15px;color:#0f172a;font-weight:400">
📊 Summary</h4>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:15px">
                    <div style="text-align:center">
                        <div style="font-size:2rem;font-weight:700;color:#0054AE
">${beforeCount}</div>
                        <div style="font-size:.8rem;color:#94a3b8">Before</div>
                    </div>
                    <div style="text-align:center">
                        <div style="font-size:2rem;font-weight:700;color:#0054AE
">${removedCount}</div>
                        <div style="font-size:.8rem;color:#94a3b8">Removed</div>
                    </div>
                    <div style="text-align:center">
                        <div style="font-size:2rem;font-weight:700;color:#0054AE
">${afterCount}</div>
                        <div style="font-size:.8rem;color:#94a3b8">After</div>
                    </div>
                </div>
            </div>
            
            <div class="comparison-grid">
                <div class="comparison-column">
                    <h4>📝 Before (${beforeCount} items)</h4>
                    <div class="metadata-list">
                        ${metadata.map(item => `
                            <div class="metadata-item">
                                <div class="metadata-key">${escapeHtml(item.key)}</div>
                                <div class="metadata-value">${escapeHtml(truncate(item.value, 100))}</div>
                                <span class="metadata-category">${item.category}</span>
                                <span class="risk-badge risk-${item.risk_level}" style="margin-left:8px">${item.risk_level}</span>
                            </div>
                        `).join('') || '<p style="text-align:center;color:#64748b;padding:20px">No metadata found</p>'}
                    </div>
                </div>
                
                <div class="comparison-column">
                    <h4>✨ After (${afterCount} items)</h4>
                    <div class="metadata-list">
                        <div class="empty-state">
                            <div class="empty-state-icon">✅</div>
                            <p style="color:#0054AE;font-weight:500">
All metadata removed!</p>
                            <p style="font-size:.9rem">Your file is now clean and safe to share</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Comparison error:', error);
        content.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">❌</div>
                <p>Failed to load comparison</p>
                <p style="font-size:.9rem;margin-top:10px">${error.message}</p>
            </div>
        `;
    }
}

// Download clean file
async function downloadClean(fileId) {
    try {
        const response = await fetch(`${API}/analyses/${fileId}/download_clean/`, {
            headers: { "Authorization": `Token ${token}` }
        });
        
        if (!response.ok) throw new Error("Download failed");
        
        const blob = await response.blob();
        const file = fileHistory.find(f => f.id === fileId);
        const filename = file ? `clean_${file.original_filename}` : 'clean_file';
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Download error:', error);
        alert('Failed to download file: ' + error.message);
    }
}

// Filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        renderHistory();
    });
});

// Refresh history
document.getElementById('refreshHistory').addEventListener('click', loadFileHistory);

// Close comparison modal
document.getElementById('closeComparison').addEventListener('click', () => {
    document.getElementById('comparisonModal').classList.remove('show');
});

// Update profile
document.getElementById("updateForm").onsubmit = async (e) => {
    e.preventDefault();
    const msgDiv = document.getElementById("updateMessage");
    msgDiv.innerHTML = "";
    
    const data = {
        email: document.getElementById("updateEmail").value,
        first_name: document.getElementById("updateFirstName").value,
        last_name: document.getElementById("updateLastName").value
    };
    
    try {
        const response = await fetch(`${API}/auth/profile/update/`, {
            method: "PATCH",
            headers: authHeaders,
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            const errors = Object.values(result).flat().join(", ");
            throw new Error(errors);
        }
        
        msgDiv.innerHTML = '<div class="success">✅ Profile updated successfully!</div>';
        loadProfile();
        
    } catch (error) {
        msgDiv.innerHTML = `<div class="error">❌ ${error.message}</div>`;
    }
};

// Change password
document.getElementById("passwordForm").onsubmit = async (e) => {
    e.preventDefault();
    const msgDiv = document.getElementById("passwordMessage");
    msgDiv.innerHTML = "";
    
    const oldPassword = document.getElementById("oldPassword").value;
    const newPassword = document.getElementById("newPassword").value;
    const newPassword2 = document.getElementById("newPassword2").value;
    
    if (newPassword !== newPassword2) {
        msgDiv.innerHTML = '<div class="error">❌ New passwords do not match!</div>';
        return;
    }
    
    try {
        const response = await fetch(`${API}/auth/change-password/`, {
            method: "POST",
            headers: authHeaders,
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword,
                new_password2: newPassword2
            })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            const errors = Object.values(result).flat().join(", ");
            throw new Error(errors);
        }
        
        localStorage.setItem("token", result.token);
        
        msgDiv.innerHTML = '<div class="success">✅ Password changed successfully!</div>';
        document.getElementById("passwordForm").reset();
        
    } catch (error) {
        msgDiv.innerHTML = `<div class="error">❌ ${error.message}</div>`;
    }
};

// Logout
document.getElementById("logoutLink").onclick = async (e) => {
    e.preventDefault();
    
    try {
        await fetch(`${API}/auth/logout/`, {
            method: "POST",
            headers: authHeaders
        });
    } catch (error) {
        console.error(error);
    }
    
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "auth.html";
};

// Delete account modal
const deleteModal = document.getElementById("deleteModal");
document.getElementById("deleteAccountBtn").onclick = () => {
    deleteModal.classList.add("show");
};
document.getElementById("cancelDelete").onclick = () => {
    deleteModal.classList.remove("show");
    document.getElementById("deletePassword").value = "";
    document.getElementById("deleteMessage").innerHTML = "";
};

document.getElementById("confirmDelete").onclick = async () => {
    const password = document.getElementById("deletePassword").value;
    const msgDiv = document.getElementById("deleteMessage");
    msgDiv.innerHTML = "";
    
    if (!password) {
        msgDiv.innerHTML = '<div class="error">❌ Please enter your password</div>';
        return;
    }
    
    try {
        const response = await fetch(`${API}/auth/delete-account/`, {
            method: "DELETE",
            headers: authHeaders,
            body: JSON.stringify({ password })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || "Failed to delete account");
        }
        
        msgDiv.innerHTML = '<div class="success">✅ Account deleted. Redirecting...</div>';
        
        setTimeout(() => {
            localStorage.clear();
            window.location.href = "auth.html";
        }, 2000);
        
    } catch (error) {
        msgDiv.innerHTML = `<div class="error">❌ ${error.message}</div>`;
    }
};

// Utility functions
function getFileIcon(fileType) {
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('image')) return '🖼️';
    return '📁';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(str, maxLength) {
    if (!str) return '';
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
}

// Close modals on outside click
document.getElementById('comparisonModal').addEventListener('click', (e) => {
    if (e.target.id === 'comparisonModal') {
        e.target.classList.remove('show');
    }
});

document.getElementById('deleteModal').addEventListener('click', (e) => {
    if (e.target.id === 'deleteModal') {
        e.target.classList.remove('show');
    }
});

// Initialize
loadProfile();
loadFileHistory();