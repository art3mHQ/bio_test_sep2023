from time import sleep

from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from config import celery_app

User = get_user_model()


@celery_app.task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()


# @shared_task()
@celery_app.task()
def send_feedback_email_task(email_address):
    """Sends an email when the user deleted."""
    sleep(5)  # Simulate expensive operation(s) that freeze Django
    send_mail(
        "Your account was deleted",
        f"\t{email_address}\n\nGoodbay, Thank you!",
        "fff-support@example.com",
        [email_address],
        fail_silently=False,
    )


@celery_app.task()
def send_otp_task(email_address, otp):
    """Sends an otp when needed."""
    send_mail(
        "Your OTP is:",
        f"\t{otp}\n\n otp will expire in 10 minutes, Thank you!",
        "fff-support@example.com",
        [email_address],
        fail_silently=False,
    )
