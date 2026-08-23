import logging
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, parseaddr

from app.config import settings

logger = logging.getLogger(__name__)


def email_configured() -> bool:
    return bool(settings.smtp_host or settings.ses_from_email)


def public_smtp_error(exc: BaseException) -> str:
    text = str(exc).replace("\n", " ").strip() or type(exc).__name__
    if settings.smtp_password:
        text = text.replace(settings.smtp_password, "***")
    if "535" in text or "authentication failed" in text.lower():
        return (
            "autenticacao SMTP recusada (erro 535). "
            "SMTP_PORT deve ser 465 ou 587 — 535 nao e porta. "
            "Confira SMTP_USER (e-mail completo) e SMTP_PASSWORD (senha da caixa Hostinger)."
        )
    if "timed out" in text.lower() or "timeout" in text.lower():
        return (
            "conexao SMTP expirou. Use SMTP_PORT=465 (ou 587), nao 535. "
            "Host: smtp.titan.email ou smtp.hostinger.com"
        )
    return text[:240]


def send_password_reset_email(to_email: str, reset_url: str, app_url: str) -> None:
    subject = "Redefinir sua senha — Lance On"
    text = (
        "Recebemos um pedido para redefinir a senha da sua conta Lance On.\n\n"
        "Se foi voce, abra este link (expira em 1 hora):\n"
        f"{reset_url}\n\n"
        "Se o app estiver instalado, voce tambem pode usar:\n"
        f"{app_url}\n\n"
        "Se nao foi voce, ignore este e-mail. Sua senha permanece a mesma."
    )
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<body style="font-family:system-ui,sans-serif;background:#0a0a0a;color:#f5f5f5;padding:24px;">
  <h1 style="color:#22c55e;">Lance On</h1>
  <p>Recebemos um pedido para redefinir a senha da sua conta.</p>
  <p>
    <a href="{reset_url}" style="display:inline-block;background:#16a34a;color:#fff;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:700;">
      Redefinir senha
    </a>
  </p>
  <p style="color:#a3a3a3;font-size:14px;">O link expira em 1 hora. Se voce nao pediu isso, ignore este e-mail.</p>
</body>
</html>"""

    mailbox = _mailbox_address()
    from_header = formataddr(("Lance On", mailbox))
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_header
    message["To"] = to_email
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    if settings.smtp_host:
        _send_smtp(message, mailbox)
        return
    if settings.ses_from_email:
        _send_ses(to_email, mailbox, subject, text, html)
        return

    raise RuntimeError("Nenhum provedor de e-mail configurado (SMTP_HOST ou SES_FROM_EMAIL)")


def _mailbox_address() -> str:
    raw = (
        settings.smtp_user
        or settings.smtp_from
        or settings.ses_from_email
        or settings.admin_email
    )
    _name, address = parseaddr(raw or "")
    if address and "@" in address:
        return address
    match = re.search(r"[^<\s]+@[^>\s]+", raw or "")
    if match:
        return match.group(0)
    return (raw or "").strip()


def _send_smtp(message: EmailMessage, mailbox: str) -> None:
    host = (settings.smtp_host or "").strip()
    port = int(settings.smtp_port)
    if port not in {465, 587}:
        raise RuntimeError(
            f"SMTP_PORT={port} e invalido. Use 465 (SSL) ou 587 (TLS). "
            "535 e codigo de senha errada, nao e porta."
        )
    user = (settings.smtp_user or mailbox).strip().strip('"').strip("'")
    password = (settings.smtp_password or "").strip().strip('"').strip("'")
    if not user or "@" not in user:
        raise RuntimeError("SMTP_USER deve ser o e-mail completo, ex: noreply@lanceonpara.com.br")
    if not password:
        raise RuntimeError("SMTP_PASSWORD esta vazio. Use a senha da caixa de e-mail Hostinger.")
    context = ssl.create_default_context()
    server: smtplib.SMTP | None = None

    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=20, context=context)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
        if user:
            server.login(user, password)
        server.send_message(message, from_addr=mailbox)
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                try:
                    server.close()
                except Exception:
                    pass


def _send_ses(to_email: str, from_address: str, subject: str, text: str, html: str) -> None:
    import boto3

    kwargs: dict = {"region_name": settings.s3_region}
    using_minio = bool(settings.s3_endpoint_url)
    if settings.s3_access_key and settings.s3_secret_key and not using_minio:
        kwargs["aws_access_key_id"] = settings.s3_access_key
        kwargs["aws_secret_access_key"] = settings.s3_secret_key

    client = boto3.client("ses", **kwargs)
    client.send_email(
        Source=from_address,
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": text, "Charset": "UTF-8"},
                "Html": {"Data": html, "Charset": "UTF-8"},
            },
        },
    )
