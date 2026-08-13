import logging
import smtplib

from flask import current_app

from contextlib import redirect_stderr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
        server = server_class(
            self.app.config['SMTP_SERVER'],
            self.app.config['SMTP_PORT'],
            timeout = 10,
        )
        try:
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

    def _send(self, server, sender, recipients, msg):
        if self.app.config['SMTP_USE_TLS']:
            server.starttls()

        username = self.app.config['SMTP_USERNAME']
        password = self.app.config['SMTP_PASSWORD']
        if username and password:
            server.login(username, password)

        try:
            server.sendmail(sender, recipients, msg.as_string())
        finally:
            server.quit()

    def send_email(self, msg, subject, recipients, body, html=None, sender=None):
        if self.app is None:
            raise RuntimeError("Extension not initialized with Flask app")

        sender = sender or self.app.config['SMTP_DEFAULT_SENDER']
        if sender is None:
            raise ValueError("No sender configured")

        # Connect and send
        if self.app.config['SMTP_USE_SSL']:
            server_class = smtplib.SMTP_SSL
        else:
            server_class =  smtplib.SMTP
        server = server_class(self.app.config['SMTP_SERVER'], self.app.config['SMTP_PORT'])

        debug_level = int(self.app.config.get('SMTP_DEBUG_LEVEL', '0'))
        debug_file = self.app.config.get('SMTP_DEBUG_LOG')

        if debug_level:
            if not debug_file:
                raise ValueError(
                    'setting {SMTP_DEBUG_LEVEL=} requires SMTP_DEBUG_LOG set'
                    ' as path to logging file.')

            # Set SMTP debugging and redirect to file.
            server.set_debuglevel(debug_level)
            with open(debug_file, 'a') as smtp_log_file:
                with redirect_stderr(smtp_log_file):
                    self._send(server, sender, recipients, msg)
        else:
            self._send(server, sender, recipients, msg)

        current_app.logger.info('Sent email %s to %s, from %s', subject, recipients, sender)
