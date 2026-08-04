const API_BASE = window.location.origin;

// Override fetch to include password header
const originalFetch = window.fetch;
window.fetch = async function() {
    let [resource, config] = arguments;
    // For relative URLs, prepend API_BASE just for checking, though usually fetch is used with full URL in this app
    const urlStr = (typeof resource === 'string') ? resource : resource.url;
    if (!urlStr || urlStr.indexOf('/static/') === -1) {
        config = config || {};
        config.headers = config.headers || {};
        config.headers['X-Admin-Password'] = localStorage.getItem('admin_password') || '';
    }
    const response = await originalFetch(resource, config);
    if (response.status === 401) {
        document.getElementById('login-overlay').style.display = 'flex';
    }
    return response;
};

async function submitAdminPassword() {
    const password = document.getElementById('admin-password').value.trim();
    localStorage.setItem('admin_password', password);
    
    const btn = document.getElementById('btn-admin-login');
    const msg = document.getElementById('admin-login-message');
    btn.disabled = true;
    
    try {
        const res = await originalFetch(`${API_BASE}/telegram/status`, {
            headers: { 'X-Admin-Password': password }
        });
        if (res.status === 200) {
            document.getElementById('login-overlay').style.display = 'none';
            msg.innerText = '';
            checkStatus();
        } else {
            msg.className = 'message error';
            msg.innerText = 'Incorrect password.';
        }
    } catch (e) {
        msg.className = 'message error';
        msg.innerText = 'Network error.';
    }
    btn.disabled = false;
}

// Initial check
if (!localStorage.getItem('admin_password')) {
    document.getElementById('login-overlay').style.display = 'flex';
} else {
    document.getElementById('login-overlay').style.display = 'none';
}

// Add event listener for enter key
document.getElementById('admin-password').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        submitAdminPassword();
    }
});


function addLog(message, type = 'info') {
    const logs = document.getElementById('logs');
    const time = new Date().toLocaleTimeString();
    
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `<span class="log-time">[${time}]</span> <span class="log-${type}">${message}</span>`;
    
    logs.appendChild(entry);
    logs.scrollTop = logs.scrollHeight;
}

function updateStatus(dotClass, text) {
    const dot = document.querySelector('#global-status .dot');
    const textSpan = document.querySelector('#global-status .text');
    
    dot.className = `dot ${dotClass}`;
    textSpan.innerText = text;
}

function unlockBotControls() {
    document.getElementById('bot-section').classList.remove('disabled-section');
    document.getElementById('auth-section').innerHTML = `
        <div class="message success" style="margin-top:0">
            ✅ Successfully connected to Telegram. Bot is ready.
        </div>
    `;
    updateStatus('active', 'Online & Ready');
}

async function checkStatus() {
    try {
        const res = await fetch(`${API_BASE}/telegram/status`);
        const data = await res.json();
        
        if (data.real_client && data.real_client.configured) {
            // Need to check if actually logged in, but we assume configured means ready for now
            // Or we check auth manually
            updateStatus('active', 'API Reached');
            addLog('Connected to backend API.', 'success');
        }
    } catch (e) {
        updateStatus('error', 'API Offline');
        addLog('Could not connect to backend API.', 'error');
    }
}

async function requestLoginCode() {
    const btn = document.getElementById('btn-send-code');
    const msg = document.getElementById('auth-message-1');
    
    btn.disabled = true;
    btn.innerText = 'Sending...';
    msg.className = 'message';
    msg.innerText = '';
    
    try {
        const res = await fetch(`${API_BASE}/telegram/auth/send-code`, { method: 'POST' });
        const data = await res.json();
        
        if (data.status === 'code_sent') {
            msg.className = 'message success';
            msg.innerText = 'Code sent to your phone!';
            addLog('Telegram login code requested.', 'info');
            
            setTimeout(() => {
                document.getElementById('step-1').classList.add('hidden');
                document.getElementById('step-2').classList.remove('hidden');
            }, 1000);
        } else {
            msg.className = 'message error';
            msg.innerText = data.message || 'Failed to send code.';
            btn.disabled = false;
            btn.innerText = 'Try Again';
        }
    } catch (e) {
        msg.className = 'message error';
        msg.innerText = 'Network error.';
        btn.disabled = false;
        btn.innerText = 'Try Again';
    }
}

async function submitLoginCode() {
    const code = document.getElementById('login-code').value;
    const btn = document.getElementById('btn-login');
    const msg = document.getElementById('auth-message-2');
    
    if (!code) return;
    
    btn.disabled = true;
    btn.innerText = 'Logging in...';
    
    try {
        const res = await fetch(`${API_BASE}/telegram/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });
        const data = await res.json();
        
        if (data.status === 'connected') {
            addLog('Successfully logged into Telegram account!', 'success');
            if (data.session_string) {
                addLog('=================================', 'info');
                addLog('IMPORTANT! COPY THIS STRING:', 'error');
                addLog(data.session_string, 'info');
                addLog('Add it to Render as TELEGRAM_SESSION_STRING so you never have to log in again.', 'error');
                addLog('=================================', 'info');
                alert("Login successful! Please check the Live Logs at the bottom of the page to copy your Session String.");
            }
            unlockBotControls();
        } else {
            msg.className = 'message error';
            msg.innerText = data.message || 'Invalid code.';
            btn.disabled = false;
            btn.innerText = 'Login';
        }
    } catch (e) {
        msg.className = 'message error';
        msg.innerText = 'Network error.';
        btn.disabled = false;
        btn.innerText = 'Login';
    }
}

async function searchGroups() {
    addLog('Searching for tech groups and attempting to join...', 'info');
    try {
        const res = await fetch(`${API_BASE}/telegram/groups/search`);
        const data = await res.json();
        
        if (data.status === 'success') {
            const count = data.joined_groups ? data.joined_groups.length : 0;
            addLog(`Found ${data.found_chats_count || 0} chats. Successfully joined ${count} new tech groups.`, 'success');
            
            if (data.failed_joins && data.failed_joins.length > 0) {
                data.failed_joins.forEach(err => {
                    addLog(`Failed to join ${err.title}: ${err.error}`, 'error');
                });
            }
        } else {
            addLog(`Error searching groups: ${data.message}`, 'error');
        }
    } catch (e) {
        addLog('Failed to trigger group search.', 'error');
    }
}

async function startAutomation() {
    addLog('Starting the daily automation cycle...', 'info');
    try {
        const res = await fetch(`${API_BASE}/automation/start`, { method: 'POST' });
        const data = await res.json();
        addLog(`Engine started. Queued ${data.queued_messages ? data.queued_messages.length : 0} actions.`, 'success');
    } catch (e) {
        addLog('Failed to start engine.', 'error');
    }
}

// --- Extract Leads Workflow ---
let currentExtractedUsers = [];

function openExtractModal() {
    document.getElementById('extract-modal').style.display = 'flex';
    document.getElementById('extract-step-1').classList.remove('hidden');
    document.getElementById('extract-step-2').classList.add('hidden');
    document.getElementById('extract-step-3').classList.add('hidden');
    fetchGroups();
}

function closeExtractModal() {
    document.getElementById('extract-modal').style.display = 'none';
}

async function fetchGroups() {
    const list = document.getElementById('groups-list');
    list.innerHTML = '<div class="message info">Loading groups...</div>';
    
    try {
        const res = await fetch(`${API_BASE}/telegram/groups`);
        const data = await res.json();
        
        if (data.status === 'success' && data.groups) {
            if (data.groups.length === 0) {
                list.innerHTML = '<div class="message info">No groups found. Try finding groups first.</div>';
                return;
            }
            
            list.innerHTML = '';
            data.groups.forEach(g => {
                const btn = document.createElement('button');
                btn.className = 'btn secondary';
                btn.style.textAlign = 'left';
                btn.innerText = g.title;
                btn.onclick = () => extractUsers(g.id, g.title);
                list.appendChild(btn);
            });
        } else {
            list.innerHTML = `<div class="message error">Error: ${data.message || 'Failed to load groups'}</div>`;
        }
    } catch (e) {
        list.innerHTML = '<div class="message error">Network error while loading groups.</div>';
    }
}

async function extractUsers(chatId, title) {
    document.getElementById('extract-step-1').classList.add('hidden');
    document.getElementById('extract-step-2').classList.remove('hidden');
    document.getElementById('extract-status').innerText = `from ${title}`;
    addLog(`Extracting users from group: ${title}...`, 'info');
    
    try {
        const res = await fetch(`${API_BASE}/telegram/groups/${chatId}/active-users`);
        const data = await res.json();
        
        if (data.status === 'success' && data.active_users) {
            currentExtractedUsers = data.active_users;
            document.getElementById('extract-step-2').classList.add('hidden');
            document.getElementById('extract-step-3').classList.remove('hidden');
            document.getElementById('extracted-count').innerText = currentExtractedUsers.length;
            addLog(`Successfully extracted ${currentExtractedUsers.length} users.`, 'success');
        } else {
            closeExtractModal();
            addLog(`Error extracting users: ${data.message}`, 'error');
        }
    } catch (e) {
        closeExtractModal();
        addLog(`Network error while extracting users.`, 'error');
    }
}

async function startCampaign() {
    if (currentExtractedUsers.length === 0) return;
    
    const btn = document.getElementById('btn-start-campaign');
    const msg = document.getElementById('campaign-message');
    btn.disabled = true;
    btn.innerText = 'Starting...';
    msg.className = 'message';
    msg.innerText = '';
    
    // Format leads for outreach API
    const leads = currentExtractedUsers.map(u => ({
        chat_id: u.username ? `@${u.username}` : u.id.toString(),
        name: u.first_name || 'there',
        context: 'the group',
        is_new: true
    }));
    
    try {
        addLog(`Sending ${leads.length} leads to the outreach engine...`, 'info');
        const res = await fetch(`${API_BASE}/outreach/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(leads)
        });
        const data = await res.json();
        
        msg.className = 'message success';
        msg.innerText = `Campaign started! ${data.queued_messages ? data.queued_messages.length : 0} messages queued.`;
        addLog(`Campaign processed. Queued: ${data.queued_messages ? data.queued_messages.length : 0}, Skipped: ${data.skipped_count || 0}.`, 'success');
        
        setTimeout(() => {
            closeExtractModal();
            btn.disabled = false;
            btn.innerText = 'Start Campaign';
            msg.innerText = '';
        }, 2000);
        
    } catch (e) {
        msg.className = 'message error';
        msg.innerText = 'Failed to start campaign.';
        btn.disabled = false;
        btn.innerText = 'Start Campaign';
        addLog(`Network error starting campaign.`, 'error');
    }
}

// Initial status check
checkStatus();

