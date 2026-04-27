import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText

SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.send']

class GmailService:
    def __init__(self, credentials_path=None, token_path=None, redirect_port=None):
        self.credentials_path = credentials_path or os.environ.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        self.token_path = token_path or os.environ.get('GOOGLE_TOKEN_PATH', 'token.json')
        self.redirect_port = int(redirect_port or os.environ.get('GOOGLE_OAUTH_REDIRECT_PORT', '53510'))
        self.creds = self.get_credentials()

    def get_credentials(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(f"Error: {self.credentials_path} not found.")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=self.redirect_port)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        return creds

    def get_service(self):
        if not self.creds:
            return None
        return build('gmail', 'v1', credentials=self.creds)

    def get_unread_emails_with_attachments(self, email, min_age_minutes=1, max_age_minutes=9):
        """Fetches unread emails with attachments from a time window (e.g., 1-9 minutes old)."""
        service = self.get_service()
        if not service:
            return []

        try:
            # Note: userId='me' refers to the authenticated user.
            # If the app is intended to check different users, each would need its own token.
            # For this implementation, we assume the provided token has access to the requested email.
            user_id = 'me' 
            query = f'is:unread has:attachment newer_than:{max_age_minutes}m older_than:{min_age_minutes}m'
            results = service.users().messages().list(userId=user_id, q=query).execute()
            messages = results.get('messages', [])
            email_data = []

            for message in messages:
                msg = service.users().messages().get(userId=user_id, id=message['id']).execute()
                payload = msg.get('payload', {})
                headers = payload.get('headers', [])
                
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')

                attachments = []
                parts = [payload]
                while parts:
                    part = parts.pop()
                    if part.get('parts'):
                        parts.extend(part.get('parts'))
                    
                    if part.get('filename'):
                        attachment_id = part.get('body', {}).get('attachmentId')
                        if attachment_id:
                            attachment = service.users().messages().attachments().get(
                                userId=user_id, messageId=message['id'], id=attachment_id).execute()
                            
                            file_data = base64.urlsafe_b64decode(attachment.get('data').encode('UTF-8'))
                            attachments.append({
                                'filename': part.get('filename'),
                                'data': file_data
                            })

                if attachments:
                    email_data.append({
                        'id': message['id'],
                        'subject': subject,
                        'sender': sender,
                        'attachments': attachments
                    })
                
                # Mark email as read
                service.users().messages().batchModify(
                    userId=user_id, 
                    body={'ids': [message['id']], 'removeLabelIds': ['UNREAD']}
                ).execute()

            return email_data
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def send_result_email(self, to, subject, body):
        service = self.get_service()
        if not service:
            return None

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        try:
            sent_message = service.users().messages().send(userId='me', body={'raw': raw}).execute()
            return sent_message
        except HttpError as error:
            print(f"An error occurred while sending email: {error}")
            return None
