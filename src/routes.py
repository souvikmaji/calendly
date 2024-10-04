# API routes

from flask import Blueprint
from flask_restx import Api, Resource, reqparse

from src import services
from src.api_exceptions import AvailabilityError, InvalidTimestampError, UserNotFoundError

bp = Blueprint('api', __name__)
api = Api(bp, version='1.0', title='Calendly API', description='A simple API server for scheduling meetings', doc='/docs')


@api.route('/users')
class Users(Resource):
    def get(self):
        """Get all users"""
        users = services.get_all_users()
        return [{"id": user.id, "name": user.name} for user in users]


@api.route('/availability/<int:user_id>')
class Availability(Resource):

    def get(self, user_id):
        """Get availability for a user"""
        availability = services.get_availability(user_id)
        return [{"start_time": slot.start_time, "end_time": slot.end_time} for slot in availability]

    def parse_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument('start_time', type=int, required=True)
        parser.add_argument('end_time', type=int, required=True)
        return parser.parse_args()

    @api.doc(params={'start_time': 'Start time of availability slot', 'end_time': 'End time of availability slot'})
    def post(self, user_id):
        """Set availability for a user"""

        args = self.parse_args()

        try:
            services.set_user_availability(user_id, args['start_time'], args['end_time'])
        except UserNotFoundError:
            return {"error": "user do not exist"}, 404
        except AvailabilityError as e:
            return {"error": str(e)}, 400
        except InvalidTimestampError as e:
            return {"error": str(e)}, 400

        return {"message": "Availability set successfully"}, 201


@api.route('/overlap')
class Overlap(Resource):

    def parse_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user1_id', type=int, required=True)
        parser.add_argument('user2_id', type=int, required=True)
        return parser.parse_args()

    @api.doc(params={'user1_id': 'ID of first user', 'user2_id': 'ID of second user'})
    def get(self):
        """Get overlap between two users' availability"""
        args = self.parse_args()
        overlap_slots = services.find_overlap(args['user1_id'], args['user2_id'])

        return overlap_slots


@api.route('/meeting')
class Meeting(Resource):
    def parse_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user1_id', type=int, required=True)
        parser.add_argument('user2_id', type=int, required=True)
        parser.add_argument('meeting_start_time', type=int, required=True)
        parser.add_argument('meeting_end_time', type=int, required=True)
        return parser.parse_args()

    @api.doc(params={'user1_id': 'ID of first user', 'user2_id': 'ID of second user',
                        'meeting_start_time': 'Start time of meeting', 'meeting_end_time': 'End time of meeting'})
    def post(self):
        """Schedule a meeting between two users"""
        args = self.parse_args()

        try:
            services.schedule_meeting(args['user1_id'], args['user2_id'], args['meeting_start_time'],
                                      args['meeting_end_time'])
        except UserNotFoundError as e:
            return {"error": str(e)}, 404
        except AvailabilityError as e:
            return {"error": str(e)}, 400
        except InvalidTimestampError as e:
            return {"error": str(e)}, 400


        return {"message": "Meeting scheduled successfully!"}, 201
