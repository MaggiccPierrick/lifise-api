import re

from os import environ as env
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail as SendgridMail

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


class Sendgrid:
    """
    Class to send an email using smtp parameters from config file
    """
    def __init__(self):
        self.log = Logger()
        self.api_key = env['SENDGRID_API_KEY']
        self.sender = (env['SENDGRID_SENDER_EMAIL'], env['SENDGRID_SENDER_NAME'])
        self.template_id = env['SENDGRID_TEMPLATE_ID']

    def send_email(self, to_emails: list, subject: str, txt_content: str, token: str = None):
        """

        :param to_emails: list of email addresses
        :param subject:
        :param txt_content:
        :param token:
        :return:
        """
        if len(to_emails) > 1:
            message = SendgridMail(from_email=self.sender, to_emails=self.sender)
            for email_address in to_emails:
                message.add_bcc(email_address)
        else:
            message = SendgridMail(from_email=self.sender, to_emails=to_emails)

        message.dynamic_template_data = {
            'subject': subject,
            'custom_message': txt_content,
            'token': token
        }
        message.template_id = self.template_id
        try:
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            if response.status_code >= 300:
                self.log.error("Sending email failed , status code : {0}".format(response.status_code))
                return False
        except Exception as e:
            self.log.error("Sending email failed with error : {0}".format(e))
            return False
        return True
