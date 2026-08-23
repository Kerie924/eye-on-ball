from json import dumps
from urllib.parse import urlparse

from fastapi import HTTPException, status
from fastapi.responses import HTMLResponse

from app.config import settings

_DEFAULT_API_KEY = "AIzaSyAjl7oyXIWmLGys0YnJEjPSd5g8rZ1cSDM"
_DEFAULT_AUTH_DOMAIN = "lance-on.firebaseapp.com"
_DEFAULT_APP_ID = "1:998054424238:android:e105a80d4f32de63b7073f"


def is_safe_continue_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme in {"lanceon", "exp", "exps"}:
        return True
    if parsed.scheme in {"http", "https"} and host in {"localhost", "127.0.0.1"}:
        return True
    if parsed.scheme == "http" and host.startswith("192.168."):
        return True
    return False


def google_app_html(continue_url: str) -> HTMLResponse:
    if not is_safe_continue_url(continue_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL de retorno invalida",
        )

    firebase_config = {
        "apiKey": _DEFAULT_API_KEY,
        "authDomain": _DEFAULT_AUTH_DOMAIN,
        "projectId": settings.firebase_project_id or "lance-on",
        "appId": _DEFAULT_APP_ID,
    }

    page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Lance On — Google</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: system-ui, sans-serif;
      background: #0a0a0a;
      color: #f5f5f5;
    }}
    main {{ text-align: center; padding: 24px; }}
    p {{ color: #a3a3a3; }}
    .error {{ color: #fca5a5; }}
  </style>
</head>
<body>
  <main>
    <h1>Lance On</h1>
    <p id="status">Conectando com o Google...</p>
  </main>
  <script src="https://www.gstatic.com/firebasejs/11.6.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/11.6.0/firebase-auth-compat.js"></script>
  <script>
    const CONTINUE_URL = {dumps(continue_url)};
    const FIREBASE_CONFIG = {dumps(firebase_config)};
    const statusEl = document.getElementById("status");

    function returnToApp(idToken) {{
      const sep = CONTINUE_URL.includes("?") ? "&" : "?";
      window.location.replace(CONTINUE_URL + sep + "id_token=" + encodeURIComponent(idToken));
    }}

    async function start() {{
      try {{
        firebase.initializeApp(FIREBASE_CONFIG);
        const provider = new firebase.auth.GoogleAuthProvider();
        provider.addScope("email");
        provider.addScope("profile");
        provider.setCustomParameters({{ prompt: "select_account" }});
        const result = await firebase.auth().signInWithPopup(provider);
        const idToken = await result.user.getIdToken();
        statusEl.textContent = "Voltando para o app...";
        returnToApp(idToken);
      }} catch (error) {{
        const code = error && error.code ? String(error.code) : "";
        if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") {{
          statusEl.textContent = "Login cancelado.";
          return;
        }}
        if (code === "auth/unauthorized-domain") {{
          statusEl.className = "error";
          statusEl.textContent =
            "Adicione api.lanceonpara.com.br em Firebase Authentication → Settings → Authorized domains.";
          return;
        }}
        statusEl.className = "error";
        statusEl.textContent = (error && error.message) || "Falha no login Google";
      }}
    }}

    start();
  </script>
</body>
</html>
"""
    return HTMLResponse(page)
