# API routes

from flask import Blueprint, request, jsonify
from models import User, Availability, db
import services

bp = Blueprint('api', __name__)


@bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": user.id, "name": user.name} for user in users])


@bp.route('/availability', methods=['POST'])
def set_availability():
    data = request.json
    user_id = data['user_id']
    start_time = data['start_time']
    end_time = data['end_time']

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user do not exist"}), 404
    # TODO: check if start_time < end_time
    # check if start_time & end_time> current time
    # check if not overlapping with existing slots
    availability = Availability(user_id=user_id, start_time=start_time, end_time=end_time)
    db.session.add(availability)
    db.session.commit()

    return jsonify({"message": "Availability set successfully"}), 201


@bp.route('/availability/<int:user_id>', methods=['GET'])
def get_availability(user_id):
    availability = Availability.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "start_time": slot.start_time,
        "end_time": slot.end_time
    } for slot in availability])


@bp.route('/overlap', methods=['GET'])
def check_overlap():
    user1_id = request.args.get('user1_id')
    user2_id = request.args.get('user2_id')

    overlap_slots = services.find_overlap(user1_id, user2_id)

    return jsonify(overlap_slots)


@bp.route('/meeting', methods=['POST'])
def schedule_meeting():
    data = request.json
    user1_id = data['user1_id']
    user2_id = data['user2_id']
    meeting_start_time = data['meeting_start_time']
    meeting_end_time = data['meeting_end_time']

    # Validate users exist
    user1 = User.query.get(user1_id)
    user2 = User.query.get(user2_id)
    if not user1 or not user2:
        return jsonify({"error": "One or both users do not exist"}), 404

    # Check if the requested meeting time is available for both users
    if not services.check_availability(user1_id, meeting_start_time, meeting_end_time) or \
            not services.check_availability(user2_id, meeting_start_time, meeting_end_time):
        return jsonify({"error": "No overlap found in availability for the requested time"}), 400

    # Schedule the meeting and update availability for both users
    services.schedule_meeting(user1_id, user2_id, meeting_start_time, meeting_end_time)

    return jsonify({"message": "Meeting scheduled successfully!"}), 201