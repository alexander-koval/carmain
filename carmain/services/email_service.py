from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from carmain.core.config import get_settings


async def send_verification_email(to_email: str, token: str) -> None:
    """
    Send a verification email with the given token via FastAPI-Mail.
    """
    settings = get_settings()
    verify_url = f"{settings.app_url}/v1/auth/verify"
    subject = "Verify your email"
    body = f"Click the link to verify your account: {verify_url}?token={token}"

    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=body,
        subtype=MessageType.plain,
    )
    fm = FastMail(
        ConnectionConfig(
            MAIL_USERNAME=settings.smtp_user,
            MAIL_PASSWORD=settings.smtp_password,
            MAIL_FROM=settings.smtp_from,
            MAIL_PORT=settings.smtp_port,
            MAIL_SERVER=settings.smtp_host,
            MAIL_TLS=True,
            MAIL_SSL=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
    )
    await fm.send_message(message)


async def send_password_reset_email(to_email: str, token: str) -> None:
    """
    Send a verification email with the given token via FastAPI-Mail.
    """
    settings = get_settings()
    verify_url = f"{settings.app_url}/v1/auth/verify"
    subject = "Verify your email"
    body = f"Click the link to verify your account: {verify_url}?token={token}"

    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=body,
        subtype=MessageType.plain,
    )
    fm = FastMail(
        ConnectionConfig(
            MAIL_USERNAME=settings.smtp_user,
            MAIL_PASSWORD=settings.smtp_password,
            MAIL_FROM=settings.smtp_from,
            MAIL_PORT=settings.smtp_port,
            MAIL_SERVER=settings.smtp_host,
            MAIL_TLS=True,
            MAIL_SSL=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
    )
    await fm.send_message(message)
