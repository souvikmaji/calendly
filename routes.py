# API routes
import time

from flask import Blueprint, request
from flask_restx import Api, Resource

import services
from models import Availability, User, db

bp = Blueprint('api', __name__)
api = Api(bp, version='1.0', title='Calendly API', description='A simple API server for scheduling meetings')

@api.route('/users')
class Users(Resource):
    def get(self):
        users = User.query.all()
        return [{"id": user.id, "name": user.name} for user in users]


@api.route('/availability/<int:user_id>')
class AvailabilityApi(Resource):

    def get(self, user_id):
        availability = Availability.query.filter_by(user_id=user_id).all()
        return [{
            "start_time": slot.start_time,
            "end_time": slot.end_time
        } for slot in availability]

    def post(self, user_id):
        """Set availability for a user"""
        data = request.json
        start_time = data['start_time']
        end_time = data['end_time']

        user = User.query.get(user_id)
        if not user:
            return {"error": "user do not exist"}, 404

        current_time = int(time.time())
        if start_time >= end_time or start_time < current_time or end_time < current_time:
            return {"error": "invalid time"}, 400

        # check if there is a meeting scheduled in the requested time
        if services.check_availability(user_id, start_time, end_time):
            return {"error": "User is not available in the requested time"}, 400
        availability = Availability(user_id=user_id, start_time=start_time, end_time=end_time)
        db.session.add(availability)
        db.session.commit()

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

        # Validate users exist
        user1 = User.query.get(user1_id)
        user2 = User.query.get(user2_id)
        if not user1 or not user2:
            return {"error": "One or both users do not exist"}, 404

        # Check if the requested meeting time is available for both users
        if not services.check_availability(user1_id, meeting_start_time, meeting_end_time) or \
                not services.check_availability(user2_id, meeting_start_time, meeting_end_time):
            return {"error": "No overlap found in availability for the requested time"}, 400

        # Schedule the meeting and update availability for both users
        services.schedule_meeting(user1_id, user2_id, meeting_start_time, meeting_end_time)

        return {"message": "Meeting scheduled successfully!"}, 201
