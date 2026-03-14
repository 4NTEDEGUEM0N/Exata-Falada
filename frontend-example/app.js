let API_URL = '';

if (window.location.hostname === 'exatafalada.duckdns.org') {
    API_URL = '/api'; 
} else {
    API_URL = 'http://127.0.0.1:8000'; 
}

let currentTaskId = null;
let pollingInterval = null;

// DOM Elements
const loginContainer = document.getElementById('login-container');
const appContainer = document.getElementById('app-container');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const userDisplay = document.getElementById('user-display');
const logoutBtn = document.getElementById('logout-btn');

const uploadForm = document.getElementById('upload-form');
const pdfFileInput = document.getElementById('pdf-file');
const convertBtn = document.getElementById('convert-btn');

const progressSection = document.getElementById('progress-section');
const statusBadge = document.getElementById('status-badge');
const progressBar = document.getElementById('progress-bar');
const progressPercentage = document.getElementById('progress-percentage');
const terminalLogs = document.getElementById('terminal-logs');
const downloadContainer = document.getElementById('download-container');
const downloadBtn = document.getElementById('download-btn');

const tabBtns = document.querySelectorAll('.tab-btn');
const viewSections = document.querySelectorAll('.view-section');

const patcherForm = document.getElementById('patcher-form');
const originalFileInput = document.getElementById('original-file');
const correctionsFileInput = document.getElementById('corrections-file');
const patchBtn = document.getElementById('patch-btn');
const patcherError = document.getElementById('patcher-error');

// User Menu & Modals
const userMenuBtn = document.getElementById('user-menu-btn');
const userMenuDropdown = document.getElementById('user-menu-dropdown');
const menuMyTasks = document.getElementById('menu-my-tasks');
const menuAllTasks = document.getElementById('menu-all-tasks');
const menuAllUsers = document.getElementById('menu-all-users');
const menuCreateUser = document.getElementById('menu-create-user');

const modalOverlay = document.getElementById('modal-overlay');
const modalMyTasks = document.getElementById('modal-my-tasks');
const modalAllTasks = document.getElementById('modal-all-tasks');
const modalAllUsers = document.getElementById('modal-all-users');
const modalCreateUser = document.getElementById('modal-create-user');
const closeBtns = document.querySelectorAll('.close-modal-btn');

// Forms & Tables
const myTasksTbody = document.getElementById('my-tasks-tbody');
const allTasksTbody = document.getElementById('all-tasks-tbody');
const allUsersTbody = document.getElementById('all-users-tbody');
const createUserForm = document.getElementById('create-user-form');
const createUserMsg = document.getElementById('create-user-msg');

let isAdmin = false;

// Authentication Check
function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        fetchUserInfo(token);
    } else {
        showLogin();
    }
}

function showLogin() {
    loginContainer.classList.remove('hidden');
    appContainer.classList.add('hidden');
}

function showApp() {
    loginContainer.classList.add('hidden');
    appContainer.classList.remove('hidden');
}

// Fetch User Info
async function fetchUserInfo(token) {
    try {
        const response = await fetch(`${API_URL}/user/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            userDisplay.textContent = `Olá, ${data.username}`;
            isAdmin = data.admin === true;
            
            // Check admin status for UI rendering
            if (isAdmin) {
                document.getElementById('admin-settings').classList.remove('hidden');
                document.querySelectorAll('.admin-only').forEach(el => el.classList.remove('hidden'));
                userDisplay.innerHTML += ' <span style="color:var(--primary); font-size: 0.8em; font-weight: bold;">[ADMIN]</span>';
            } else {
                document.getElementById('admin-settings').classList.add('hidden');
                document.querySelectorAll('.admin-only').forEach(el => el.classList.add('hidden'));
            }
            
            showApp();
        } else {
            logout();
        }
    } catch (error) {
        console.error('Erro ao buscar usuário:', error);
        logout();
    }
}

// Login Submit
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    // OAuth2 expects form-data
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch(`${API_URL}/user/token`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            loginError.textContent = '';
            fetchUserInfo(data.access_token);
        } else {
            const error = await response.json();
            loginError.textContent = 'Usuário ou senha incorretos.';
        }
    } catch (error) {
        loginError.textContent = 'Erro ao conectar com o servidor.';
    }
});

function logout() {
    localStorage.removeItem('token');
    showLogin();
}

logoutBtn.addEventListener('click', logout);

// File Upload Handler
pdfFileInput.addEventListener('change', (e) => {
    const fileName = e.target.files[0]?.name;
    if (fileName) {
        document.querySelector('.file-message').textContent = fileName;
    } else {
        document.querySelector('.file-message').textContent = 'Arraste seu PDF aqui ou clique para selecionar';
    }
});

// Upload and Convert Submit
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const file = pdfFileInput.files[0];
    const pages = document.getElementById('pages').value;
    const token = localStorage.getItem('token');
    
    if (!file || !token) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('paginas', pages);

    // Append admin settings if visible and filled
    const adminSettings = document.getElementById('admin-settings');
    if (!adminSettings.classList.contains('hidden')) {
        const dpi = document.getElementById('dpi').value;
        const workers = document.getElementById('workers').value;
        const model = document.getElementById('model').value;
        const reportButton = document.getElementById('report-button').checked;

        if (dpi) formData.append('dpi', dpi);
        if (workers) formData.append('gemini_workers', workers);
        if (model) formData.append('gemini_model', model);
        formData.append('report_button', reportButton);
    }

    // Setup UI for processing
    convertBtn.disabled = true;
    convertBtn.textContent = 'Iniciando...';
    progressSection.classList.remove('hidden');
    downloadContainer.classList.add('hidden');
    terminalLogs.value = 'Iniciando upload para o servidor...\n';
    updateProgressUI(0, 'Processing', 'Processando');

    try {
        const response = await fetch(`${API_URL}/converter/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            currentTaskId = data.task_id;
            
            terminalLogs.value += `Task iniciada na nuvem. ID: ${currentTaskId}\n`;
            
            // Call polling IMMEDIATELY rather than waiting interval
            pollStatus();
            startPolling();
        } else {
            const error = await response.json();
            terminalLogs.value += `\nErro: ${error.detail}`;
            updateProgressUI(0, 'Error', 'Falhou');
            convertBtn.disabled = false;
            convertBtn.textContent = 'Iniciar Conversão';
        }
    } catch (error) {
        terminalLogs.value += '\nErro críco ao comunicar com o servidor.';
        updateProgressUI(0, 'Error', 'Erro de Rede');
        convertBtn.disabled = false;
        convertBtn.textContent = 'Iniciar Conversão';
    }
});

// Polling Task Status
function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(pollStatus, 2500); // Check every 2.5 seconds
}

async function pollStatus() {
    if (!currentTaskId) return;
    
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`${API_URL}/converter/status/${currentTaskId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            
            // Update Logs
            if (data.logs && data.logs !== terminalLogs.value) {
                terminalLogs.value = data.logs;
                terminalLogs.scrollTop = terminalLogs.scrollHeight;
            }

            // Update Progress Bar
            updateProgressUI(data.progress, data.status, (data.status === 'Completed' ? 'Concluído' : 'Processando'));

            // Handle Complete
            if (data.status === 'Completed') {
                clearInterval(pollingInterval);
                convertBtn.disabled = false;
                convertBtn.textContent = 'Nova Conversão';
                downloadContainer.classList.remove('hidden');
                
                // Setup Download Button
                downloadBtn.onclick = () => downloadFile(data.html_filename);
            } 
            // Handle Error
            else if (data.status === 'Error') {
                clearInterval(pollingInterval);
                convertBtn.disabled = false;
                convertBtn.textContent = 'Tentar Novamente';
                updateProgressUI(data.progress, 'Error', 'Erro');
            }
        }
    } catch (error) {
        console.error("Poling error", error);
    }
}

function updateProgressUI(percentage, status, statusText) {
    progressBar.style.width = `${percentage}%`;
    progressPercentage.textContent = `${percentage}%`;
    
    statusBadge.textContent = statusText;
    statusBadge.className = 'badge';
    
    if (status === 'Completed') statusBadge.classList.add('badge-completed');
    else if (status === 'Error') statusBadge.classList.add('badge-error');
    else statusBadge.classList.add('badge-processing');
}

async function downloadFile(filename) {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_URL}/converter/download/${filename}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } else {
            alert('Não foi possível baixar o arquivo.');
        }
    } catch (error) {
         alert('Erro de rede ao tentar baixar o arquivo.');
    }
}

// Tabs functionality
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all buttons and sections
        tabBtns.forEach(b => b.classList.remove('active'));
        viewSections.forEach(s => {
            if (s.classList.contains('active')) {
                s.classList.replace('active', 'hidden');
            }
        });

        // Add active class to clicked button
        btn.classList.add('active');

        // Show target section
        const targetId = btn.getAttribute('data-target');
        document.getElementById(targetId).classList.replace('hidden', 'active');
    });
});

// Patcher File Handlers
originalFileInput.addEventListener('change', (e) => {
    const fileName = e.target.files[0]?.name;
    document.getElementById('original-msg').textContent = fileName || 'Arraste seu HTML original aqui ou clique para selecionar';
});

correctionsFileInput.addEventListener('change', (e) => {
    const fileName = e.target.files[0]?.name;
    document.getElementById('corrections-msg').textContent = fileName || 'Arraste seu HTML com correções aqui ou clique para selecionar';
});

// Patcher Form Submit
patcherForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    patcherError.textContent = '';
    
    const originalFile = originalFileInput.files[0];
    const correctionsFile = correctionsFileInput.files[0];
    const token = localStorage.getItem('token');
    
    if (!originalFile || !correctionsFile || !token) return;

    const formData = new FormData();
    formData.append('original_file', originalFile);
    formData.append('corrections_file', correctionsFile);

    patchBtn.disabled = true;
    patchBtn.textContent = 'Processando...';

    try {
        const response = await fetch(`${API_URL}/patcher/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (response.ok) {
            let filename = 'arquivo_corrigido.html';
            const disposition = response.headers.get('content-disposition');
            console.log('Disposition Header:', disposition);
            
            if (disposition && disposition.indexOf('filename=') !== -1) {
                // Remove trailing quotes, spaces, and handle potentially encoded filenames
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) { 
                    filename = matches[1].replace(/['"]/g, '').trim();
                }
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            
            patchBtn.textContent = 'Processado com Sucesso!';
            setTimeout(() => {
                patchBtn.disabled = false;
                patchBtn.textContent = 'Processar e Baixar';
            }, 3000);
        } else {
            const error = await response.json();
            patcherError.textContent = error.detail || 'Erro ao processar os arquivos.';
            patchBtn.disabled = false;
            patchBtn.textContent = 'Processar e Baixar';
        }
    } catch (error) {
        patcherError.textContent = 'Erro de rede ao comunicar com o servidor.';
        patchBtn.disabled = false;
        patchBtn.textContent = 'Processar e Baixar';
    }
});

// ================= User Menu & Modal Logic ================= //

// Toggle Menu Dropdown
userMenuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    userMenuDropdown.classList.toggle('hidden');
});

// Close dropdown when clicking outside
document.addEventListener('click', () => {
    if (!userMenuDropdown.classList.contains('hidden')) {
        userMenuDropdown.classList.add('hidden');
    }
});

function openModal(modalEl) {
    modalOverlay.classList.remove('hidden');
    document.querySelectorAll('.modal-content').forEach(m => m.classList.add('hidden'));
    modalEl.classList.remove('hidden');
}

function closeModal() {
    modalOverlay.classList.add('hidden');
}

closeBtns.forEach(btn => {
    btn.addEventListener('click', closeModal);
});
modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) closeModal();
});

// Menu Actions
menuMyTasks.addEventListener('click', () => {
    openModal(modalMyTasks);
    fetchTasks('/task/me', myTasksTbody);
});

menuAllTasks.addEventListener('click', () => {
    if (isAdmin) {
        openModal(modalAllTasks);
        fetchTasks('/task/', allTasksTbody, true);
    }
});

menuAllUsers.addEventListener('click', () => {
    if (isAdmin) {
        openModal(modalAllUsers);
        fetchUsers('/user/', allUsersTbody);
    }
});

menuCreateUser.addEventListener('click', () => {
    if (isAdmin) {
        openModal(modalCreateUser);
        createUserMsg.textContent = '';
        createUserForm.reset();
    }
});

// ================= API Handlers for Tasks ================= //

async function fetchTasks(endpoint, tbodyEl, showUserId = false) {
    const token = localStorage.getItem('token');
    tbodyEl.innerHTML = '<tr><td colspan="5" style="text-align:center;">Carregando...</td></tr>';
    
    try {
        const response = await fetch(`${API_URL}${endpoint}?limit=50`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            renderTasksTable(data.tasks, tbodyEl, showUserId);
        } else {
            tbodyEl.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--danger)">Erro ao carregar tarefas</td></tr>';
        }
    } catch (error) {
        tbodyEl.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--danger)">Erro de conexão</td></tr>';
    }
}

function renderTasksTable(tasks, tbodyEl, showUserId) {
    if (!tasks || tasks.length === 0) {
        tbodyEl.innerHTML = '<tr><td colspan="5" style="text-align:center;">Nenhuma tarefa encontrada.</td></tr>';
        return;
    }

    tbodyEl.innerHTML = '';
    
    // Reverse to show newest first
    tasks.reverse().forEach(task => {
        const tr = document.createElement('tr');
        
        let statusHtml = '';
        if (task.status === 'Completed') statusHtml = '<span class="status-cell status-completed">Concluída</span>';
        else if (task.status === 'Error') statusHtml = '<span class="status-cell status-error">Erro</span>';
        else statusHtml = '<span class="status-cell status-processing">Processando</span>';

        // Check if download is possible
        const isCompleted = task.status === 'Completed' && task.html_filename;
        const downloadBtnHtml = isCompleted ? `
            <button class="action-btn success-btn btn-icon btn-download" data-filename="${task.html_filename}" title="Baixar">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            </button>
        ` : '';

        let columnsHtml = `<td>#${task.id}</td>`;
        if (showUserId) columnsHtml += `<td>${task.user_id}</td>`;
        
        columnsHtml += `
            <td>${task.pdf_filename}</td>
            <td>${statusHtml}</td>
            <td class="actions-cell">
                ${downloadBtnHtml}
                <button class="action-btn delete-btn btn-icon btn-delete" data-id="${task.id}" title="Excluir">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </td>
        `;
        
        tr.innerHTML = columnsHtml;

        // Add event listeners for buttons in this row
        if (isCompleted) {
            tr.querySelector('.btn-download').addEventListener('click', () => {
                downloadFile(task.html_filename);
            });
        }
        
        tr.querySelector('.btn-delete').addEventListener('click', async (e) => {
            const btn = e.currentTarget;
            btn.disabled = true;
            await deleteTask(task.id, tr);
        });

        tbodyEl.appendChild(tr);
    });
}

async function deleteTask(taskId, rowEl) {
    if (!confirm('Tem certeza que deseja excluir esta tarefa? O arquivo também será permanentemente apagado.')) {
        rowEl.querySelector('.btn-delete').disabled = false;
        return;
    }

    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`${API_URL}/task/delete/${taskId}`, {
            method: 'POST', // the api route is defined as POST /delete/{id}
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            rowEl.remove();
        } else {
            alert('Falha ao excluir a tarefa.');
            rowEl.querySelector('.btn-delete').disabled = false;
        }
    } catch (error) {
        alert('Erro de rede ao excluir a tarefa.');
        rowEl.querySelector('.btn-delete').disabled = false;
    }
}

// ================= API Handlers for Users ================= //

async function fetchUsers(endpoint, tbodyEl) {
    const token = localStorage.getItem('token');
    tbodyEl.innerHTML = '<tr><td colspan="4" style="text-align:center;">Carregando...</td></tr>';
    
    try {
        const response = await fetch(`${API_URL}${endpoint}?limit=50`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            // The backend mistakenly returns the user list inside `tasks` property
            renderUsersTable(data.tasks, tbodyEl);
        } else {
            tbodyEl.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--danger)">Erro ao carregar usuários</td></tr>';
        }
    } catch (error) {
        tbodyEl.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--danger)">Erro de conexão</td></tr>';
    }
}

function renderUsersTable(users, tbodyEl) {
    if (!users || users.length === 0) {
        tbodyEl.innerHTML = '<tr><td colspan="4" style="text-align:center;">Nenhum usuário encontrado.</td></tr>';
        return;
    }

    tbodyEl.innerHTML = '';
    
    users.forEach(user => {
        const tr = document.createElement('tr');
        
        let adminHtml = user.admin ? '<span class="status-cell status-completed">Sim</span>' : '<span class="status-cell">Não</span>';
        
        let columnsHtml = `
            <td>#${user.id}</td>
            <td>${user.username}</td>
            <td>${adminHtml}</td>
            <td class="actions-cell">
                <button class="action-btn delete-btn btn-icon btn-delete-user" data-id="${user.id}" title="Excluir Usuário">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </td>
        `;
        
        tr.innerHTML = columnsHtml;

        tr.querySelector('.btn-delete-user').addEventListener('click', async (e) => {
            const btn = e.currentTarget;
            btn.disabled = true;
            await deleteUser(user.id, tr);
        });

        tbodyEl.appendChild(tr);
    });
}

async function deleteUser(userId, rowEl) {
    if (!confirm('Tem certeza que deseja excluir este usuário? Esta ação não pode ser desfeita.')) {
        rowEl.querySelector('.btn-delete-user').disabled = false;
        return;
    }

    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`${API_URL}/user/delete/${userId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            rowEl.remove();
        } else {
            alert('Falha ao excluir o usuário.');
            rowEl.querySelector('.btn-delete-user').disabled = false;
        }
    } catch (error) {
        alert('Erro de rede ao excluir o usuário.');
        rowEl.querySelector('.btn-delete-user').disabled = false;
    }
}

// ================= Create User Form (Admin) ================= //

createUserForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    createUserMsg.className = 'msg-text';
    createUserMsg.textContent = 'Criando...';
    
    const username = document.getElementById('new-username').value;
    const password = document.getElementById('new-password').value;
    const adminMode = document.getElementById('new-is-admin').checked;
    const token = localStorage.getItem('token');

    try {
        const response = await fetch(`${API_URL}/user/signup`, {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                admin: adminMode
            })
        });

        if (response.ok) {
            createUserMsg.textContent = 'Usuário criado com sucesso!';
            createUserMsg.classList.add('msg-success');
            setTimeout(() => {
                closeModal();
                createUserForm.reset();
            }, 2000);
        } else {
            const data = await response.json();
            createUserMsg.textContent = data.detail || 'Erro ao criar usuário.';
            createUserMsg.classList.add('msg-error');
        }
    } catch (error) {
        createUserMsg.textContent = 'Erro de conexão.';
        createUserMsg.classList.add('msg-error');
    }
});

// Init
checkAuth();
