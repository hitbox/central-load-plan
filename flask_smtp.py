import logging
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class SMTP:

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        # Default config
        app.config.setdefault('SMTP_SERVER', 'localhost')
        app.config.setdefault('SMTP_PORT', 25)
        app.config.setdefault('SMTP_USE_TLS', False)
        app.config.setdefault('SMTP_USE_SSL', False)
        app.config.setdefault('SMTP_USERNAME', None)
        app.config.setdefault('SMTP_PASSWORD', None)
        app.config.setdefault('SMTP_DEFAULT_SENDER', None)

        self.app = app

        # Attach the extension to the app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['smtp'] = self

    def test_smtp_connection(self):
        if self.app.config['SMTP_USE_SSL']:
            server_class = smtplib.SMTP_SSL
        else:
            server_class = smtplib.SMTP
        try:
            server = server_class(self.app.config['SMTP_SERVER'], self.app.config['SMTP_PORT'], timeout=10)
            if self.app.config['SMTP_USE_TLS'] and not self.app.config['SMTP_USE_SSL']:
                server.starttls()
            username = self.app.config['SMTP_USERNAME']
            password = self.app.config['SMTP_PASSWORD']
            if username and password:
                server.login(username, password)
        except Exception as e:
            raise RuntimeError(f"SMTP connection test failed: {e}")
        finally:
            server.quit()

    def send_email(self, subject, recipients, body, html=None, sender=None):
        if self.app is None:
            raise RuntimeError("Extension not initialized with Flask app")

        sender = sender or self.app.config['SMTP_DEFAULT_SENDER']
        if sender is None:
            raise ValueError("No sender configured")

        # Create message
        if html:
            msg = MIMEMultipart('alternative')
        else:
            msg = MIMEText(body)

        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)

        if html:
            msg.attach(MIMEText(body, 'plain'))
            msg.attach(MIMEText(html, 'html'))

        # Connect and send
        if self.app.config['SMTP_USE_SSL']:
            server_class = smtplib.SMTP_SSL
        else:
            server_class =  smtplib.SMTP
        server = server_class(self.app.config['SMTP_SERVER'], self.app.config['SMTP_PORT'])

        try:
            if self.app.config['SMTP_USE_TLS'] and not self.app.config['SMTP_USE_SSL']:
                server.starttls()
            username = self.app.config['SMTP_USERNAME']
            password = self.app.config['SMTP_PASSWORD']
            if username and password:
                server.login(username, password)
            server.sendmail(sender, recipients, msg.as_string())
            logger.info('Sent email %s to %s, from %s', subject, recipients, sender)
        finally:
            server.quit()
