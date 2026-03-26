"""
lobby.py — Multi-user session management lobby for the oTree game.

Teachers/researchers log in and can create sessions via the oTree 6 REST API.
Run as a separate service: uvicorn lobby:app --host 0.0.0.0 --port 8001

Dependencies: pip install fastapi uvicorn httpx python-multipart itsdangerous pyyaml
"""

import os
import json
import hashlib
import secrets
import httpx
import yaml

from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# ─── Configuration ──────────────────────────────────────────────────────────

OTREE_URL = os.environ.get("OTREE_URL", "http://localhost:8000")
OTREE_REST_KEY = os.environ.get("OTREE_REST_KEY", "dev_rest_key_2025")  # must match settings.py
SECRET_KEY = os.environ.get("LOBBY_SECRET_KEY", secrets.token_hex(32))
USERS_FILE = Path(os.environ.get("LOBBY_USERS_FILE", "lobby_users.yaml"))
SESSION_CONFIG = os.environ.get("OTREE_SESSION_CONFIG", "test_1")

# Session cookie signer
signer = URLSafeTimedSerializer(SECRET_KEY)


# ─── User store (YAML) ──────────────────────────────────────────────────────


def load_users() -> dict:
    """Load username → hashed password from YAML file."""
    if not USERS_FILE.exists():
        # Create a default admin user on first run
        default = {"admin": _hash_password("changeme")}
        with open(USERS_FILE, "w") as f:
            yaml.dump(default, f)
        print(f"Created default user file at {USERS_FILE}")
        print("Default credentials: admin / changeme — CHANGE IMMEDIATELY")
        return default
    with open(USERS_FILE) as f:
        return yaml.safe_load(f) or {}


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_user(username: str, password: str) -> bool:
    users = load_users()
    hashed = users.get(username)
    return hashed is not None and hashed == _hash_password(password)


# ─── Auth helpers ────────────────────────────────────────────────────────────


def get_current_user(request: Request) -> str | None:
    token = request.cookies.get("lobby_session")
    if not token:
        return None
    try:
        username = signer.loads(token, max_age=86400)  # 24h
        return username
    except (BadSignature, SignatureExpired):
        return None


def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/lobby/login"})
    return user


# ─── oTree REST helpers ──────────────────────────────────────────────────────

OTREE_HEADERS = {"otree-rest-key": OTREE_REST_KEY, "Content-Type": "application/json"}


async def otree_create_session(num_participants: int, session_config: str) -> dict:
    payload = {
        "session_config_name": session_config,
        "num_participants": num_participants,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{OTREE_URL}/api/sessions",
            headers=OTREE_HEADERS,
            json=payload,
        )
        r.raise_for_status()
        return r.json()


async def otree_get_sessions() -> list:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{OTREE_URL}/api/sessions", headers=OTREE_HEADERS)
        r.raise_for_status()
        return r.json()


# ─── FastAPI app ─────────────────────────────────────────────────────────────

app = FastAPI(title="Lobby – Tragédie des communs", docs_url=None, redoc_url=None)

# ─── Shared CSS/HTML helpers ─────────────────────────────────────────────────

BASE_STYLE = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;1,9..144,400&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {
  --river-deep: #1a3a4a;
  --river-mid:  #2e6b7e;
  --river-light:#5fa8b8;
  --river-pale: #c8e8ef;
  --moss:       #4a7c4e;
  --earth-pale: #f5ede0;
  --sand:       #e8dcc8;
  --surface:    #fafaf7;
  --border:     rgba(58,90,65,0.15);
  --text:       #1c2b1e;
  --muted:      #7a8f82;
  --danger:     #8b2020;
  --radius:     12px;
  --font-d:     'Fraunces', Georgia, serif;
  --font-b:     'DM Sans', system-ui, sans-serif;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
body{font-family:var(--font-b);background:var(--surface);color:var(--text);min-height:100vh;display:flex;flex-direction:column;}
body::before{content:'';position:fixed;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--river-deep),var(--river-mid),var(--river-light),var(--moss),var(--river-deep));background-size:200% 100%;animation:rf 8s linear infinite;z-index:100;}
@keyframes rf{0%{background-position:0%}100%{background-position:200%}}
header{background:var(--river-deep);color:white;padding:18px 32px;display:flex;align-items:center;gap:14px;}
.brand-title{font-family:var(--font-d);font-size:1.1rem;font-weight:500;}
.brand-sub{font-size:0.75rem;opacity:0.5;margin-top:2px;}
main{flex:1;display:flex;flex-direction:column;align-items:center;padding:40px 20px 64px;}
.inner{width:100%;max-width:680px;}
h1{font-family:var(--font-d);font-size:1.8rem;font-weight:500;color:var(--river-deep);margin-bottom:28px;letter-spacing:-0.02em;}
h2{font-family:var(--font-d);font-size:1.2rem;font-weight:500;color:var(--river-deep);margin-bottom:16px;}
.card{background:white;border:1px solid var(--border);border-radius:var(--radius);padding:24px 28px;margin-bottom:18px;box-shadow:0 1px 3px rgba(26,58,74,0.07);}
label{font-size:0.88rem;font-weight:500;color:var(--muted);display:block;margin-bottom:5px;}
input[type=text],input[type=password],input[type=number],select{width:100%;padding:10px 14px;border:1.5px solid var(--border);border-radius:8px;font-family:var(--font-b);font-size:0.95rem;color:var(--text);background:white;outline:none;transition:border-color .2s;}
input:focus,select:focus{border-color:var(--river-mid);box-shadow:0 0 0 3px rgba(46,107,126,0.1);}
.btn{display:inline-flex;align-items:center;gap:7px;background:var(--river-deep);color:white;border:none;border-radius:8px;padding:11px 24px;font-family:var(--font-b);font-size:0.92rem;font-weight:500;cursor:pointer;transition:background .2s,transform .15s;text-decoration:none;}
.btn:hover{background:var(--river-mid);transform:translateY(-1px);}
.btn-sm{padding:7px 16px;font-size:0.82rem;}
.btn-danger{background:#8b2020;}.btn-danger:hover{background:#a02828;}
.btn-ghost{background:transparent;border:1.5px solid var(--border);color:var(--muted);}.btn-ghost:hover{background:var(--earth-pale);transform:none;}
.alert-err{background:#fdf0f0;border:1px solid #e0a0a0;border-radius:8px;padding:12px 16px;color:#8b2020;font-size:0.88rem;margin-bottom:16px;}
.alert-ok{background:#f0f8f0;border:1px solid #a0d0a0;border-radius:8px;padding:12px 16px;color:#1b5e20;font-size:0.88rem;margin-bottom:16px;}
.stat-row{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid var(--border);font-size:0.9rem;}
.stat-row:last-child{border-bottom:none;}
.stat-lbl{color:var(--muted);}
.stat-val{font-weight:500;}
.session-card{background:white;border:1px solid var(--border);border-radius:var(--radius);padding:18px 24px;margin-bottom:12px;}
.session-code{font-family:monospace;font-size:0.85rem;background:var(--earth-pale);border:1px solid var(--sand);border-radius:6px;padding:6px 10px;color:var(--river-deep);display:inline-block;margin-top:6px;word-break:break-all;}
.url-row{display:flex;align-items:center;gap:8px;margin-top:8px;}
.copy-btn{font-size:0.75rem;padding:4px 10px;}
.form-row{margin-bottom:16px;}
footer{background:var(--river-deep);color:rgba(255,255,255,0.35);text-align:center;padding:12px;font-size:0.72rem;}
nav.topnav{display:flex;align-items:center;gap:16px;margin-left:auto;}
.topnav a{color:rgba(255,255,255,0.6);text-decoration:none;font-size:0.82rem;}
.topnav a:hover{color:white;}
.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:500;background:rgba(255,255,255,0.12);color:rgba(255,255,255,0.8);}
</style>
"""


def _header(username: str | None = None) -> str:
    nav = ""
    if username:
        nav = f"""
        <nav class="topnav">
          <span class="badge">{username}</span>
          <a href="/lobby/logout">Déconnexion</a>
        </nav>"""
    return f"""
    <header>
      <svg width="36" height="36" viewBox="0 0 40 40" fill="none">
        <path d="M4 28C8 22,14 26,20 20C26 14,32 18,36 12" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round" fill="none"/>
        <path d="M4 34C8 28,14 32,20 26C26 20,32 24,38 18" stroke="rgba(95,168,184,0.7)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
        <circle cx="10" cy="12" r="5" fill="rgba(74,124,78,0.55)"/>
        <circle cx="30" cy="10" r="3.5" fill="rgba(74,124,78,0.35)"/>
      </svg>
      <div>
        <div class="brand-title">Lobby — Tragédie des communs</div>
        <div class="brand-sub">Gestion des sessions de jeu</div>
      </div>
      {nav}
    </header>"""


def _footer() -> str:
    return "<footer>PhDTrack – Transition Environnementale · ENS de Rennes</footer>"


# ─── Routes ──────────────────────────────────────────────────────────────────


@app.get("/lobby", response_class=HTMLResponse)
@app.get("/lobby/", response_class=HTMLResponse)
async def index(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/lobby/login", status_code=302)
    return RedirectResponse("/lobby/dashboard", status_code=302)


@app.get("/lobby/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    err_html = f'<div class="alert-err">Identifiants incorrects.</div>' if error else ""
    html = f"""<!DOCTYPE html><html lang="fr"><head><title>Connexion – Lobby</title>{BASE_STYLE}</head>
    <body>
    {_header()}
    <main><div class="inner">
      <h1>Connexion</h1>
      {err_html}
      <div class="card">
        <form method="post" action="/lobby/login">
          <div class="form-row">
            <label>Nom d'utilisateur</label>
            <input type="text" name="username" autocomplete="username" required autofocus>
          </div>
          <div class="form-row">
            <label>Mot de passe</label>
            <input type="password" name="password" autocomplete="current-password" required>
          </div>
          <button type="submit" class="btn">Se connecter</button>
        </form>
      </div>
    </div></main>
    {_footer()}
    </body></html>"""
    return HTMLResponse(html)


@app.post("/lobby/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if not verify_user(username, password):
        return RedirectResponse("/lobby/login?error=1", status_code=302)
    token = signer.dumps(username)
    response = RedirectResponse("/lobby/dashboard", status_code=302)
    response.set_cookie(
        "lobby_session", token, httponly=True, samesite="lax", max_age=86400
    )
    return response


@app.get("/lobby/logout")
async def logout():
    response = RedirectResponse("/lobby/login", status_code=302)
    response.delete_cookie("lobby_session")
    return response


@app.get("/lobby/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, created: str = "", error: str = ""):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/lobby/login", status_code=302)

    # Fetch active sessions from oTree
    sessions_html = ""
    try:
        sessions = await otree_get_sessions()
        if sessions:
            for s in sessions:
                code = s.get("code", "—")
                config = s.get("session_config", {}).get("name", "—")
                n = s.get("num_participants", "?")
                created_at = s.get("created_at_timestamp", "")
                room_url = (
                    f"{OTREE_URL}/room/{s.get('room_name', '')}"
                    if s.get("room_name")
                    else ""
                )
                join_url = f"{OTREE_URL}/join/{code}"
                admin_url = f"{OTREE_URL}/SessionStartLinks/{code}"

                sessions_html += f"""
                <div class="session-card">
                  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                    <div>
                      <strong style="font-size:0.95rem;">{config}</strong>
                      &nbsp;·&nbsp;
                      <span style="color:var(--muted);font-size:0.85rem;">{n} participants</span>
                    </div>
                  </div>
                  <div class="session-code">{code}</div>
                  <div class="url-row">
                    <span style="font-size:0.8rem;color:var(--muted);">Lien de participation :</span>
                    <a href="{join_url}" target="_blank" style="font-size:0.8rem;color:var(--river-mid);">{join_url}</a>
                    <button class="btn btn-sm copy-btn" onclick="navigator.clipboard.writeText('{join_url}');this.textContent='Copié !'">Copier</button>
                  </div>
                  <div class="url-row">
                    <a href="{admin_url}" target="_blank" class="btn btn-sm btn-ghost">Liens individuels</a>
                  </div>
                </div>"""
        else:
            sessions_html = '<p style="color:var(--muted);font-size:0.9rem;">Aucune session active pour l\'instant.</p>'
    except Exception as e:
        sessions_html = (
            f'<div class="alert-err">Impossible de contacter oTree : {e}</div>'
        )

    created_banner = ""
    if created:
        created_banner = f'<div class="alert-ok"> Session créée avec succès ! Code : <strong>{created}</strong></div>'

    error_banner = ""
    if error:
        error_banner = f'<div class="alert-err"> Erreur lors de la création de session : {error}</div>'

    html = f"""<!DOCTYPE html><html lang="fr"><head><title>Tableau de bord – Lobby</title>{BASE_STYLE}</head>
    <body>
    {_header(user)}
    <main><div class="inner">
      <h1>Tableau de bord</h1>
      {created_banner}
      {error_banner}

      <!-- Create session -->
      <div class="card">
        <h2>Créer une nouvelle session</h2>
        <form method="post" action="/lobby/create-session">
          <div class="form-row">
            <label>Nombre de participants</label>
            <input type="number" name="num_participants" min="2" max="30" value="6" required>
          </div>
          <div class="form-row">
            <label>Configuration</label>
            <select name="session_config">
              <option value="{SESSION_CONFIG}">{SESSION_CONFIG}</option>
            </select>
          </div>
          <button type="submit" class="btn"> Créer la session</button>
        </form>
      </div>

      <!-- Active sessions -->
      <div class="card">
        <h2>Sessions actives</h2>
        {sessions_html}
        <div style="margin-top:14px;">
          <a href="/lobby/dashboard" class="btn btn-ghost btn-sm">🔄 Actualiser</a>
          <a href="{OTREE_URL}/SessionMonitor" target="_blank" class="btn btn-ghost btn-sm" style="margin-left:8px;">Moniteur oTree</a>
        </div>
      </div>

    </div></main>
    {_footer()}
    </body></html>"""
    return HTMLResponse(html)


@app.post("/lobby/create-session")
async def create_session(
    request: Request,
    num_participants: int = Form(...),
    session_config: str = Form(...),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/lobby/login", status_code=302)

    try:
        result = await otree_create_session(num_participants, session_config)
        code = result.get("code", "unknown")
        return RedirectResponse(f"/lobby/dashboard?created={code}", status_code=302)
    except Exception as e:
        # Log error for debugging
        error_msg = f"Session creation failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        # Redirect with error message (encode for URL if needed)
        import urllib.parse
        return RedirectResponse(f"/lobby/dashboard?error={urllib.parse.quote(error_msg)}", status_code=302)


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("lobby:app", host="0.0.0.0", port=8001, reload=False)
