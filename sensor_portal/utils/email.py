import logging
from typing import List

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from user_management.models import User

logger = logging.getLogger(__name__)


def send_email_to_users(users: List[User], subject: str, body: str) -> None:
    """
    Sends an email with the given subject and body to a list of User objects.

    Args:
        users (List[User]): List of user objects to send the email to.
        subject (str): Subject of the email.
        body (str): Email body content.
    """
    for user in users:
        send_email_to_user(user, subject, body)


def send_email_to_user(user: User, subject: str, body: str) -> None:
    """
    Sends an email to a single user if the user does not have a related deviceuser.

    Args:
        user (User): Django User object to send the email to.
        subject (str): Subject of the email.
        body (str): Email body content.
    """
    try:
        user.deviceuser
        return
    except User.deviceuser.RelatedObjectDoesNotExist:
        pass

    new_body = render_to_string(
        "email_body.html", {"user": user, "body": body})

    send_email(user.email, subject, new_body)


def send_email(to_email: str | List[str], subject: str, body: str) -> None:
    """
    Sends an HTML email to one or more recipients.

    Args:
        to_email (str | List[str]): Recipient email address(es).
        subject (str): Subject of the email.
        body (str): HTML content of the email.

    Raises:
        ValueError: If 'to_email' is not provided.
    """
    try:
        settings.EMAIL_HOST_USER
    except AttributeError:
        logger.error("No email sender configured")
        return

    if not to_email:
        raise ValueError(
            "The 'to_email' address must be provided and cannot be empty.")
    elif not isinstance(to_email, list):
        to_email = [to_email]

    try:
        html_message = render_to_string(
            "email.html", {"body": body})
        message = EmailMessage(subject=subject,
                               body=html_message,
                               from_email=settings.EMAIL_HOST_USER,
                               to=to_email)
        message.content_subtype = 'html'
        result = message.send()
        logger.info(
            f"Sending email to {', '.join(to_email)} with subject: {subject} - Status {result}")
    except Exception as e:
        logger.error(
            f"Sending email to {', '.join(to_email)} with subject: {subject} - Status 0")
        logger.error(e)
