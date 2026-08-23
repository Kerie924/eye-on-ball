from json import dumps

from fastapi.responses import HTMLResponse


def reset_password_html(token: str) -> HTMLResponse:
    page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Lance On — Nova senha</title>
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
    main {{
      width: min(420px, 100%);
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    h1 {{ margin: 0 0 4px; }}
    p {{ color: #a3a3a3; margin: 0 0 8px; }}
    label {{ font-size: 14px; color: #d4d4d4; }}
    input {{
      width: 100%;
      box-sizing: border-box;
      padding: 12px;
      border-radius: 10px;
      border: 1px solid #262626;
      background: #171717;
      color: #fff;
    }}
    button {{
      margin-top: 8px;
      border: 0;
      border-radius: 10px;
      padding: 12px 16px;
      background: #16a34a;
      color: #fff;
      font-weight: 700;
      cursor: pointer;
    }}
    .error {{ color: #fca5a5; }}
    .success {{ color: #86efac; }}
  </style>
</head>
<body>
  <main>
    <h1>Nova senha</h1>
    <p>Este link foi enviado ao seu e-mail e expira em 1 hora.</p>
    <label for="password">Nova senha</label>
    <input id="password" type="password" minlength="8" autocomplete="new-password" />
    <label for="confirm">Confirmar senha</label>
    <input id="confirm" type="password" minlength="8" autocomplete="new-password" />
    <p id="status"></p>
    <button id="submit" type="button">Salvar senha</button>
  </main>
  <script>
    const TOKEN = {dumps(token)};
    const statusEl = document.getElementById("status");
    const button = document.getElementById("submit");

    button.addEventListener("click", async () => {{
      const password = document.getElementById("password").value;
      const confirm = document.getElementById("confirm").value;
      statusEl.className = "";
      if (password.length < 8) {{
        statusEl.className = "error";
        statusEl.textContent = "A senha deve ter pelo menos 8 caracteres.";
        return;
      }}
      if (password !== confirm) {{
        statusEl.className = "error";
        statusEl.textContent = "As senhas nao coincidem.";
        return;
      }}
      button.disabled = true;
      try {{
        const response = await fetch("/api/auth/reset-password", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ token: TOKEN, password }}),
        }});
        const data = await response.json().catch(() => ({{}}));
        if (!response.ok) {{
          throw new Error(data.detail || "Nao foi possivel redefinir a senha");
        }}
        statusEl.className = "success";
        statusEl.textContent = "Senha atualizada. Voce ja pode entrar no app.";
      }} catch (error) {{
        statusEl.className = "error";
        statusEl.textContent = error.message || "Nao foi possivel redefinir a senha";
        button.disabled = false;
      }}
    }});
  </script>
</body>
</html>
"""
    return HTMLResponse(page)
