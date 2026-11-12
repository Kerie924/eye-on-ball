#!/usr/bin/env python3
"""Build Lance On Windows capture install/update guide as .docx (no third-party deps)."""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parents[1] / "docs" / "LanceOn-Windows-Capture-Guide.docx"

# Paragraph styles: title, h1, h2, h3, body, bullet, code, table handled separately
Content = list[tuple[str, str]]  # (kind, text)


def p(text: str, kind: str = "body") -> tuple[str, str]:
    return (kind, text)


GUIDE: Content = [
    p("Lance On — Guia de Instalacao e Atualizacao (Windows)", "title"),
    p("Software de captura no PC da quadra — somente versao Windows", "body"),
    p(
        "Este documento explica como instalar, configurar, testar, usar e atualizar "
        "o agente de captura Lance On em um PC Windows da quadra. "
        "O painel admin e a API ficam na nuvem; neste PC so e instalado o gravador.",
        "body",
    ),
    p("1. Visao geral", "h1"),
    p("O que fica onde", "h2"),
    p(
        "Nuvem (AWS): API + painel admin. O cliente abre o site no navegador "
        "(https://lanceonpara.com.br). Nada disso e instalado no PC da quadra.",
        "bullet",
    ),
    p(
        "PC da quadra (Windows): agente de captura. Grava os clips das cameras, "
        "ouve os botoes fisicos (Arduino USB) e envia os videos para a API "
        "(https://api.lanceonpara.com.br).",
        "bullet",
    ),
    p("Pasta principal da instalacao", "h2"),
    p(
        "Tudo e instalado em C:\\LanceOn (pasta visivel). Nao usa ProgramData. "
        "Se precisar de outra unidade: defina a variavel de ambiente LANCEON_HOME "
        "(exemplo: D:\\LanceOn) antes de instalar.",
        "body",
    ),
    p("2. Requisitos", "h1"),
    p("Windows 10 ou Windows 11.", "bullet"),
    p(
        "Python 3.11 ou superior (incluindo 3.15), baixado de https://www.python.org/downloads/ "
        "— NAO use o Python da Microsoft Store. Na instalacao, marque "
        "\"Add python.exe to PATH\" e mantenha tcl/tk habilitado (necessario para o painel).",
        "bullet",
    ),
    p(
        "FFmpeg no PATH. O Setup tenta instalar com winget (Gyan.FFmpeg). "
        "Se falhar, instale manualmente e reinicie o PC.",
        "bullet",
    ),
    p(
        "Cameras IP acessiveis na rede do PC (RTSP, tipicamente porta 554), "
        "com usuario e senha conhecidos.",
        "bullet",
    ),
    p(
        "Placa Arduino Uno/Nano (ou compativel) com o firmware lanceon_buttons.ino, "
        "conectada por USB, para os botoes fisicos da quadra.",
        "bullet",
    ),
    p(
        "Chave do dispositivo (device key) criada no painel admin para aquela quadra.",
        "bullet",
    ),
    p("3. Instalacao (primeira vez)", "h1"),
    p("Passo a passo", "h2"),
    p(
        "1. Copie a pasta capture do USB (ou do pacote recebido) para o PC — "
        "por exemplo Area de Trabalho, ou direto para C:\\LanceOn\\setup-src "
        "(caminho sem acentos ajuda a evitar erros de UAC).",
        "body",
    ),
    p(
        "2. Clique com o botao direito em LanceOn-Setup.bat → Executar como administrador.",
        "body",
    ),
    p(
        "3. No Setup App, preencha: URL da API (padrao https://api.lanceonpara.com.br), "
        "chave do dispositivo, quantidade de cameras, IP de cada camera, "
        "usuario/senha das cameras e, se quiser, a imagem da marca d'agua / logo.",
        "body",
    ),
    p(
        "4. Clique em Instalar e iniciar e aceite o UAC (controle de conta de usuario).",
        "body",
    ),
    p(
        "5. Ao terminar com sucesso, o Setup cria C:\\LanceOn\\, instala as dependencias "
        "Python em C:\\LanceOn\\capture\\.venv, grava C:\\LanceOn\\config.yaml, "
        "cria os atalhos .bat e a tarefa agendada LanceOnCapture (inicio no login).",
        "body",
    ),
    p("Arquivos e pastas apos a instalacao", "h2"),
    p("C:\\LanceOn\\ — pasta principal", "bullet"),
    p("C:\\LanceOn\\LanceOn.bat — app de controle (abrir sempre; tambem ha atalho na Area de Trabalho)", "bullet"),
    p("C:\\LanceOn\\capture\\ — software do agente", "bullet"),
    p("C:\\LanceOn\\config.yaml — configuracao (IPs, chave, logo, etc.)", "bullet"),
    p("C:\\LanceOn\\data\\ — buffers e fila de upload", "bullet"),
    p("C:\\LanceOn\\logs\\capture.log — log principal do gravador", "bullet"),
    p("C:\\LanceOn\\logs\\control-app-error.log — erros do painel de controle", "bullet"),
    p("C:\\LanceOn\\start-capture.bat / stop-capture.bat / status-capture.bat", "bullet"),
    p("Se a instalacao falhar (\"cannot find the specified path\")", "h2"),
    p("Nao use o Python da Microsoft Store. Reinstale o Python de python.org com PATH marcado.", "bullet"),
    p("Confira o log: C:\\LanceOn\\setup-staging\\lanceon-install.log", "bullet"),
    p("Instalacao manual (CMD como Administrador), se necessario:", "bullet"),
    p(
        "mkdir C:\\LanceOn\n"
        "cd /d C:\\caminho\\para\\capture\n"
        "python install_windows.py --source \"%CD%\" --settings C:\\LanceOn\\settings.json",
        "code",
    ),
    p("4. App de controle (uso diario)", "h1"),
    p(
        "Abra C:\\LanceOn\\LanceOn.bat ou o atalho \"Lance On\" na Area de Trabalho.",
        "body",
    ),
    p("Funcoes principais", "h2"),
    p("Ver se o gravador esta em execucao ou parado", "bullet"),
    p("Iniciar / Parar o gravador", "bullet"),
    p("Testar conexoes — cameras RTSP + placa Arduino USB (obrigatorio na primeira configuracao)", "bullet"),
    p("Alterar IPs das cameras, usuario e senha", "bullet"),
    p("Trocar a logo / marca d'agua e o tamanho no video (5–80% da altura; padrao 28)", "bullet"),
    p("Salvar e reiniciar gravador — aplica as mudancas", "bullet"),
    p("Abrir logs — abre a pasta C:\\LanceOn\\logs", "bullet"),
    p("Fluxo recomendado na primeira configuracao da quadra", "h2"),
    p("1. Preencha IPs e senha das cameras no painel.", "body"),
    p("2. Conecte o Arduino (com firmware lanceon_buttons.ino) na USB do PC.", "body"),
    p("3. Clique em Testar conexoes. Cada camera e os botoes devem mostrar [OK].", "body"),
    p(
        "4. Se aparecer [FALHOU], corrija IP/senha/rede/USB e teste de novo. "
        "A porta COM1 nativa do PC e ignorada de proposito (nao e o Arduino).",
        "body",
    ),
    p("5. Clique em Salvar e reiniciar gravador.", "body"),
    p("6. So entao use os botoes fisicos da quadra ou o botao PRONTO no app mobile.", "body"),
    p(
        "Na subida do gravador, o arquivo capture.log tambem imprime um bloco "
        "DIAGNOSTICO LANCE ON com o mesmo tipo de resultado.",
        "body",
    ),
    p("5. Botoes fisicos (Arduino) — pares fixos", "h1"),
    p(
        "Use Arduino Uno/Nano (USB) com o sketch em:\n"
        "capture\\firmware\\lanceon_buttons\\lanceon_buttons.ino",
        "body",
    ),
    p(
        "Grave o firmware com o Arduino IDE (placa correta + porta COM do Arduino). "
        "Ao conectar, a placa envia LANCEON_BUTTONS_READY na serial (115200 baud).",
        "body",
    ),
    p(
        "Ligue cada botao NO (normalmente aberto) entre o par de pinos (sinal + GND). "
        "Nunca altere estes pares — o software ja espera exatamente esta pinagem:",
        "body",
    ),
    p("CAM 1 → D2 (sinal) + D3 (GND)", "bullet"),
    p("CAM 2 → D4 (sinal) + D5 (GND)", "bullet"),
    p("CAM 3 → D6 (sinal) + D7 (GND)", "bullet"),
    p("CAM 4 → D8 (sinal) + D9 (GND)", "bullet"),
    p("CAM 5 → D10 (sinal) + D11 (GND)", "bullet"),
    p("CAM 6 → D12 (sinal) + D13 (GND)", "bullet"),
    p(
        "O agente escolhe automaticamente a porta USB (Arduino/CH340/CP210x). "
        "Nao escolha COM1 \"Communications Port\" do Windows — essa porta nativa "
        "nao e a placa de botoes.",
        "body",
    ),
    p(
        "Alem dos botoes fisicos, o app mobile (PRONTO) e o painel admin (Gravar) "
        "tambem disparam a gravacao pela internet.",
        "body",
    ),
    p("6. Atualizacao do software (sem reinstalar do zero)", "h1"),
    p("Atualizacao rapida (recomendada)", "h2"),
    p(
        "1. Copie a pasta capture nova (USB ou pacote) para o PC — pode ser uma pasta "
        "temporaria, por exemplo Area de Trabalho\\capture-nova.",
        "body",
    ),
    p(
        "2. Pare o gravador: abra Lance On → Parar, ou execute C:\\LanceOn\\stop-capture.bat.",
        "body",
    ),
    p(
        "3. Na pasta capture nova, execute repair-lanceon-launcher.bat "
        "(como Administrador se o Windows pedir). Isso atualiza "
        "C:\\LanceOn\\LanceOn.bat, control_app.py, a pasta agent\\ e o stop-capture.bat.",
        "body",
    ),
    p(
        "4. Abra C:\\LanceOn\\LanceOn.bat, clique em Testar conexoes e depois "
        "Salvar e reiniciar gravador (ou Iniciar).",
        "body",
    ),
    p("Atualizacao completa (reinstalacao limpa)", "h2"),
    p(
        "Use quando a atualizacao rapida nao bastar (mudanca grande de dependencias, "
        "venv quebrado, etc.):",
        "body",
    ),
    p("1. Pare o gravador (stop-capture.bat).", "body"),
    p(
        "2. (Opcional) Faça backup de C:\\LanceOn\\config.yaml e da pasta "
        "C:\\LanceOn\\capture\\assets\\ se a logo personalizada estiver la.",
        "body",
    ),
    p(
        "3. Rode de novo LanceOn-Setup.bat como Administrador a partir da pasta capture nova. "
        "O instalador recria C:\\LanceOn\\capture, o .venv e a tarefa agendada, "
        "mantendo o fluxo de configuracao no Setup App.",
        "body",
    ),
    p("4. Confirme IPs/chave/logo, instale, teste conexoes e reinicie.", "body"),
    p("O que NAO precisa reinstalar a cada update", "h2"),
    p("Python do sistema (desde que continue 3.11+ com tcl/tk).", "bullet"),
    p("FFmpeg (se ja estiver no PATH).", "bullet"),
    p("Firmware do Arduino (so se o arquivo .ino tiver mudado).", "bullet"),
    p("7. Arranque automatico e comandos uteis", "h1"),
    p(
        "O gravador inicia no login do usuario via tarefa agendada LanceOnCapture "
        "(necessario para sessao interativa). Em PC de quadra, configure login automatico no Windows.",
        "body",
    ),
    p("Comandos (CMD):", "body"),
    p(
        "schtasks /Run /TN LanceOnCapture\n"
        "schtasks /End /TN LanceOnCapture\n"
        "type C:\\LanceOn\\logs\\capture.log",
        "code",
    ),
    p("Ou use os arquivos start-capture.bat, stop-capture.bat e status-capture.bat em C:\\LanceOn\\.", "body"),
    p("8. Solucao de problemas", "h1"),
    p("LanceOn.bat abre o CMD e fecha na hora", "h2"),
    p("Rode repair-lanceon-launcher.bat a partir da pasta capture atualizada.", "bullet"),
    p("Ou execute novamente LanceOn-Setup.bat.", "bullet"),
    p(
        "Leia C:\\LanceOn\\logs\\control-app-error.log. "
        "Erro comum: Python sem tcl/tk — reinstale o Python de python.org.",
        "bullet",
    ),
    p("Painel abre mas mostra erro de wmic / WinError 2", "h2"),
    p(
        "Versoes recentes do Windows 11 removeram o wmic. Use a versao atualizada do "
        "control_app.py (via repair-lanceon-launcher.bat). O status passa a usar PowerShell.",
        "body",
    ),
    p("Log diz que esta aguardando trigger, mas nao ha camera / Arduino", "h2"),
    p(
        "Versoes antigas podiam escolher COM1 nativo e iniciar buffers sem validar RTSP. "
        "Na versao atual: use Testar conexoes; o log mostra [FALHOU] com causa; "
        "COM1 e ignorado; a placa so e aceita apos LANCEON_BUTTONS_READY.",
        "body",
    ),
    p("Camera [FALHOU] no teste", "h2"),
    p("Confirme IP na mesma rede do PC; ping no IP da camera.", "bullet"),
    p("Confirme usuario/senha RTSP (erro 401 = credenciais).", "bullet"),
    p("Confirme que a camera responde em rtsp://usuario:senha@IP:554/...", "bullet"),
    p("Confirme que o FFmpeg esta instalado (ffmpeg -version no CMD).", "bullet"),
    p("Botoes [FALHOU] / placa nao encontrada", "h2"),
    p("Conecte o Arduino por USB; no Gerenciador de Dispositivos deve aparecer porta COM USB (CH340/Arduino).", "bullet"),
    p("Grave o firmware lanceon_buttons.ino na placa.", "bullet"),
    p("Pare o gravador antes do teste se a porta estiver \"em uso\".", "bullet"),
    p("Nao use COM1 Communications Port do PC.", "bullet"),
    p("Clips nao aparecem no app", "h2"),
    p(
        "O botao grava localmente mesmo sem internet; o upload vai para a fila. "
        "O app so mostra o video depois que a API recebe o arquivo. "
        "Confira C:\\LanceOn\\logs\\capture.log e a pasta C:\\LanceOn\\data\\.",
        "body",
    ),
    p("9. Comportamento do clip e da fila", "h1"),
    p(
        "No momento do botao, o gravador fecha o segmento ao vivo e monta os ultimos "
        "30 segundos ate o press. Segmentos curtos (2s) evitam o clip terminar cedo demais.",
        "body",
    ),
    p(
        "Sem internet: clips ficam na fila e sobem quando a API voltar. "
        "Itens com mais de 48 h ou se a fila passar de ~4 GB podem ser descartados.",
        "body",
    ),
    p("10. Checklist rapido para o tecnico / cliente", "h1"),
    p("Python 3.11+ (python.org) no PATH, com tcl/tk", "bullet"),
    p("FFmpeg no PATH", "bullet"),
    p("LanceOn-Setup.bat executado como Administrador → INSTALL_OK", "bullet"),
    p("C:\\LanceOn\\LanceOn.bat abre o painel", "bullet"),
    p("Testar conexoes → todas as cameras [OK] e botoes [OK]", "bullet"),
    p("Salvar e reiniciar → capture.log com DIAGNOSTICO OK", "bullet"),
    p("Pressionar botao fisico → nova linha de trigger no log e clip na fila/upload", "bullet"),
    p("Apos update: repair-lanceon-launcher.bat + Testar conexoes de novo", "bullet"),
    p("11. Contatos / URLs", "h1"),
    p("Site / admin: https://lanceonpara.com.br", "bullet"),
    p("API: https://api.lanceonpara.com.br", "bullet"),
    p("App Android: https://play.google.com/store/apps/details?id=com.lanceon.app", "bullet"),
    p(
        "Documento gerado para a versao Windows do software de captura Lance On. "
        "Nao inclui instalacao Ubuntu/Raspberry Pi.",
        "body",
    ),
]


def _runs_xml(text: str, *, bold: bool = False, mono: bool = False, size: int = 22) -> str:
    """size is half-points (22 = 11pt)."""
    fonts = (
        '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'
        if mono
        else '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'
    )
    bold_xml = "<w:b/>" if bold else ""
    parts: list[str] = []
    for i, line in enumerate(text.split("\n")):
        if i:
            parts.append("<w:r><w:br/></w:r>")
        parts.append(
            "<w:r>"
            f"<w:rPr>{fonts}{bold_xml}<w:sz w:val=\"{size}\"/><w:szCs w:val=\"{size}\"/></w:rPr>"
            f"<w:t xml:space=\"preserve\">{escape(line)}</w:t>"
            "</w:r>"
        )
    return "".join(parts)


def _paragraph_xml(kind: str, text: str) -> str:
    if kind == "title":
        return (
            f'<w:p><w:pPr><w:spacing w:after="200"/>'
            f'<w:jc w:val="center"/></w:pPr>'
            f"{_runs_xml(text, bold=True, size=36)}</w:p>"
        )
    if kind == "h1":
        return (
            f'<w:p><w:pPr><w:spacing w:before="360" w:after="160"/>'
            f'<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="4" w:color="1E8F4A"/></w:pBdr>'
            f"</w:pPr>{_runs_xml(text, bold=True, size=28)}</w:p>"
        )
    if kind == "h2":
        return (
            f'<w:p><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>'
            f"{_runs_xml(text, bold=True, size=24)}</w:p>"
        )
    if kind == "bullet":
        return (
            '<w:p><w:pPr><w:spacing w:after="80"/>'
            '<w:ind w:left="360" w:hanging="180"/></w:pPr>'
            f"{_runs_xml('• ' + text, size=21)}</w:p>"
        )
    if kind == "code":
        return (
            '<w:p><w:pPr><w:spacing w:before="120" w:after="120"/>'
            '<w:shd w:val="clear" w:fill="F3F4F6"/>'
            '<w:ind w:left="120" w:right="120"/></w:pPr>'
            f"{_runs_xml(text, mono=True, size=18)}</w:p>"
        )
    # body
    return (
        f'<w:p><w:pPr><w:spacing w:after="120"/></w:pPr>'
        f"{_runs_xml(text, size=21)}</w:p>"
    )


def build_document_xml(items: Content) -> str:
    body = "".join(_paragraph_xml(kind, text) for kind, text in items)
    body += '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>' \
            '<w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080"/>' \
            "</w:sectPr>"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<w:body>{body}</w:body></w:document>"
    )


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    document_xml = build_document_xml(GUIDE)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", RELS)
        zf.writestr("word/document.xml", document_xml)
        zf.writestr("word/_rels/document.xml.rels", DOC_RELS)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
