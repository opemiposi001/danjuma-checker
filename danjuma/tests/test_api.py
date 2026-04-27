import unittest
import json
import os
import sys

# Add the project root to the path so we can import the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Note: We need to mock the scheduler to prevent it from running in tests
from unittest.mock import patch

with patch('scheduler.start_scheduler'):
    from app import create_app
    from models.database import get_db_connection, init_db

class TestAPI(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for testing
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['VIRUSTOTAL_API_KEY'] = 'test_key'
        
        with patch('scheduler.start_scheduler'):
            self.app = create_app()
            self.client = self.app.test_client()
        
        # Initialize the in-memory database
        init_db()

    def test_register_email(self):
        response = self.client.post('/api/register', 
                                    data=json.dumps({'email': 'test@gmail.com'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('Successfully registered test@gmail.com', response.get_data(as_text=True))

    def test_get_status(self):
        # Register first
        self.client.post('/api/register', 
                         data=json.dumps({'email': 'test@gmail.com'}),
                         content_type='application/json')
        
        response = self.client.get('/api/status?email=test@gmail.com')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertTrue(data['is_active'])

    def test_unregister_email(self):
        # Register first
        self.client.post('/api/register', 
                         data=json.dumps({'email': 'test@gmail.com'}),
                         content_type='application/json')
        
        response = self.client.delete('/api/unregister',
                                      data=json.dumps({'email': 'test@gmail.com'}),
                                      content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Check status
        response = self.client.get('/api/status?email=test@gmail.com')
        data = json.loads(response.get_data(as_text=True))
        self.assertFalse(data['is_active'])

    def test_get_scans_empty(self):
        response = self.client.get('/api/scans?email=test@gmail.com')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 0)

if __name__ == '__main__':
    unittest.main()
