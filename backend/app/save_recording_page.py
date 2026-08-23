from json import dumps

from fastapi.responses import HTMLResponse


def save_recording_html(download_url: str, recording_id: int) -> HTMLResponse:
    url_js = dumps(download_url)
    page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Lance On — Baixar video</title>
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
      gap: 14px;
      text-align: center;
    }}
    h1 {{ margin: 0; font-size: 24px; }}
    p {{ color: #a3a3a3; margin: 0; }}
    a {{
      display: block;
      border-radius: 10px;
      padding: 14px 16px;
      background: #16a34a;
      color: #fff;
      font-weight: 700;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <main>
    <h1>Baixar video</h1>
    <p>O download deve iniciar sozinho. Se nao iniciar, toque no botao.</p>
    <a id="dl" href={url_js} download="lance-{recording_id}.mp4">Baixar video</a>
  </main>
  <script>
    const url = {url_js};
    window.location.replace(url);
  </script>
</body>
</html>
"""
    return HTMLResponse(page)
