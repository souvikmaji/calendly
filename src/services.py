# Business logic for handling availability and overlaps
import time

from sqlalchemy import text

from src.models import Availability, Meeting, User, db
from src.api_exceptions import AvailabilityError, InvalidTimestampError, UserNotFoundError


def get_all_users():
    return User.query.all()


def get_availability(user_id):
    availability = Availability.query.filter_by(user_id=user_id).all()
    return availability


def find_overlap(user1_id, user2_id):
    query = """
        SELECT 
            GREATEST(a1.start_time, a2.start_time) AS overlap_start,
            LEAST(a1.end_time, a2.end_time) AS overlap_end
        FROM 
            availabilities a1
        JOIN 
            availabilities a2 
        ON 
            a1.user_id = :user1_id AND a2.user_id = :user2_id
        WHERE 
            GREATEST(a1.start_time, a2.start_time) < LEAST(a1.end_time, a2.end_time)
        """

    result = db.session.execute(text(query), {'user1_id': user1_id, 'user2_id': user2_id})
    overlaps = [{'start_time': row[0], 'end_time': row[1]} for row in result]

    return overlaps


def check_availability(user_id, start_time, end_time):
    """ Check if a user has availability during the requested meeting time directly in the database. """
    result = db.session.query(Availability).filter(
        Availability.user_id == user_id,
        Availability.start_time <= start_time,
        Availability.end_time >= end_time
    ).first()

    return result is not None



def set_user_availability(user_id, start_time, end_time):
    user = User.query.get(user_id)
    if not user:
        raise UserNotFoundError("User does not exist")

    if not is_valid_timestamps(start_time, end_time):
        raise InvalidTimestampError("Invalid timestamps")

    # TODO: Check if the user is already available in the requested time, if there is a consecutive slot, merge them
    if check_availability(user_id, start_time, end_time):
        raise AvailabilityError("User is not available in the requested time")

    availability = Availability(user_id=user_id, start_time=start_time, end_time=end_time)
    db.session.add(availability)
    db.session.commit()



def schedule_meeting(user1_id, user2_id, meeting_start_time, meeting_end_time):
    """ Schedule a meeting between two users and update their availability. """
    if not is_valid_timestamps(meeting_start_time, meeting_end_time):
        raise InvalidTimestampError("Invalid timestamps")

    user1 = User.query.get(user1_id)
    user2 = User.query.get(user2_id)
    if not user1 or not user2:
        raise UserNotFoundError("One or both users do not exist")


    if (not check_availability(user1_id, meeting_start_time, meeting_end_time) or not check_availability(user2_id,
                                                                                                         meeting_start_time,
                                                                                                         meeting_end_time)):
        raise AvailabilityError("No overlap found in availability for the requested time")
    create_meeting(user1_id, user2_id, meeting_start_time, meeting_end_time)


def create_meeting(user1_id, user2_id, meeting_start_time, meeting_end_time):
    # Create new meeting entry
    meeting = Meeting(user1_id=user1_id, user2_id=user2_id, meeting_time=meeting_start_time)
    db.session.add(meeting)

    # Adjust availability for user1
    _update_availability(user1_id, meeting_start_time, meeting_end_time)

    # Adjust availability for user2
    _update_availability(user2_id, meeting_start_time, meeting_end_time)

    db.session.commit()


def _update_availability(user_id, meeting_start_time, meeting_end_time):
    """ Adjust user's availability by removing or splitting slots based on the meeting time. """
    available_slots = Availability.query.filter_by(user_id=user_id).all()

    for slot in available_slots:
        if slot.start_time <= meeting_start_time and slot.end_time >= meeting_end_time:
            # If the slot exactly matches the meeting time, remove it
            if slot.start_time == meeting_start_time and slot.end_time == meeting_end_time:
                db.session.delete(slot)
            else:
                # If the meeting overlaps partially, split the slot
                if slot.start_time < meeting_start_time:
                    # Create a new slot for the time before the meeting
                    new_slot_before = Availability(user_id=user_id, start_time=slot.start_time,
                                                   end_time=meeting_start_time)
                    db.session.add(new_slot_before)

                if slot.end_time > meeting_end_time:
                    # Create a new slot for the time after the meeting
                    new_slot_after = Availability(user_id=user_id, start_time=meeting_end_time, end_time=slot.end_time)
                    db.session.add(new_slot_after)

                # Remove the original slot
                db.session.delete(slot)


def is_valid_timestamps(start_time, end_time):
    current_time = int(time.time())
    if start_time >= end_time or start_time < current_time or end_time < current_time:
        return False
    return True
