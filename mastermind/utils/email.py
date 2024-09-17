# mastermind/utils/email.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from email.mime.application import MIMEApplication

def send_email(subject, recipient, template, **kwargs):
    """Send an email via SMTP."""
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', True)

    SMTP_SENDER_NAME = os.getenv('SMTP_SENDER_NAME')
    SMTP_SENDER_EMAIL = os.getenv('SMTP_SENDER_EMAIL')
    SMTP_REPLY_TO = os.getenv('SMTP_REPLY_TO')

    sender = f"{SMTP_SENDER_NAME} <{SMTP_SENDER_EMAIL}>"

    # Render the email template with provided context
    html_body = render_template(template, **kwargs)

    # Create the MIME message
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    if SMTP_REPLY_TO:
        msg['Reply-To'] = SMTP_REPLY_TO

    # Attach the HTML body
    msg.attach(MIMEText(html_body, 'html'))

    try:
        # Establish a secure session with the server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
        current_app.logger.info(f"Email sent to {recipient}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {recipient}: {e}")
        return False
