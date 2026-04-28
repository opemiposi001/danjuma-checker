import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gmail_service import GmailService

class TestGmailService(unittest.TestCase):
    @patch.object(GmailService, 'get_credentials', return_value=None)
    @patch('services.gmail_service.get_oauth_token')
    def test_get_authorization_url(self, mock_get_oauth_token, mock_get_credentials):
        mock_get_oauth_token.return_value = None
        flow_mock = MagicMock()
        flow_mock.authorization_url.return_value = ('https://auth.example.com', 'state-123')

        with patch.object(GmailService, 'create_oauth_flow', return_value=flow_mock):
            gmail_service = GmailService(email='user@example.com')
            auth_url, state = gmail_service.get_authorization_url(email='user@example.com', redirect_uri='http://localhost:53510/api/gmail/callback')

        self.assertEqual(auth_url, 'https://auth.example.com')
        self.assertEqual(state, 'state-123')
        flow_mock.authorization_url.assert_called_once_with(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

    @patch.object(GmailService, 'get_credentials', return_value=None)
    @patch('services.gmail_service.get_oauth_token')
    def test_exchange_code_for_credentials(self, mock_get_oauth_token, mock_get_credentials):
        mock_get_oauth_token.return_value = None
        flow_mock = MagicMock()
        creds_mock = MagicMock()
        flow_mock.credentials = creds_mock

        with patch.object(GmailService, 'create_oauth_flow', return_value=flow_mock):
            with patch.object(GmailService, 'save_credentials_for_email', return_value=True) as mock_save:
                gmail_service = GmailService(email='user@example.com')
                returned_creds = gmail_service.exchange_code_for_credentials('auth-code', email='user@example.com', redirect_uri='http://localhost:53510/api/gmail/callback')

        self.assertIs(returned_creds, creds_mock)
        flow_mock.fetch_token.assert_called_once_with(code='auth-code')
        mock_save.assert_called_once_with('user@example.com', creds_mock)

if __name__ == '__main__':
    unittest.main()
