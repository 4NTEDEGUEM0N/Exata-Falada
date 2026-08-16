let API_URL = '';

if (window.location.hostname === '127.0.0.1') {
    API_URL = 'http://127.0.0.1:8000'; 
} else {
    API_URL = '/api-v2'; 
}

let currentTaskId = null;
let currentUserId = null;
let pollingInterval = null;

function formatDate(isoString) {
    if (!isoString) return '-';
    const date = new Date(isoString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
}

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
            currentUserId = data.id;
            userDisplay.textContent = `Olá, ${data.username}`;
            isAdmin = data.admin === true;
            
            // Check admin status for UI rendering
            if (isAdmin) {
                document.getElementById('admin-settings').classList.remove('hidden');
                document.querySelectorAll('.admin-only').forEach(el => el.classList.remove('hidden'));
                document.getElementById('library-admin-view').classList.remove('hidden');
                document.getElementById('library-user-view').classList.add('hidden');
                userDisplay.innerHTML += ' <span style="color:var(--primary); font-size: 0.8em; font-weight: bold;">[ADMIN]</span>';
                
                // Fetch models since the user is an admin
                fetchModels(token);
            } else {
                document.getElementById('admin-settings').classList.add('hidden');
                document.querySelectorAll('.admin-only').forEach(el => el.classList.add('hidden'));
                document.getElementById('library-admin-view').classList.add('hidden');
                document.getElementById('library-user-view').classList.remove('hidden');
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

// Fetch Available Models
async function fetchModels(token) {
    try {
        const response = await fetch(`${API_URL}/converter/models`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const modelSelect = document.getElementById('model');
            modelSelect.innerHTML = ''; // Clear loading state
            
            // Add default option placeholder
            const defaultOption = document.createElement('option');
            defaultOption.value = "";
            defaultOption.disabled = true;
            defaultOption.selected = true;
            defaultOption.textContent = `Padrão: ${data.default_model}`;
            modelSelect.appendChild(defaultOption);

            // Add all available models
            data.available_models.forEach(modelName => {
                const option = document.createElement('option');
                option.value = modelName;
                option.textContent = modelName;
                modelSelect.appendChild(option);
            });
        } else {
            console.error("Erro ao buscar modelos disponíveis");
        }
    } catch (error) {
        console.error("Erro de rede ao buscar modelos:", error);
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
        if (workers) formData.append('workers', workers);
        if (model) formData.append('ai_model', model);
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
            let statusText = 'Processando';
            if (data.status === 'Completed') statusText = 'Concluído';
            else if (data.status === 'Completed with errors') statusText = 'Concluído c/ erros';
            else if (data.status === 'Error') statusText = 'Falhou';
            else statusText = 'Processando';

            updateProgressUI(data.progress, data.status, statusText);

            // Handle Complete
            if (data.status === 'Completed' || data.status === 'Completed with errors') {
                clearInterval(pollingInterval);
                convertBtn.disabled = false;
                convertBtn.textContent = 'Nova Conversão';
                downloadContainer.classList.remove('hidden');
                
                // Setup Download Button
                downloadBtn.onclick = () => downloadFile(currentTaskId);
            } 
            // Handle Error
            else if (data.status === 'Error') {
                clearInterval(pollingInterval);
                convertBtn.disabled = false;
                convertBtn.textContent = 'Tentar Novamente';
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
    else if (status === 'Completed with errors') {
        statusBadge.classList.add('badge-completed');
        statusBadge.style.backgroundColor = '#f39c12'; // Laranja para aviso
        statusBadge.style.color = '#fff';
    }
    else if (status === 'Error') statusBadge.classList.add('badge-error');
    else {
        statusBadge.classList.add('badge-processing');
        statusBadge.style.backgroundColor = ''; // Reset
        statusBadge.style.color = '';
    }
}

async function downloadFile(taskId) {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_URL}/converter/download/${taskId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            let filename = `arquivo_convertido_${taskId}.html`;
            const disposition = response.headers.get('content-disposition');
            if (disposition && disposition.indexOf('filename=') !== -1) {
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

        if (targetId === 'view-library') {
            if (isAdmin) {
                fetchBooks('/library/', document.getElementById('all-books-tbody'), true, 1, 'all-books-pagination');
            } else {
                fetchBooks(`/library/books/${currentUserId}`, document.getElementById('my-books-tbody'), false, 1, 'my-books-pagination');
            }
        }
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
    fetchTasks(`/task/user/${currentUserId}`, myTasksTbody, false, 1, 'my-tasks-pagination');
});

menuAllTasks.addEventListener('click', () => {
    if (isAdmin) {
        document.getElementById('modal-all-tasks-title').innerHTML = 'Todas as Tarefas do Sistema <span class="admin-badge">Admin</span>';
        openModal(modalAllTasks);
        fetchTasks('/task/', allTasksTbody, true, 1, 'all-tasks-pagination');
    }
});

menuAllUsers.addEventListener('click', () => {
    if (isAdmin) {
        openModal(modalAllUsers);
        fetchUsers('/user/', allUsersTbody, 1, 'all-users-pagination');
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

function renderPaginationControls(data, containerId, fetchCallback) {
    if (!containerId) return;
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (data.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = `
        <button class="secondary-btn" id="${containerId}-prev" ${data.page <= 1 ? 'disabled' : ''}>Anterior</button>
        <span class="pagination-info">Página ${data.page} de ${data.total_pages}</span>
        <button class="secondary-btn" id="${containerId}-next" ${data.page >= data.total_pages ? 'disabled' : ''}>Próxima</button>
    `;

    if (data.page > 1) {
        document.getElementById(`${containerId}-prev`).addEventListener('click', () => fetchCallback(data.page - 1));
    }
    if (data.page < data.total_pages) {
        document.getElementById(`${containerId}-next`).addEventListener('click', () => fetchCallback(data.page + 1));
    }
}

async function fetchTasks(endpoint, tbodyEl, showUserId = false, page = 1, paginationContainerId = null) {
    const token = localStorage.getItem('token');
    tbodyEl.innerHTML = '<tr><td colspan="5" style="text-align:center;">Carregando...</td></tr>';
    
    const baseEndpoint = endpoint.split('?')[0];

    try {
        const response = await fetch(`${API_URL}${baseEndpoint}?page=${page}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            renderTasksTable(data.tasks, tbodyEl, showUserId);
            renderPaginationControls(data, paginationContainerId, (newPage) => fetchTasks(baseEndpoint, tbodyEl, showUserId, newPage, paginationContainerId));
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
    
    tasks.forEach(task => {
        const tr = document.createElement('tr');
        
        let statusHtml = '';
        if (task.status === 'Completed') statusHtml = '<span class="status-cell status-completed">Concluída</span>';
        else if (task.status === 'Completed with errors') statusHtml = '<span class="status-cell status-completed" style="background-color: #f39c12; color: #fff;">Concluída c/ Erros</span>';
        else if (task.status === 'Error') statusHtml = '<span class="status-cell status-error">Erro</span>';
        else statusHtml = '<span class="status-cell status-processing">Processando</span>';

        // Check if download is possible
        const isCompleted = (task.status === 'Completed' || task.status === 'Completed with errors') && task.html_filename;
        const downloadBtnHtml = isCompleted ? `
            <button class="action-btn success-btn btn-icon btn-download" data-taskid="${task.id}" title="Baixar">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            </button>
        ` : '';
        
        const infoBtnHtml = `
            <button class="action-btn primary-btn btn-icon btn-info" data-id="${task.id}" title="Ver Logs">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
            </button>
        `;

        let columnsHtml = `<td>#${task.id}</td>`;
        if (showUserId) columnsHtml += `<td>${task.user_id}</td>`;
        
        columnsHtml += `
            <td class="col-name" title="${task.pdf_filename}">${task.pdf_filename}</td>
            <td class="col-date">${formatDate(task.created_at)}</td>
            <td>${statusHtml}</td>
            <td class="actions-cell">
                ${infoBtnHtml}
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
                downloadFile(task.id);
            });
        }
        
        tr.querySelector('.btn-info').addEventListener('click', async () => {
             const titleEl = document.getElementById('modal-task-logs-title');
             const logsEl = document.getElementById('modal-terminal-logs');
             titleEl.textContent = `Logs da Tarefa #${task.id}`;
             logsEl.value = 'Buscando logs...';
             openModal(document.getElementById('modal-task-logs'));
             
             const token = localStorage.getItem('token');
             try {
                 const response = await fetch(`${API_URL}/converter/status/${task.id}`, {
                     headers: { 'Authorization': `Bearer ${token}` }
                 });
                 if (response.ok) {
                     const detail = await response.json();
                     logsEl.value = detail.logs || 'Nenhum log registrado para esta tarefa.';
                     logsEl.scrollTop = logsEl.scrollHeight;
                 } else {
                     logsEl.value = 'Erro ao carregar os logs da tarefa.';
                 }
             } catch (error) {
                 logsEl.value = 'Erro de rede ao buscar os logs.';
             }
        });

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

async function fetchUsers(endpoint, tbodyEl, page = 1, paginationContainerId = null) {
    const token = localStorage.getItem('token');
    tbodyEl.innerHTML = '<tr><td colspan="4" style="text-align:center;">Carregando...</td></tr>';
    
    const baseEndpoint = endpoint.split('?')[0];

    try {
        const response = await fetch(`${API_URL}${baseEndpoint}?page=${page}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            renderUsersTable(data.users, tbodyEl);
            renderPaginationControls(data, paginationContainerId, (newPage) => fetchUsers(baseEndpoint, tbodyEl, newPage, paginationContainerId));
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
                <button class="action-btn success-btn btn-icon btn-user-books" data-id="${user.id}" title="Listar Livros">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
                </button>
                <button class="action-btn primary-btn btn-icon btn-user-tasks" data-id="${user.id}" title="Ver Tarefas">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                </button>
                <button class="action-btn delete-btn btn-icon btn-delete-user" data-id="${user.id}" title="Excluir Usuário">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </td>
        `;
        
        tr.innerHTML = columnsHtml;

        tr.querySelector('.btn-user-books').addEventListener('click', () => {
            document.getElementById('current-user-books-id').value = user.id;
            openModal(document.getElementById('modal-user-books'));
            fetchUserBooks(user.id, 1);
        });

        tr.querySelector('.btn-user-tasks').addEventListener('click', () => {
            document.getElementById('modal-all-tasks-title').innerHTML = `Tarefas do Usuário #${user.id} - ${user.username}`;
            openModal(modalAllTasks);
            fetchTasks(`/task/user/${user.id}`, allTasksTbody, true, 1, 'all-tasks-pagination');
        });

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

// ================= Library Handlers ================= //

async function fetchBooks(endpoint, tbodyEl, isAdminView, page = 1, paginationContainerId = null) {
    const token = localStorage.getItem('token');
    tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center;">Carregando...</td></tr>';
    
    try {
        const response = await fetch(`${API_URL}${endpoint.split('?')[0]}?page=${page}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            renderBooksTable(data.books, tbodyEl, isAdminView);
            renderPaginationControls(data, paginationContainerId, (newPage) => fetchBooks(endpoint, tbodyEl, isAdminView, newPage, paginationContainerId));
        } else {
            tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--danger)">Erro ao carregar livros</td></tr>';
        }
    } catch (error) {
        tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--danger)">Erro de conexão</td></tr>';
    }
}

function renderBooksTable(books, tbodyEl, isAdminView) {
    if (!books || books.length === 0) {
        tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center;">Nenhum livro encontrado.</td></tr>';
        return;
    }
    tbodyEl.innerHTML = '';
    books.forEach(book => {
        const tr = document.createElement('tr');
        let actionsHtml = `
            <button class="action-btn success-btn btn-icon btn-open-book" data-id="${book.id}" title="Abrir Livro">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>
            </button>
        `;
        if (isAdminView) {
            actionsHtml += `
                <button class="action-btn primary-btn btn-icon btn-book-users" data-id="${book.id}" title="Gerenciar Usuários">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                </button>
                <button class="action-btn delete-btn btn-icon btn-delete-book" data-id="${book.id}" title="Excluir Livro">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            `;
        }
        
        tr.innerHTML = `
            <td>#${book.id}</td>
            <td class="col-name" title="${book.filename}">${book.filename}</td>
            <td class="col-date">${formatDate(book.created_at)}</td>
            <td class="actions-cell">${actionsHtml}</td>
        `;
        
        if (isAdminView) {
            tr.querySelector('.btn-book-users').addEventListener('click', () => {
                document.getElementById('current-book-id').value = book.id;
                openModal(document.getElementById('modal-book-users'));
                fetchBookUsers(book.id, 1);
            });
            tr.querySelector('.btn-delete-book').addEventListener('click', async () => {
                if(confirm('Tem certeza que deseja excluir este livro?')) {
                    const token = localStorage.getItem('token');
                    await fetch(`${API_URL}/library/delete/${book.id}`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
                    fetchBooks('/library/', document.getElementById('all-books-tbody'), true, 1, 'all-books-pagination');
                }
            });
        }
        
        tr.querySelector('.btn-open-book').addEventListener('click', async () => {
            const token = localStorage.getItem('token');
            const btn = tr.querySelector('.btn-open-book');
            btn.disabled = true;
            try {
                const response = await fetch(`${API_URL}/library/${book.id}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    window.open(url, '_blank');
                } else {
                    alert('Não foi possível abrir o arquivo.');
                }
            } catch (err) {
                alert('Erro de rede ao tentar abrir o arquivo.');
            } finally {
                btn.disabled = false;
            }
        });

        tbodyEl.appendChild(tr);
    });
}

// Upload Book Logic
const uploadBookForm = document.getElementById('upload-book-form');
const bookFileInput = document.getElementById('book-file');
const bookMsg = document.getElementById('book-msg');

if (bookFileInput) {
    bookFileInput.addEventListener('change', (e) => {
        bookMsg.textContent = e.target.files[0]?.name || 'Arraste seu arquivo HTML aqui ou clique para selecionar';
    });
}

if (uploadBookForm) {
    uploadBookForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const file = bookFileInput.files[0];
        const token = localStorage.getItem('token');
        if (!file || !token) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        const btn = document.getElementById('upload-book-btn');
        const msg = document.getElementById('upload-book-msg');
        btn.disabled = true;
        btn.textContent = 'Enviando...';
        
        try {
            const response = await fetch(`${API_URL}/library/`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });
            if (response.ok) {
                msg.textContent = 'Livro enviado com sucesso!';
                msg.className = 'msg-text msg-success';
                uploadBookForm.reset();
                bookMsg.textContent = 'Arraste seu arquivo HTML aqui ou clique para selecionar';
                fetchBooks('/library/', document.getElementById('all-books-tbody'), true, 1, 'all-books-pagination');
            } else {
                const err = await response.json();
                msg.textContent = err.detail || 'Erro ao enviar livro.';
                msg.className = 'msg-text msg-error';
            }
        } catch (err) {
            msg.textContent = 'Erro de rede.';
            msg.className = 'msg-text msg-error';
        } finally {
            btn.disabled = false;
            btn.textContent = 'Enviar Livro';
        }
    });
}

// Book Users Logic
async function fetchBookUsers(bookId, page = 1) {
    const token = localStorage.getItem('token');
    const tbodyEl = document.getElementById('book-users-tbody');
    tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center;">Carregando...</td></tr>';
    
    try {
        const response = await fetch(`${API_URL}/library/users/${bookId}?page=${page}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            const data = await response.json();
            renderBookUsersTable(data.users, tbodyEl, bookId);
            renderPaginationControls(data, 'book-users-pagination', (newPage) => fetchBookUsers(bookId, newPage));
        } else {
            tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--danger)">Erro</td></tr>';
        }
    } catch (error) {
        tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--danger)">Erro</td></tr>';
    }
}

function renderBookUsersTable(users, tbodyEl, bookId) {
    if (!users || users.length === 0) {
        tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center;">Nenhum usuário com acesso a este livro.</td></tr>';
        return;
    }
    tbodyEl.innerHTML = '';
    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>#${user.id}</td>
            <td>${user.username}</td>
            <td class="actions-cell">
                <button class="action-btn delete-btn btn-icon btn-remove-user-book" data-userid="${user.id}" title="Remover Acesso">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="18" y1="8" x2="23" y2="13"></line><line x1="23" y1="8" x2="18" y2="13"></line></svg>
                </button>
            </td>
        `;
        tr.querySelector('.btn-remove-user-book').addEventListener('click', async () => {
            const token = localStorage.getItem('token');
            await fetch(`${API_URL}/library/remove/${user.id}/${bookId}`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
            fetchBookUsers(bookId, 1);
        });
        tbodyEl.appendChild(tr);
    });
}

const addUserToBookForm = document.getElementById('add-user-to-book-form');
if (addUserToBookForm) {
    addUserToBookForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const bookId = document.getElementById('current-book-id').value;
        const userId = document.getElementById('book-user-id').value;
        const token = localStorage.getItem('token');
        
        try {
            const response = await fetch(`${API_URL}/library/add/${userId}/${bookId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                document.getElementById('book-user-id').value = '';
                fetchBookUsers(bookId, 1);
            } else {
                alert('Falha ao adicionar usuário. Verifique se o ID está correto ou se já possui acesso.');
            }
        } catch(err) {
            alert('Erro de rede.');
        }
    });
}

// User Books Logic
async function fetchUserBooks(userId, page = 1) {
    const token = localStorage.getItem('token');
    const tbodyEl = document.getElementById('user-books-tbody');
    tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center;">Carregando...</td></tr>';
    
    try {
        const response = await fetch(`${API_URL}/library/books/${userId}?page=${page}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            const data = await response.json();
            renderUserBooksTable(data.books, tbodyEl, userId);
            renderPaginationControls(data, 'user-books-pagination', (newPage) => fetchUserBooks(userId, newPage));
        } else {
            tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--danger)">Erro</td></tr>';
        }
    } catch (error) {
        tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--danger)">Erro</td></tr>';
    }
}

function renderUserBooksTable(books, tbodyEl, userId) {
    if (!books || books.length === 0) {
        tbodyEl.innerHTML = '<tr><td colspan="3" style="text-align:center;">Nenhum livro para este usuário.</td></tr>';
        return;
    }
    tbodyEl.innerHTML = '';
    books.forEach(book => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>#${book.id}</td>
            <td class="col-name" title="${book.filename}">${book.filename}</td>
            <td class="col-date">${formatDate(book.created_at)}</td>
            <td class="actions-cell">
                <button class="action-btn delete-btn btn-icon btn-remove-book-user" data-bookid="${book.id}" title="Remover Acesso">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="18" y1="8" x2="23" y2="13"></line><line x1="23" y1="8" x2="18" y2="13"></line></svg>
                </button>
            </td>
        `;
        tr.querySelector('.btn-remove-book-user').addEventListener('click', async () => {
            const token = localStorage.getItem('token');
            await fetch(`${API_URL}/library/remove/${userId}/${book.id}`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
            fetchUserBooks(userId, 1);
        });
        tbodyEl.appendChild(tr);
    });
}

const addBookToUserForm = document.getElementById('add-book-to-user-form');
if (addBookToUserForm) {
    addBookToUserForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userId = document.getElementById('current-user-books-id').value;
        const bookId = document.getElementById('user-book-id').value;
        const token = localStorage.getItem('token');
        
        try {
            const response = await fetch(`${API_URL}/library/add/${userId}/${bookId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                document.getElementById('user-book-id').value = '';
                fetchUserBooks(userId, 1);
            } else {
                alert('Falha ao adicionar livro. Verifique se o ID está correto ou se já possui acesso.');
            }
        } catch(err) {
            alert('Erro de rede.');
        }
    });
}

// Theme Logic
const themeSelectors = document.querySelectorAll('.theme-selector');

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    themeSelectors.forEach(select => select.value = theme);
}

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
}

themeSelectors.forEach(select => {
    select.addEventListener('change', (e) => {
        applyTheme(e.target.value);
    });
});

// Init
initTheme();
checkAuth();
