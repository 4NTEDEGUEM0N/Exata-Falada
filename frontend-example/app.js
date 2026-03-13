const API_URL = 'http://localhost:8000';
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
            
            // Check admin status to show advanced settings
            if (data.admin === true) {
                document.getElementById('admin-settings').classList.remove('hidden');
                userDisplay.innerHTML += ' <span style="color:var(--primary); font-size: 0.8em; font-weight: bold;">[ADMIN]</span>';
            } else {
                document.getElementById('admin-settings').classList.add('hidden');
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

// Init
checkAuth();
