import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def email_configured() -> bool:
    return bool(settings.smtp_host or settings.ses_from_email)


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

    from_address = (
        settings.smtp_from
        or settings.ses_from_email
        or settings.admin_email
    )
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_address
    message["To"] = to_email
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    if settings.smtp_host:
        _send_smtp(message)
        return
    if settings.ses_from_email:
        _send_ses(to_email, from_address, subject, text, html)
        return

    raise RuntimeError("Nenhum provedor de e-mail configurado (SMTP_HOST ou SES_FROM_EMAIL)")


def _send_smtp(message: EmailMessage) -> None:
    port = settings.smtp_port
    if port == 465:
        server = smtplib.SMTP_SSL(settings.smtp_host, port, timeout=20)
    else:
        server = smtplib.SMTP(settings.smtp_host, port, timeout=20)
    try:
        if settings.smtp_use_tls and port != 465:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password or "")
        server.send_message(message)
    finally:
        server.quit()


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
