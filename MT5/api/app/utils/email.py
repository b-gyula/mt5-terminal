import logging
import smtplib
from email.message import EmailMessage
from fastapi.exceptions import RequestValidationError
from app.utils.config import env
from app.models import mt5 as mt

logger = logging.getLogger(__name__)

def subject(r: mt.TradeRequest) -> str:
    return f"{mt.OrderType(r.type).name} {r.volume} {r.symbol} @ {r.price}"


def ex2subject(ex: Exception) -> str:
    match ex:
        case RequestValidationError():
            return ex.errors()[0]['msg']
        case _: return str(ex)


def send_order_mail(request: str, r: mt.TradeRequest | None, ex: Exception | None = None):
    if ex: # TODO for validation error format all errors()
        send_mail(f'Unable to create order: {ex2subject(ex)}', request, str(ex))
    else:
        send_mail(f"Order created {subject(r)}", request)


def send_mail(
    subject: str,
    request: str,
    error: str | None = None
) -> bool:
    """
    Send an email notification for order operations.

    Args:
        subject: Email subject line
        request: body of the original request
        error: Optional error message for failed orders

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    recipient   = env.SEND_ORDER_TO
    smtp_server = env.SMTP_SERVER
    smtp_port   = env.SMTP_PORT
    smtp_user   = env.SMTP_USER
    smtp_passwd = env.SMTP_PASSWD

    body = f"{subject}\nFrom:\n\n{request}"

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = env.SMTP_FROM
    msg['To'] = recipient
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_port > 25:
                server.starttls()
            if smtp_user and smtp_passwd:
                server.login(smtp_user, smtp_passwd)
            server.send_message(msg)
        logger.info(f"Order notification email sent to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
