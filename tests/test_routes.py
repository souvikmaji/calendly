import json
import unittest
from datetime import datetime

from app import create_app
from models import User, db


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True

        with self.app.app_context():
            db.create_all()

            # Add sample data
            user1 = User(name="User1")
            user2 = User(name="User2")
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_users(self):
        response = self.client.get('/api/users')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], 'User1')
        self.assertEqual(data[1]['name'], 'User2')

    def test_set_availability(self):
        start_time = datetime.fromisoformat('2025-01-01T00:00:00').timestamp()
        end_time = datetime.fromisoformat('2025-01-01T01:00:00').timestamp()
        response = self.client.post('/api/availability', json={
            'user_id': 1,
            'start_time': start_time,
            'end_time': end_time
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Availability set successfully')

        response = self.client.get('/availability/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['start_time'], start_time)
        self.assertEqual(data[0]['end_time'], end_time)


    def test_set_availability_invalid_time(self):
        # cannot modify a past availability
        response = self.client.post('/api/availability', json={
            'user_id': 1,
            'start_time': datetime.fromisoformat('2020-01-01T00:00:00').timestamp(),
            'end_time': datetime.fromisoformat('2020-01-01T01:00:00').timestamp()
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'invalid time')

        # start time cannot be greater than end time
        response = self.client.post('/api/availability', json={
            'user_id': 1,
            'start_time': datetime.fromisoformat('2025-01-01T01:00:00').timestamp(),
            'end_time': datetime.fromisoformat('2025-01-01T00:00:00').timestamp()
        })

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'invalid time')

    def test_check_overlap(self):
        self.client.post('/api/availability', json={
            'user_id': 1,
            'start_time': 1609459200,
            'end_time': 1609462800
        })
        self.client.post('/availability', json={
            'user_id': 2,
            'start_time': 1609459200,
            'end_time': 1609462800
        })
        response = self.client.get('/overlap?user1_id=1&user2_id=2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['start_time'], 1609459200)
        self.assertEqual(data[0]['end_time'], 1609462800)

    def test_schedule_meeting(self):
        self.client.post('/api/availability', json={
            'user_id': 1,
            'start_time': 1609459200,
            'end_time': 1609462800
        })
        self.client.post('/availability', json={
            'user_id': 2,
            'start_time': 1609459200,
            'end_time': 1609462800
        })
        response = self.client.post('/meeting', json={
            'user1_id': 1,
            'user2_id': 2,
            'meeting_start_time': 1609459200,
            'meeting_end_time': 1609462800
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Meeting scheduled successfully!')


if __name__ == '__main__':
    unittest.main()
