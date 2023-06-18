from flask import Blueprint, current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

email = Blueprint("email", __name__, template_folder="templates")


def send_email(to, subject, html_content):
    SENDGRID_API_KEY = current_app.config["SENDGRID_API_KEY"]
    FROM_EMAIL = current_app.config["FROM_EMAIL"]
    APP_NAME = current_app.config["APP_NAME"]

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to,
        subject=f"[{APP_NAME}] {subject}",
        html_content=html_content,
    )

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    return response
