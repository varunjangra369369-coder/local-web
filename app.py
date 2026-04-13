import os
import sys
import uuid
import importlib.util
import traceback
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# =========================================================
# THE MULTI-USER SINGLE PAGE APPLICATION (HTML/CSS/JS)
# =========================================================
SPA_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Cloud Python Workspace</title>
    <style>
        :root { --bg-color: #0f172a; --card-bg: #1e293b; --primary: #3b82f6; --success: #10b981; --danger: #ef4444; --text-main: #f8fafc; --text-muted: #94a3b8; --border: #334155; }
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { margin: 0; font-family: system-ui, sans-serif; background-color: var(--bg-color); color: var(--text-main); overscroll-behavior: none; height: 100vh; display: flex; flex-direction: column; }
        
        /* Utility */
        .hidden { display: none !important; }
        .error-msg { color: var(--danger); font-size: 14px; margin-top: 10px; text-align: center; height: 20px; }
        
        /* Headers */
        .app-header { background: var(--card-bg); height: 60px; display: flex; justify-content: space-between; align-items: center; padding: 0 16px; border-bottom: 1px solid var(--border); flex-shrink: 0; }
        .app-title { font-size: 18px; font-weight: 700; margin: 0; color: var(--primary); }
        .icon-btn { background: none; border: none; color: var(--text-main); font-size: 20px; padding: 10px; cursor: pointer; }
        
        /* Auth Screens */
        .auth-container { flex: 1; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .auth-card { background: var(--card-bg); padding: 40px 30px; border-radius: 16px; border: 1px solid var(--border); box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 100%; max-width: 380px; }
        .auth-card h2 { margin-top: 0; text-align: center; }
        input, select { width: 100%; padding: 14px; margin-top: 15px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-color); color: white; font-size: 15px; }
        button.primary-btn { width: 100%; padding: 14px; margin-top: 20px; background: var(--primary); color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; }
        .text-link { color: var(--primary); text-align: center; display: block; margin-top: 15px; cursor: pointer; font-size: 14px; background: none; border: none; width: 100%; }
        
        /* Dashboard */
        #dashboard-view { flex: 1; overflow-y: auto; padding: 16px; padding-bottom: 90px; }
        .project-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 12px; cursor: pointer; }
        .fab { position: fixed; bottom: 24px; right: 24px; width: 56px; height: 56px; border-radius: 50%; background: var(--primary); color: white; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.4); font-size: 24px; cursor: pointer; z-index: 1000; }
        
        /* Editor */
        #editor-view { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .tabs { display: flex; background: var(--bg-color); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; margin: 0 10px; }
        .tab { flex: 1; padding: 8px 12px; font-size: 14px; border: none; background: transparent; color: var(--text-muted); font-weight: 600; }
        .tab.active { background: var(--primary); color: white; }
        #code-pane { display: none; flex: 1; background: #1e1e1e; }
        textarea { width: 100%; height: 100%; background: transparent; color: #d4d4d4; font-family: monospace; font-size: 14px; padding: 16px; border: none; resize: none; outline: none; }
        #preview-pane { display: flex; flex: 1; flex-direction: column; position: relative; }
        iframe { flex: 1; border: none; background: #ffffff; width: 100%; height: 100%; }
        .loading-overlay { position: absolute; inset: 0; background: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; display: none; color:#333; font-family: sans-serif;}
    </style>
</head>
<body>

    <!-- 1. AUTHENTICATION SCREENS -->
    <div id="auth-view" class="auth-container">
        
        <!-- Signup Screen -->
        <div id="signup-card" class="auth-card hidden">
            <h2>Create Account</h2>
            <p style="text-align:center; color:var(--text-muted); font-size:14px;">Set up your private workspace</p>
            <input type="password" id="reg-password" placeholder="Create a Password" required>
            <select id="reg-question">
                <option value="pet">What is your first pet's name?</option>
                <option value="city">In what city were you born?</option>
                <option value="color">What is your favorite color?</option>
            </select>
            <input type="text" id="reg-answer" placeholder="Security Answer (for password reset)" required>
            <div id="signup-error" class="error-msg"></div>
            <button class="primary-btn" onclick="handleSignup()">Create Workspace</button>
        </div>

        <!-- Login Screen -->
        <div id="login-card" class="auth-card hidden">
            <h2>Welcome Back</h2>
            <input type="password" id="login-password" placeholder="Enter Password">
            <div id="login-error" class="error-msg"></div>
            <button class="primary-btn" onclick="handleLogin()">Login</button>
            <button class="text-link" onclick="showScreen('forgot-card')">Forgot Password?</button>
        </div>

        <!-- Forgot Password Screen -->
        <div id="forgot-card" class="auth-card hidden">
            <h2>Reset Password</h2>
            <p id="recovery-question-text" style="color:var(--text-muted); font-size:14px; text-align:center;"></p>
            <input type="text" id="recovery-answer" placeholder="Your Answer">
            <input type="password" id="new-password" placeholder="Enter New Password">
            <div id="forgot-error" class="error-msg"></div>
            <button class="primary-btn" onclick="handleResetPassword()">Reset Password</button>
            <button class="text-link" onclick="showScreen('login-card')">Back to Login</button>
        </div>

    </div>

    <!-- 2. DASHBOARD SCREEN -->
    <div id="app-view" class="hidden" style="display:flex; flex-direction:column; height:100%;">
        <div class="app-header">
            <h1 class="app-title">☁️ My Workspace</h1>
            <button class="icon-btn" onclick="logout()" style="font-size:14px; color:var(--danger)">Lock</button>
        </div>
        
        <div id="dashboard-view">
            <div id="projects-container"></div>
            <button class="fab" onclick="createNewProject()">+</button>
        </div>

        <!-- 3. EDITOR SCREEN -->
        <div id="editor-view" class="hidden">
            <div style="padding: 10px; background:var(--card-bg); display:flex; align-items:center;">
                <button class="icon-btn" onclick="closeEditor()" style="margin-right:10px;">◀</button>
                <div class="tabs">
                    <button class="tab active" id="tab-preview" onclick="switchTab('preview')">👁️ Preview</button>
                    <button class="tab" id="tab-code" onclick="switchTab('code')">💻 Code</button>
                </div>
                <button class="icon-btn" onclick="deleteProject()" style="color:var(--danger); margin-left:auto;">🗑️</button>
            </div>
            
            <div id="code-pane">
                <textarea id="code-editor" spellcheck="false"></textarea>
                <button class="fab" onclick="saveAndRun()" style="background:var(--success)">▶</button>
            </div>
            
            <div id="preview-pane">
                <div id="loading-overlay" class="loading-overlay"><h3>Executing... ⚡</h3></div>
                <iframe id="app-preview"></iframe>
            </div>
        </div>
    </div>

    <script>
        // ==========================================
        // CRYPTOGRAPHY & AUTHENTICATION LOGIC
        // ==========================================
        
        // Military-grade SHA-256 Hashing function
        async function hashString(message) {
            const msgBuffer = new TextEncoder().encode(message.toLowerCase().trim());
            const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        }

        const authKey = 'flask_workspace_auth';
        const dataKey = 'flask_workspace_projects';
        let currentProjectId = null;

        function getAuth() { return JSON.parse(localStorage.getItem(authKey)); }
        
        function showScreen(screenId) {
            document.getElementById('auth-view').classList.add('hidden');
            document.getElementById('app-view').classList.add('hidden');
            document.getElementById('signup-card').classList.add('hidden');
            document.getElementById('login-card').classList.add('hidden');
            document.getElementById('forgot-card').classList.add('hidden');

            if (screenId === 'app') {
                document.getElementById('app-view').classList.remove('hidden');
                loadDashboard();
            } else {
                document.getElementById('auth-view').classList.remove('hidden');
                document.getElementById(screenId).classList.remove('hidden');
            }
            
            // Clear errors
            document.querySelectorAll('.error-msg').forEach(el => el.innerText = '');
        }

        async function handleSignup() {
            const pw = document.getElementById('reg-password').value;
            const qType = document.getElementById('reg-question').value;
            const qText = document.getElementById('reg-question').options[document.getElementById('reg-question').selectedIndex].text;
            const ans = document.getElementById('reg-answer').value;

            if (!pw || !ans) return showErr('signup-error', 'Please fill all fields');
            if (pw.length < 4) return showErr('signup-error', 'Password must be 4+ chars');

            const pwHash = await hashString(pw);
            const ansHash = await hashString(ans);

            localStorage.setItem(authKey, JSON.stringify({
                pwHash: pwHash,
                question: qText,
                ansHash: ansHash
            }));
            
            showScreen('app');
        }

        async function handleLogin() {
            const pw = document.getElementById('login-password').value;
            const auth = getAuth();
            if (!pw) return;

            const pwHash = await hashString(pw);
            if (pwHash === auth.pwHash) {
                document.getElementById('login-password').value = '';
                showScreen('app');
            } else {
                showErr('login-error', 'Incorrect password');
            }
        }

        async function handleResetPassword() {
            const ans = document.getElementById('recovery-answer').value;
            const newPw = document.getElementById('new-password').value;
            const auth = getAuth();

            if (!ans || !newPw) return showErr('forgot-error', 'Fill all fields');

            const ansHash = await hashString(ans);
            if (ansHash === auth.ansHash) {
                auth.pwHash = await hashString(newPw);
                localStorage.setItem(authKey, JSON.stringify(auth));
                showScreen('login-card');
                alert("Password reset successfully! Please login.");
            } else {
                showErr('forgot-error', 'Security answer is incorrect');
            }
        }

        function showErr(id, msg) { document.getElementById(id).innerText = msg; }
        function logout() { showScreen('login-card'); }

        // ==========================================
        // WORKSPACE & EDITOR LOGIC
        // ==========================================

        const defaultCode = `from flask import Flask\\n\\napp = Flask(__name__)\\n\\n@app.route('/')\\ndef home():\\n    return "<h1>🚀 Serverless App Running!</h1><p>Edit the code to update this page.</p>"`;

        function loadDashboard() {
            document.getElementById('dashboard-view').classList.remove('hidden');
            document.getElementById('editor-view').classList.add('hidden');
            
            const container = document.getElementById('projects-container');
            let projects = JSON.parse(localStorage.getItem(dataKey)) || {};
            const keys = Object.keys(projects);
            
            if (keys.length === 0) {
                container.innerHTML = `<div style="text-align:center; padding:40px; color:#888;">No projects yet. Click + to create one.</div>`;
                return;
            }

            container.innerHTML = '';
            keys.sort((a,b)=>b-a).forEach(id => {
                const card = document.createElement('div');
                card.className = 'project-card';
                card.onclick = () => openEditor(id);
                card.innerHTML = `<h3 style="margin:0 0 5px 0;">${projects[id].name}</h3><small style="color:#888;">ID: ${id}</small>`;
                container.appendChild(card);
            });
        }

        function createNewProject() {
            const name = prompt("Enter Project Name:");
            if (!name) return;
            let projects = JSON.parse(localStorage.getItem(dataKey)) || {};
            const id = Date.now().toString();
            projects[id] = { name: name.trim(), code: defaultCode };
            localStorage.setItem(dataKey, JSON.stringify(projects));
            openEditor(id);
        }

        function openEditor(id) {
            currentProjectId = id;
            let projects = JSON.parse(localStorage.getItem(dataKey));
            document.getElementById('code-editor').value = projects[id].code;
            
            document.getElementById('dashboard-view').classList.add('hidden');
            document.getElementById('editor-view').classList.remove('hidden');
            
            saveAndRun();
        }

        function closeEditor() {
            currentProjectId = null;
            document.getElementById('app-preview').removeAttribute('srcdoc');
            loadDashboard();
        }

        function deleteProject() {
            if (confirm("Delete this project?")) {
                let projects = JSON.parse(localStorage.getItem(dataKey));
                delete projects[currentProjectId];
                localStorage.setItem(dataKey, JSON.stringify(projects));
                closeEditor();
            }
        }

        function switchTab(tab) {
            document.getElementById('tab-preview').classList.toggle('active', tab==='preview');
            document.getElementById('tab-code').classList.toggle('active', tab==='code');
            document.getElementById('preview-pane').style.display = tab==='preview' ? 'flex' : 'none';
            document.getElementById('code-pane').style.display = tab==='code' ? 'flex' : 'none';
        }

        function saveAndRun() {
            const code = document.getElementById('code-editor').value;
            let projects = JSON.parse(localStorage.getItem(dataKey));
            projects[currentProjectId].code = code;
            localStorage.setItem(dataKey, JSON.stringify(projects));
            
            switchTab('preview');
            
            const overlay = document.getElementById('loading-overlay');
            const preview = document.getElementById('app-preview');
            
            overlay.style.display = 'flex';
            preview.removeAttribute('srcdoc');

            fetch('/run_serverless', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            })
            .then(res => res.json())
            .then(data => {
                overlay.style.display = 'none';
                if (data.status === "success") {
                    preview.srcdoc = data.html;
                } else {
                    preview.srcdoc = `<div style="padding:20px; font-family:sans-serif; background:#fff;"><h2 style="color:#e11d48; margin-top:0;">Error 💥</h2><pre style="background:#ffe4e6; color:#be123c; padding:15px; border-radius:8px; white-space:pre-wrap; border:1px solid #fda4af;">${data.message}</pre></div>`;
                }
            })
            .catch(err => {
                overlay.style.display = 'none';
                preview.srcdoc = "<h3>Network Connection Error</h3>";
            });
        }

        // ==========================================
        // INITIALIZATION LOGIC
        // ==========================================
        window.onload = () => {
            const auth = getAuth();
            if (!auth) {
                showScreen('signup-card');
            } else {
                document.getElementById('recovery-question-text').innerText = "Security Question: " + auth.question;
                showScreen('login-card');
            }
        };
    </script>
</body>
</html>
"""

# =========================================================
# FLASK ROUTES
# =========================================================

@app.route('/')
def index():
    """Serves the Single Page Application"""
    return render_template_string(SPA_HTML)

# =========================================================
# ⚡ THE VERCEL SERVERLESS EXECUTION ENGINE
# =========================================================
@app.route('/run_serverless', methods=['POST'])
def run_serverless():
    """
    Safely executes arbitrary Flask code in Vercel's serverless environment.
    It simulates a web request internally and returns the HTML output instantly.
    """
    code = request.json.get('code', '')
    
    # Generate a unique module ID to prevent Vercel execution collisions
    module_id = uuid.uuid4().hex
    module_name = f"dynamic_app_{module_id}"
    tmp_path = f"/tmp/{module_name}.py"

    try:
        # Write user code to Vercel's fast temporary storage
        with open(tmp_path, 'w') as f:
            f.write(code)

        # Import the code as a dynamic python module
        spec = importlib.util.spec_from_file_location(module_name, tmp_path)
        dynamic_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = dynamic_module
        
        # Execute the module to create the Flask app object
        spec.loader.exec_module(dynamic_module)

        # Search for the user's Flask instance inside their code
        app_instance = None
        for attr in dir(dynamic_module):
            obj = getattr(dynamic_module, attr)
            if isinstance(obj, Flask) and obj.name != __name__:
                app_instance = obj
                break

        if not app_instance:
            return jsonify({"status": "error", "message": "Code must contain 'app = Flask(__name__)'"})

        # Simulate a browser GET request to the root '/'
        client = app_instance.test_client()
        response = client.get('/') 

        # Clean up the file
        os.remove(tmp_path)

        # Return the HTML text to the frontend
        return jsonify({
            "status": "success",
            "html": response.data.decode('utf-8')
        })

    except Exception as e:
        # Capture and return Python syntax/traceback errors gracefully
        error_msg = traceback.format_exc()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return jsonify({"status": "error", "message": error_msg})

if __name__ == '__main__':
    app.run(debug=True)
