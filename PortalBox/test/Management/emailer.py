import logging
import urequests
import json
import configparser

class Emailer:
    '''
    Bind settings in a class for reuse
    '''

    def __init__(self, settings):
        self.settings = settings

    def send(self, to, subject, body):
        """
        Send an email using the configured settings.

        params:
            to - The email address to which to send the email.
                can be a string for 1 recipient or an array for multiple recipients 
            subject - The subject for the email
            body - The message body for the email
        """
        if isinstance(to, str):
            to = [to]

        # Prepare the email content as a dictionary
        email_data = {
            "from": self.settings['from_address'],
            "to": to,
            "subject": subject,
            "text": body
        }

        # Add optional CC and BCC if available
        if 'cc_address' in self.settings:
            email_data["cc"] = self.settings['cc_address']
        if 'bcc_address' in self.settings:
            email_data["bcc"] = self.settings['bcc_address']
        if 'reply_to' in self.settings:
            email_data["reply_to"] = self.settings['reply_to']

        # Send the email via an HTTP POST request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.settings['api_key']}"  # Assuming API key authentication
        }

        email_service_url = self.settings.get('email_service_url', 'https://api.mailgun.net/v3/your_domain.com/messages') 
        
        try:
            response = urequests.post(email_service_url, headers=headers, json=email_data)
            if response.status_code == 200:
                logging.info(f"Emailed: {to} about: {subject}")
            else:
                logging.error(f"Failed to send email. Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            logging.error(f"Error sending email: {e}")


# Rest of this file is the test suite. Use `python3 Email.py` to run
# check prevents running of test suite if loading (import) as a module
if __name__ == "__main__":
    # standard library
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    # Read our Configuration
    settings = configparser.ConfigParser()
    settings.read('config.ini')

    # Connect to the Emailer backend service (e.g., Mailgun, Sendinblue, Gmail API)
    emailer = Emailer(settings['email'])

    # Send an email
    emailer.send(settings['email']['cc_address'], "Hello World", "Greetings Developer. You have tested the Emailer module.")
