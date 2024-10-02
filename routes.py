# API routes

from flask import Blueprint, request, jsonify
from models import User, Availability, db
import services

bp = Blueprint('api', __name__)


@bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": user.id, "name": user.name} for user in users])

@bp.route('/availability/<int:user_id>', methods=['GET'])
def get_availability(user_id):
    availability = Availability.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "start_time": slot.start_time,
        "end_time": slot.end_time
    } for slot in availability])
