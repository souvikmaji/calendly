# API routes
import time

from flask import Blueprint, request
from flask_restx import Api, Resource

import services
from exceptions import AvailabilityError, UserNotFoundError
from models import Availability, User, db

bp = Blueprint('api', __name__)
api = Api(bp, version='1.0', title='Calendly API', description='A simple API server for scheduling meetings')


@api.route('/users')
class Users(Resource):
    def get(self):
        users = services.get_all_users()
        return [{"id": user.id, "name": user.name} for user in users]


@api.route('/availability/<int:user_id>')
class AvailabilityApi(Resource):

    def get(self, user_id):
        availability = services.get_availability(user_id)
        return [{"start_time": slot.start_time, "end_time": slot.end_time} for slot in availability]

    def post(self, user_id):
        """Set availability for a user"""
        data = request.json
        start_time = data['start_time']
        end_time = data['end_time']

        try:
            services.set_user_availability(user_id, start_time, end_time)
        except UserNotFoundError:
            return {"error": "user do not exist"}, 404
        except AvailabilityError as e:
            return {"error": str(e)}, 400

        return {"message": "Availability set successfully"}, 201


@api.route('/overlap')
class Overlap(Resource):
    def get(self):
        user1_id = request.args.get('user1_id')
        user2_id = request.args.get('user2_id')

        overlap_slots = services.find_overlap(user1_id, user2_id)

        return overlap_slots


@api.route('/meeting')
class Meeting(Resource):
    def post(self):
        data = request.json
        user1_id = data['user1_id']
        user2_id = data['user2_id']
        meeting_start_time = data['meeting_start_time']
        meeting_end_time = data['meeting_end_time']

        try:
            services.schedule_meeting(user1_id, user2_id, meeting_start_time, meeting_end_time)
        except UserNotFoundError:
            return {"error": "One or both users do not exist"}, 404
        except AvailabilityError:
            return {"error": "No overlap found in availability for the requested time"}, 400

        return {"message": "Meeting scheduled successfully!"}, 201
