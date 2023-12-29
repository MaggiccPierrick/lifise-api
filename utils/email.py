import re
import threading

from flask_mail import Mail, Message
from flask import copy_current_request_context
from os import environ as env

from utils.log import Logger


def check_email_format(email_address):
    """
    Verify that the email address has the good format xxx@yyy.zzz
    :param email_address:
    :return:
    """
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.fullmatch(regex, email_address):
        return True
    else:
        return False


class Email:
    """
    Class to send an email using smtp parameters from config file
    """
    def __init__(self, flask_app):
        self.app = flask_app
        self.log = Logger()
        self.sender = (env['EMAIL_DISPLAY_NAME'], env['EMAIL_ADDRESS'])

    def send_async(self, subject, recipients, body=None, html=None, bcc=None):
        """
        Send email asynchronously according to parameters
        :return: True if email sent
        """
        if html is None and body is None:
            return False
        if not isinstance(recipients, list):
            return False
        try:
            @copy_current_request_context
            def send_message(message):
                mail.send(message)

            mail = Mail(self.app)
            if body is None:
                msg = Message(subject=subject, html=html, sender=self.sender, recipients=recipients, bcc=bcc)
            elif html is None:
                msg = Message(subject=subject, body=body, sender=self.sender, recipients=recipients, bcc=bcc)
            else:
                msg = Message(subject=subject, body=body, html=html, sender=self.sender, recipients=recipients, bcc=bcc)
            sender = threading.Thread(name='mail_sender', target=send_message, args=(msg,))
            sender.start()
            return True
        except Exception as e:
            self.log.error("Failed to send email. Error = {0}".format(e))
            return False
