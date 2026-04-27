import unittest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.virustotal_service import VirusTotalService

class TestVirusTotalService(unittest.TestCase):
    def setUp(self):
        self.vt_service = VirusTotalService(api_key='test_key')

    @patch('requests.post')
    def test_upload_file_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'id': 'analysis_123'}}
        mock_post.return_value = mock_response

        analysis_id = self.vt_service.upload_file(b'fake data', 'test.txt')
        self.assertEqual(analysis_id, 'analysis_123')

    @patch('requests.get')
    def test_get_analysis_result_completed(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'attributes': {
                    'status': 'completed',
                    'stats': {'malicious': 0, 'suspicious': 0, 'harmless': 70}
                },
                'meta': {
                    'file_info': {'sha256': 'abc123hash'}
                }
            }
        }
        mock_get.return_value = mock_response

        result = self.vt_service.get_analysis_result('analysis_123')
        self.assertEqual(result['verdict'], 'CLEAN')
        self.assertEqual(result['malicious_count'], 0)
        self.assertEqual(result['virustotal_link'], 'https://www.virustotal.com/gui/file/abc123hash')

if __name__ == '__main__':
    unittest.main()
