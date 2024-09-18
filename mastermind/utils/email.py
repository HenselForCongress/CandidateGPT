# mastermind/utils/email.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from email.mime.application import MIMEApplication
from .logging import logger

def send_email(subject, recipient, template, **kwargs):
    """Send an email via SMTP."""
    logger.debug(f"📧 Preparing to send email to {recipient} with subject: '{subject}'. Ready for it?")

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
    try:
        html_body = render_template(template, **kwargs)
        logger.debug("📝 Email template rendered successfully. Everything has changed!")
    except Exception as e:
        logger.error(f"❌ Error rendering email template: {e}. This is why we can't have nice things.")
        return False

    # Create the MIME message
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    if SMTP_REPLY_TO:
        msg['Reply-To'] = SMTP_REPLY_TO

    # Attach the HTML body
    msg.attach(MIMEText(html_body, 'html'))
    logger.debug("📎 Attached HTML content to the email message. All you had to do was stay.")

    try:
        # Establish a secure session with the server
        logger.debug("🔒 Establishing secure session with the SMTP server. Wildest dreams await!")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        if SMTP_USE_TLS:
            server.starttls()
            logger.debug("🔐 Started TLS session with the SMTP server.")

        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        logger.debug("🔑 Logged in to the SMTP server.")

        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
        logger.info(f"✅ Email sent successfully to {recipient}. You belong with me!")
        return True
    except smtplib.SMTPException as smtp_e:
        logger.error(f"🔥 SMTP error occurred while sending email to {recipient}: {smtp_e}. I knew you were trouble.")
        return False
    except Exception as e:
        logger.error(f"❗ General error occurred while sending email to {recipient}: {e}. Fearless fail!")
        return False
