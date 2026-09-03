from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr


@dataclass(frozen=True)
class EmailSettings:
    enabled: bool
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str
    reply_to: str

    @classmethod
    def from_env(cls) -> "EmailSettings":
        return cls(
            enabled=os.getenv("EMAIL_ENABLED", "false").lower() in {"1", "true", "yes"},
            host=os.getenv("SES_SMTP_HOST", "email-smtp.us-west-1.amazonaws.com"),
            port=int(os.getenv("SES_SMTP_PORT", "587")),
            username=os.getenv("SES_SMTP_USERNAME", ""),
            password=os.getenv("SES_SMTP_PASSWORD", ""),
            from_email=os.getenv("SES_FROM_EMAIL", ""),
            from_name=os.getenv("SES_FROM_NAME", "GFCRI"),
            reply_to=os.getenv("SES_REPLY_TO", ""),
        )

    @property
    def configured(self) -> bool:
        return self.enabled and bool(self.username and self.password and self.from_email)


class EmailService:
    def __init__(self, settings: EmailSettings | None = None):
        self.settings = settings or EmailSettings.from_env()

    @property
    def configured(self) -> bool:
        return self.settings.configured

    def send(self, *, to_email: str, subject: str, text_body: str, html_body: str) -> None:
        if not self.configured:
            raise RuntimeError("Email service is not configured")
        message = EmailMessage()
        message["From"] = formataddr((self.settings.from_name, self.settings.from_email))
        message["To"] = to_email
        message["Subject"] = subject
        if self.settings.reply_to:
            message["Reply-To"] = self.settings.reply_to
        message["List-Unsubscribe"] = "<https://gfcrilabs.com/api/notifications/unsubscribe>"
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")
        with smtplib.SMTP(self.settings.host, self.settings.port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(self.settings.username, self.settings.password)
            smtp.send_message(message)
