import os
import sys
import uuid
import importlib.util
import traceback
from flask import Flask, request, jsonify, render_template_string, redirect, session

app = Flask(__name__)
# =========================================================
# 🔒 SECURITY SETTINGS
# =========================================================
# 1. Change this to a random long string to secure your cookies
app.secret_key = "REPLACE_THIS_WITH_A_SUPER_SECRET_RANDOM_STRING"
# 2. Set your private login password here
APP_PASSWORD = "mysecretpassword123"

# =========================================================
# HTML TEMPLATES (Mobile UI + Login)
# =========================================================

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>Secure Login</title>
    <style>
        body { background: #0f172a; color: white; font-family: system-ui, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 40px 30px; border-radius: 16px; text-align: center; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 85%; max-width: 350px; }
        h2 { margin-top: 0; color: #3b82f6; }
        input { padding: 14px; margin-top: 15px; width: 100%; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; font-size: 16px; }
        button { padding: 14px; margin-top: 20px; width: 100%; background: #3b82f6; color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; }
        .error { color: #ef4444; margin-top: 15px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔒 Private Environment</h2>
        <p style="color: #94a3b8; font-size: 14px;">Please enter the master password.</p>
        <form method="POST" action="/login">
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Unlock Workspace</button>
        </form>
        {% if error %}<div class="error">Incorrect Password</div>{% endif %}
    </div>
</body>
</html>
"""

SHARED_CSS = """
<style>
    :root { --bg-color: #0f172a; --card-bg: #1e293b; --primary: #3b82f6; --success: #10b981; --danger: #ef4444; --text-main: #f8fafc; --text-muted: #94a3b8; --border: #334155; }
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body { margin: 0; font-family: system-ui, sans-serif; background-color: var(--bg-color); color: var(--text-main); overscroll-behavior: none; }
    .app-header { background: var(--card-bg); height: 60px; display: flex; justify-content: space-between; align-items: center; padding: 0 16px; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; }
    .app-title { font-size: 18px; font-weight: 700; margin: 0; }
    .icon-btn { background: none; border: none; color: var(--text-main); font-size: 20px; padding: 10px; cursor: pointer; }
    .fab { position: fixed; bottom: 24px; right: 24px; width: 56px; height: 56px; border-radius: 50%; background: var(--success); color: white; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.4); font-size: 24px; cursor: pointer; z-index: 1000; }
    .tabs { display: flex; background: var(--bg-color); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; margin: 0 10px; }
    .tab { flex: 1; padding: 8px 12px; font-size: 14px; border: none; background: transparent; color: var(--text-muted); font-weight: 600; }
    .tab.active { background: var(--primary); color: white; }
</style>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Flask Cloud Dashboard</title>
    """ + SHARED_CSS + """
    <style>
        .projects-list { padding: 16px; display: flex; flex-direction: column; gap: 12px; padding-bottom: 90px; }
        .project-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
        .p-title { font-size: 18px; font-weight: 600; margin: 0 0 8px 0; }
        .p-date { font-size: 13px; color: var(--text-muted); margin: 0; }
    </style>
</head>
<body>
    <div class="app-header">
        <h1 class="app-title" style="color:var(--primary)">☁️ Cloud Workspace</h1>
        <button class="icon-btn" onclick="window.location.href='/logout'" style="font-size:14px; color:var(--danger)">Logout</button>
    </div>
    <div class="projects-list" id="projects-container"></div>
    <button class="fab" onclick="createNewProject()" style="background:var(--primary)">+</button>
    <script>
        const defaultCode = `from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
        <h1>☁️ Running on Vercel</h1>
        <p>This is securely evaluated using Serverless architecture.</p>
        <p>Tap "Code" to change me!</p>
    </div>
    '''
`;
        function loadProjects() {
            const container = document.getElementById('projects-container');
            let projects = JSON.parse(localStorage.getItem('vercel_flask_projects')) || {};
            const projectIds = Object.keys(projects);
            if (projectIds.length === 0) {
                container.innerHTML = `<div style="text-align:center; padding: 40px; color:#94a3b8;">No projects yet. Tap + to begin.</div>`;
                return;
            }
            container.innerHTML = '';
            projectIds.sort((a, b) => b - a).forEach(id => {
                const p = projects[id];
                const card = document.createElement('div');
                card.className = 'project-card';
                card.onclick = () => window.location.href = '/project/' + id;
                card.innerHTML = `<p class="p-title">${p.name}</p><p class="p-date">ID: ${id}</p>`;
                container.appendChild(card);
            });
        }
        function createNewProject() {
            const name = prompt("Project Name:");
            if (!name) return;
            let projects = JSON.parse(localStorage.getItem('vercel_flask_projects')) || {};
            const newId = Date.now().toString();
            projects[newId] = { name: name.trim(), code: defaultCode };
            localStorage.setItem('vercel_flask_projects', JSON.stringify(projects));
            window.location.href = '/project/' + newId;
        }
        window.onload = loadProjects;
    </script>
</body>
</html>
"""

EDITOR_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Editor</title>
    """ + SHARED_CSS + """
    <style>
        body { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        .workspace { flex: 1; display: flex; flex-direction: column; background: #fff; }
        #code-view { display: none; flex: 1; flex-direction: column; background: #1e1e1e; }
        textarea { flex: 1; background: #1e1e1e; color: #d4d4d4; font-family: monospace; font-size: 14px; padding: 16px; border: none; resize: none; outline: none; width: 100%; }
        #preview-view { display: flex; flex: 1; flex-direction: column; position: relative; }
        iframe { flex: 1; border: none; width: 100%; height: 100%; background: #ffffff; }
        .loading-screen { position: absolute; inset: 0; background: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: sans-serif; display: none; }
    </style>
</head>
<body>
    <div class="app-header">
        <button class="icon-btn" onclick="window.location.href='/'">◀</button>
        <div class="tabs">
            <button class="tab active" id="tab-preview" onclick="switchTab('preview')">👁️ Preview</button>
            <button class="tab" id="tab-code" onclick="switchTab('code')">💻 Code</button>
        </div>
        <button class="icon-btn" style="color:var(--danger)" onclick="deleteProject()">🗑️</button>
    </div>
    <div class="workspace">
        <div id="preview-view">
            <div id="loading-overlay" class="loading-screen"><h3>Executing... ⚡</h3></div>
            <iframe id="app-preview"></iframe>
        </div>
        <div id="code-view">
            <textarea id="code-editor" spellcheck="false" autocomplete="off"></textarea>
            <button class="fab" onclick="saveAndRunCode()">▶</button>
        </div>
    </div>
    <script>
        const projectId = "{{ project_id }}";
        const editor = document.getElementById('code-editor');
        const preview = document.getElementById('app-preview');
        const overlay = document.getElementById('loading-overlay');
        
        let projects = JSON.parse(localStorage.getItem('vercel_flask_projects')) || {};
        if (!projects[projectId]) window.location.href = '/';
        editor.value = projects[projectId].code;

        function switchTab(tab) {
            document.getElementById('tab-preview').classList.toggle('active', tab==='preview');
            document.getElementById('tab-code').classList.toggle('active', tab==='code');
            document.getElementById('preview-view').style.display = tab==='preview' ? 'flex' : 'none';
            document.getElementById('code-view').style.display = tab==='code' ? 'flex' : 'none';
        }

        function deleteProject() {
            if (confirm("Delete project?")) {
                delete projects[projectId];
                localStorage.setItem('vercel_flask_projects', JSON.stringify(projects));
                window.location.href = '/';
            }
        }

        function saveAndRunCode() {
            projects[projectId].code = editor.value;
            localStorage.setItem('vercel_flask_projects', JSON.stringify(projects));
            switchTab('preview');
            
            overlay.style.display = 'flex';
            preview.removeAttribute('srcdoc');
            
            fetch('/run_serverless', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: editor.value })
            })
            .then(r => r.json())
            .then(data => {
                overlay.style.display = 'none';
                if (data.status === "success") {
                    preview.srcdoc = data.html;
                } else {
                    preview.srcdoc = `<div style="padding:16px; font-family:sans-serif;"><h2 style="color:#e11d48;">Syntax / Import Error 💥</h2><pre style="background:#ffe4e6; color:#be123c; padding:12px; border-radius:8px; white-space:pre-wrap; font-size:12px; border:1px solid #fda4af;">${data.message}</pre></div>`;
                }
            }).catch(e => {
                overlay.style.display = 'none';
                preview.srcdoc = "<h3 style='color:red; text-align:center'>Network Error calling Vercel</h3>";
            });
        }
        
        // Auto-run on load
        saveAndRunCode();
    </script>
</body>
</html>
"""

# =========================================================
# FLASK ROUTES & SECURITY LOGIC
# =========================================================

@app.before_request
def check_auth():
    """Forces password login before viewing any projects."""
    if request.path.startswith('/login'):
        return
    if not session.get('logged_in'):
        return render_template_string(LOGIN_HTML, error=False)

@app.route('/login', methods=['POST'])
def do_login():
    if request.form.get('password') == APP_PASSWORD:
        session['logged_in'] = True
        return redirect('/')
    return render_template_string(LOGIN_HTML, error=True)

@app.route('/logout')
def do_logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/project/<project_id>')
def project_editor(project_id):
    return render_template_string(EDITOR_HTML, project_id=project_id)

# =========================================================
# ⚡ THE VERCEL SERVERLESS EXECUTION ENGINE
# =========================================================
@app.route('/run_serverless', methods=['POST'])
def run_serverless():
    """
    Because Vercel cannot run background servers, this engine creates a
    unique temporary python file, parses the Flask code, mocks a web browser
    request internally, extracts the HTML, and returns it instantly.
    """
    code = request.json.get('code', '')
    
    # Generate a unique module name so Vercel executions don't collide
    module_id = uuid.uuid4().hex
    module_name = f"dynamic_app_{module_id}"
    tmp_path = f"/tmp/{module_name}.py"

    try:
        # 1. Write user code to Vercel's temporary read/write storage
        with open(tmp_path, 'w') as f:
            f.write(code)

        # 2. Dynamically import their python file as a module
        spec = importlib.util.spec_from_file_location(module_name, tmp_path)
        dynamic_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = dynamic_module
        
        # Execute the code (creates the Flask object inside the module)
        spec.loader.exec_module(dynamic_module)

        # 3. Find their Flask 'app' instance
        app_instance = None
        for attr in dir(dynamic_module):
            obj = getattr(dynamic_module, attr)
            if isinstance(obj, Flask) and obj.name != __name__:
                app_instance = obj
                break

        if not app_instance:
            return jsonify({"status": "error", "message": "Could not find a Flask 'app' object. Make sure you have 'app = Flask(__name__)'"})

        # 4. 🔥 Serverless Magic: Simulate a web request to their route without starting a server!
        client = app_instance.test_client()
        response = client.get('/')  # Fetches the response of their @app.route('/')

        # Cleanup the temporary file
        os.remove(tmp_path)

        # 5. Return the raw HTML back to the Frontend's iframe
        return jsonify({
            "status": "success",
            "html": response.data.decode('utf-8')
        })

    except Exception as e:
        # If their code crashes, grab the Python traceback and send it back
        error_msg = traceback.format_exc()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return jsonify({"status": "error", "message": error_msg})

if __name__ == '__main__':
    # Local fallback testing
    app.run(debug=True)
