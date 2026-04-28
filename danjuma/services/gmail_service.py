import os
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from models.database import get_oauth_token, save_oauth_token

SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.send']

class GmailService:
    def __init__(self, email=None, credentials_path=None, redirect_port=None):
        self.email = email
        self.credentials_path = credentials_path or os.environ.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        self.redirect_port = int(redirect_port or os.environ.get('GOOGLE_OAUTH_REDIRECT_PORT', '53510'))
        self.creds = self.get_credentials()

    def get_client_config(self):
        client_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if client_json:
            try:
                return json.loads(client_json)
            except json.JSONDecodeError:
                print('Error: GOOGLE_CREDENTIALS_JSON is not valid JSON.')
                return None

        if not os.path.exists(self.credentials_path):
            print(f'Error: {self.credentials_path} not found.')
            return None

        with open(self.credentials_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_oauth_flow(self, redirect_uri):
        client_config = self.get_client_config()
        if not client_config:
            return None

        return Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )

    def get_authorization_url(self, email=None, redirect_uri=None):
        if email:
            self.email = email

        if not self.email:
            return None, None

        redirect_uri = redirect_uri or f'http://localhost:{self.redirect_port}/api/gmail/callback'
        flow = self.create_oauth_flow(redirect_uri)
        if not flow:
            return None, None

        return flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

    def exchange_code_for_credentials(self, code, email=None, redirect_uri=None):
        if email:
            self.email = email

        if not self.email:
            return None

        redirect_uri = redirect_uri or f'http://localhost:{self.redirect_port}/api/gmail/callback'
        flow = self.create_oauth_flow(redirect_uri)
        if not flow:
            return None

        try:
            flow.fetch_token(code=code)
        except Exception as e:
            print(f'Failed to fetch OAuth token: {e}')
            return None

        creds = flow.credentials
        if not creds:
            return None

        if self.save_credentials_for_email(self.email, creds):
            self.creds = creds
            return creds

        return None

    def get_credentials(self):
        if self.email:
            token_data = get_oauth_token(self.email)
            if token_data:
                try:
                    token_info = json.loads(token_data)
                    creds = Credentials.from_authorized_user_info(token_info, SCOPES)
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        save_oauth_token(self.email, creds.to_json())
                    return creds
                except Exception as e:
                    print(f'Failed to load credentials for {self.email}: {e}')

        # Fallback for legacy token file support
        token_path = os.environ.get('GOOGLE_TOKEN_PATH', 'token.json')
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                return creds
            except Exception as e:
                print(f'Failed to load legacy credentials from {token_path}: {e}')

        return None

    @staticmethod
    def save_credentials_for_email(email, creds):
        if not email or not creds:
            return False
        save_oauth_token(email, creds.to_json())
        return True

    def get_service(self):
        if not self.creds:
            return None
        return build('gmail', 'v1', credentials=self.creds)

    def get_unread_emails_with_attachments(self, min_age_minutes=1, max_age_minutes=9):
        """Fetches unread emails with attachments from a time window (e.g., 1-9 minutes old)."""
        service = self.get_service()
        if not service:
            return []

        try:
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

                service.users().messages().batchModify(
                    userId=user_id,
                    body={'ids': [message['id']], 'removeLabelIds': ['UNREAD']}
                ).execute()

            return email_data
        except HttpError as error:
            print(f'An error occurred: {error}')
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
            print(f'An error occurred while sending email: {error}')
            return None
