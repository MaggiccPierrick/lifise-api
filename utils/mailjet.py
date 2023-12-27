from mailjet_rest import Client
from os import environ as env


class Mailjet:
	"""
	Class to interact with Mailjet API to send email
	"""
	def __init__(self):
		"""
		Initialize connection and feature with Mailjet API
		"""
		self.public_key = env['MAILJET_API_KEY']
		self.secret_key = env['MAILJET_API_SECRET']
		self.sender_mail = env['MAILJET_SENDER_EMAIL']
		self.sender_name = env['MAILJET_SENDER_NAME']
		self.connexion = Client(auth=(self.public_key, self.secret_key), version='v3.1')

	def send_basic_mail(self, to: dict, subject: str, txt_message: str, html_message: str = None):
		"""
		Send basic email with Mailjet
		:param self:
		:param to:
		:param subject:
		:param txt_message:
		:param html_message:
		:return:
		"""
		data = {
			'Messages': [{
				"From": {
					"Email": self.sender_mail,
					"Name": self.sender_name
				},
				"To": [{
					"Email": to.get('email'),
					"Name": to.get('name')
				}],
				"Subject": subject,
				"TextPart": txt_message,
				"HTMLPart": html_message
			}]
		}
		result = self.connexion.send.create(data=data)
		if result.status_code == 200:
			return True, 200, "Email sent"
		else:
			return False, 503, "Failed to send email"
