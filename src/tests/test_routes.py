import json
import unittest
from datetime import datetime

from app import create_app
from src.models import User, db


class BaseAPITestCase(unittest.TestCase):
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

        self.start_time = datetime.fromisoformat('2025-01-01T00:00:00').timestamp()
        self.end_time = datetime.fromisoformat('2025-01-01T01:00:00').timestamp()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


class TestGetUsers(BaseAPITestCase):

    def test_users_exist(self):
        response = self.client.get('/api/users')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        self.assertEqual('User1', data[0]['name'])
        self.assertEqual('User2', data[1]['name'])

    def test_no_users(self):
        with self.app.app_context():
            db.session.query(User).delete()
            db.session.commit()

        response = self.client.get('/api/users')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)

class TestAvailability(BaseAPITestCase):

    def test_non_overlapping(self):
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)
        self.assertEqual('Availability set successfully', response.json['message'])

        # once set, availability should be returned
        response = self.client.get('/api/availability/1')
        self.assertEqual(200, response.status_code)
        data = response.json
        self.assertEqual(1, len(data))
        self.assertEqual(self.start_time, data[0]['start_time'])
        self.assertEqual(self.end_time, data[0]['end_time'])

        # set 2 more non consecutive availabilities
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time + 7200, 'end_time': self.end_time + 7200})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time - 7200, 'end_time': self.end_time - 7200})
        self.assertEqual(201, response.status_code)

        response = self.client.get('/api/availability/1')
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.json))

    def test_consecutive_slots(self):
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        # set new availability that is consecutive to the previous one
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.end_time-600, 'end_time': self.end_time + 3600})
        self.assertEqual(201, response.status_code)

        response = self.client.get('/api/availability/1')
        self.assertEqual(200, response.status_code)
        data = response.json
        self.assertEqual(1, len(data))
        self.assertEqual(self.start_time, data[0]['start_time'])
        self.assertEqual(self.end_time + 3600, data[0]['end_time'])

        # set new availability that is ends at the start of the previous one
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time - 3600, 'end_time': self.start_time})
        self.assertEqual(201, response.status_code)

        response = self.client.get('/api/availability/1')
        self.assertEqual(200, response.status_code)
        data = response.json
        self.assertEqual(1, len(data))
        self.assertEqual(self.start_time - 3600, data[0]['start_time'])
        self.assertEqual(self.end_time + 3600, data[0]['end_time'])

    def test_existing_engulfing_overlap(self):
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time - 600, 'end_time': self.end_time + 600})
        self.assertEqual(201, response.status_code)

        response = self.client.get('/api/availability/1')
        self.assertEqual(200, response.status_code)
        data = response.json
        self.assertEqual(1, len(data))
        self.assertEqual(self.start_time - 600, data[0]['start_time'])
        self.assertEqual(self.end_time + 600, data[0]['end_time'])


    def test_invalid_time(self):
        # cannot modify a past availability
        response = self.client.post('/api/availability/1',
                                    json={'start_time': datetime.fromisoformat('2020-01-01T00:00:00').timestamp(),
                                          'end_time': datetime.fromisoformat('2020-01-01T01:00:00').timestamp()})
        self.assertEqual(400, response.status_code)
        self.assertEqual('Invalid timestamps', response.json['error'])

        # start time cannot be greater than end time
        response = self.client.post('/api/availability/1',
                                    json={'start_time': datetime.fromisoformat('2025-01-01T01:00:00').timestamp(),
                                          'end_time': datetime.fromisoformat('2025-01-01T00:00:00').timestamp()})

        self.assertEqual(400, response.status_code)
        self.assertEqual('Invalid timestamps', response.json['error'])

    def test_already_available(self):
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(400, response.status_code)
        self.assertEqual('User is already available in the requested time', response.json['error'])

        response = self.client.post('/api/availability/1', json={'start_time': self.start_time + 600, 'end_time': self.end_time - 600})
        self.assertEqual(400, response.status_code)
        self.assertEqual('User is already available in the requested time', response.json['error'])


class TestOverlap(BaseAPITestCase):

    def test_perfect_overlap(self):
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/availability/2',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        response = self.client.get('/api/overlap?user1_id=1&user2_id=2')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(1, len(data))
        self.assertEqual(data[0]['start_time'], self.start_time)
        self.assertEqual(data[0]['end_time'], self.end_time)

    def test_partial_overlap(self):
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/availability/2',
                                    json={'start_time': self.start_time + 1800, 'end_time': self.end_time + 2400, })
        self.assertEqual(201, response.status_code)

        response = self.client.get('/api/overlap?user1_id=1&user2_id=2')
        self.assertEqual(200, response.status_code)
        data = response.json
        self.assertEqual(1, len(data))
        self.assertEqual(self.start_time + 1800, data[0]['start_time'])
        self.assertEqual(self.end_time, data[0]['end_time'])

class TestMeeting(BaseAPITestCase):
    def test_schedule_meeting(self):
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/availability/2',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/meeting',
                                    json={'user1_id': 1, 'user2_id': 2, 'meeting_start_time': self.start_time,
                                          'meeting_end_time': self.end_time})
        self.assertEqual(201, response.status_code)
        self.assertEqual('Meeting scheduled successfully!', response.json['message'])

        # check if the availability is removed
        response = self.client.get('/api/availability/1')
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.json))

        response = self.client.get('/api/availability/2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.data)), 0)

    def test_schedule_meeting_no_overlap(self):
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/availability/2',
                                    json={'start_time': self.end_time + 3600, 'end_time': self.end_time + 7200})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/meeting',
                                    json={'user1_id': 1, 'user2_id': 2, 'meeting_start_time': self.start_time,
                                          'meeting_end_time': self.end_time})
        self.assertEqual(400, response.status_code)
        self.assertEqual('No overlap found in availability for the requested time', response.json['error'])

    def test_schedule_meeting_no_availability(self):
        # both users have no availability
        response = self.client.post('/api/meeting',
                                    json={'user1_id': 1, 'user2_id': 2, 'meeting_start_time': self.start_time,
                                          'meeting_end_time': self.end_time})
        self.assertEqual(400, response.status_code)
        self.assertEqual('No overlap found in availability for the requested time', response.json['error'])

        # add availability for user2
        response = self.client.post('/api/availability/2',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        # meeting still should not be scheduled, since user1 doesnt have availability
        response = self.client.post('/api/meeting',
                                    json={'user1_id': 1, 'user2_id': 2, 'meeting_start_time': self.start_time,
                                          'meeting_end_time': self.end_time})
        self.assertEqual(400, response.status_code)
        self.assertEqual('No overlap found in availability for the requested time', response.json['error'])

    def test_schedule_meeting_within_availability(self):
        response = self.client.post('/api/availability/1',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/availability/2',
                                    json={'start_time': self.start_time, 'end_time': self.end_time})
        self.assertEqual(201, response.status_code)

        response = self.client.post('/api/meeting',
                                    json={'user1_id': 1, 'user2_id': 2, 'meeting_start_time': self.start_time + 600,
                                          'meeting_end_time': self.end_time - 600})
        self.assertEqual(201, response.status_code)
        self.assertEqual('Meeting scheduled successfully!', response.json['message'])

        # check if the availability is divided
        response = self.client.get('/api/availability/1')
        self.assertEqual(200, response.status_code)
        data = response.json
        self.assertEqual(2, len(data))
        self.assertEqual(self.start_time, data[0]['start_time'])
        self.assertEqual(self.start_time + 600, data[0]['end_time'])
        self.assertEqual(self.end_time - 600, data[1]['start_time'])
        self.assertEqual(self.end_time, data[1]['end_time'])

    def test_schedule_meeting_invalid_time(self):
        response = self.client.post('/api/meeting', json={'user1_id': 1, 'user2_id': 2,
            'meeting_start_time': datetime.fromisoformat('2020-01-01T00:00:00').timestamp(),
            'meeting_end_time': datetime.fromisoformat('2020-01-01T01:00:00').timestamp()})
        self.assertEqual(400, response.status_code)
        self.assertEqual('Invalid timestamps', response.json['error'])

        response = self.client.post('/api/meeting',
                                    json={'user1_id': 1, 'user2_id': 2, 'meeting_start_time': datetime.fromisoformat('2025-01-01T01:00:00').timestamp(),
                                          'meeting_end_time': datetime.fromisoformat('2025-01-01T00:00:00').timestamp()})
        self.assertEqual(400, response.status_code)
        self.assertEqual('Invalid timestamps', response.json['error'])


if __name__ == '__main__':
    unittest.main()
