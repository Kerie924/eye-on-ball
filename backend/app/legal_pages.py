from fastapi.responses import HTMLResponse


def _shell(title: str, body: str) -> HTMLResponse:
    page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Lance On — {title}</title>
  <style>
    body {{
      margin: 0;
      font-family: system-ui, sans-serif;
      background: #0a0a0a;
      color: #f5f5f5;
    }}
    main {{
      width: min(720px, 100%);
      margin: 0 auto;
      padding: 32px 20px 64px;
      line-height: 1.6;
    }}
    h1 {{ color: #22c55e; }}
    h2 {{ margin-top: 28px; font-size: 18px; }}
    p, li {{ color: #d4d4d4; }}
    a {{ color: #4ade80; }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    {body}
  </main>
</body>
</html>
"""
    return HTMLResponse(page)


def privacy_html() -> HTMLResponse:
    return _shell(
        "Politica de privacidade",
        """
    <p>Ultima atualizacao: 24 de agosto de 2026.</p>
    <p>O Lance On (“nos”) opera o aplicativo e o site lanceonpara.com.br para gravacao e compartilhamento de lances de futebol.</p>
    <h2>Dados que coletamos</h2>
    <ul>
      <li>Conta: nome, e-mail, senha (armazenada de forma criptografada) e, se voce usar Google ou Apple, o identificador da conta.</li>
      <li>Perfil: foto de avatar, se voce enviar uma.</li>
      <li>Uso: pedidos de acesso a quadras, gravacoes que voce assiste ou baixa, e relatos de erro com fotos opcionais.</li>
      <li>Dispositivo: identificadores necessarios para login e notificacoes de sessao.</li>
    </ul>
    <h2>Como usamos</h2>
    <p>Usamos esses dados para autenticar voce, mostrar videos da sua quadra, melhorar o app e responder relatos de suporte. Nao vendemos seus dados.</p>
    <h2>Compartilhamento</h2>
    <p>Videos e arquivos podem ser armazenados em servidores de nuvem (Amazon S3 ou equivalente). E-mails de conta podem ser enviados pelo provedor de e-mail da plataforma. Login pode usar Google ou Apple, que recebem apenas o necessario para autenticar voce.</p>
    <h2>LGPD</h2>
    <p>Tratamos dados pessoais para executar o contrato de uso do app. Voce pode acessar, corrigir ou excluir seus dados pelo proprio aplicativo.</p>
    <h2>Retencao</h2>
    <p>Gravacoes expiram conforme a politica da quadra (em geral 48 horas). Dados de conta permanecem enquanto a conta existir. Relatos de erro podem ser guardados para suporte.</p>
    <h2>Seus direitos</h2>
    <p>Voce pode editar o perfil no app e excluir a conta em Perfil → Excluir conta. Para outras solicitacoes, fale com suporte@lanceonpara.com.br.</p>
    <h2>Contato</h2>
    <p>Lance On Para — <a href="mailto:suporte@lanceonpara.com.br">suporte@lanceonpara.com.br</a></p>
        """,
    )


def terms_html() -> HTMLResponse:
    return _shell(
        "Termos de uso",
        """
    <p>Ultima atualizacao: 24 de agosto de 2026.</p>
    <p>Ao criar uma conta no Lance On, voce concorda com estes termos.</p>
    <h2>O servico</h2>
    <p>O app permite que atletas e olheiros vejam lances gravados em quadras parceiras, dentro do periodo de validade de cada video.</p>
    <h2>Conta</h2>
    <p>Voce e responsavel pelas informacoes da conta. Olheiros podem precisar de aprovacao. Voce pode excluir a conta a qualquer momento no aplicativo.</p>
    <h2>Conteudo</h2>
    <p>Os videos pertencem as quadras e a plataforma. E proibido republicar, vender ou usar as gravacoes de forma ilegal ou ofensiva.</p>
    <h2>Disponibilidade</h2>
    <p>Gravacoes dependem de cameras, internet da quadra e armazenamento. Interrupcoes podem ocorrer.</p>
    <h2>Contato</h2>
    <p><a href="mailto:suporte@lanceonpara.com.br">suporte@lanceonpara.com.br</a></p>
        """,
    )
