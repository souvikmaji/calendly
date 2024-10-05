# Business logic for handling availability and overlaps
import time
from typing import List

from sqlalchemy import text

from src.api_exceptions import AvailabilityError, InvalidTimestampError, UserNotFoundError
from src.models import Availability, Meeting, User, db


def get_all_users() -> List[User]:
    return User.query.all()


def get_availability(user_id: int, start_time: int, end_time: int) -> List[Availability]:
    availability =  Availability.query.filter(Availability.user_id == user_id)
    if start_time:
        availability = availability.filter(Availability.start_time >= start_time)
    if end_time:
        availability = availability.filter(Availability.end_time <= end_time)
    return availability.order_by(Availability.start_time).all()

def find_overlap(user1_id: int, user2_id: int) -> List[dict]:
    """
    return a list of overlapping time slots between two users, in the format: [{"start_time": int, "end_time": int}]
    """

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


def check_availability(user_id: int, start_time: int, end_time: int) -> bool:
    """ Check if a user has availability during the requested meeting time directly in the database. """
    result = db.session.query(Availability).filter(Availability.user_id == user_id,
                                                   Availability.start_time <= start_time,
                                                   Availability.end_time >= end_time).first()

    return result is not None


def set_user_availability(user_id: int, start_time: int, end_time: int):
    user = User.query.get(user_id)
    if not user:
        raise UserNotFoundError("User does not exist")

    if not is_valid_timestamps(start_time, end_time):
        raise InvalidTimestampError("Invalid timestamps")

    # user is already available for a bigger time slot
    if check_availability(user_id, start_time, end_time):
        raise AvailabilityError("User is already available in the requested time")

    # Check if after inserting it will result in consecutive slots, if yes, merge them
    merged = merge_slots(user_id, end_time, start_time)

    if not merged:
        availability = Availability(user_id=user_id, start_time=start_time, end_time=end_time)
        db.session.add(availability)

    db.session.commit()


def merge_slots(user_id: int, end_time: int, start_time: int) -> bool:
    consecutive_slots = Availability.query.filter(
        Availability.user_id == user_id,
        ((Availability.end_time >= start_time) & (Availability.start_time <= start_time))
        | ((Availability.start_time <= end_time) & (Availability.end_time >= end_time))
    ).all()

    if consecutive_slots:
        for slot in consecutive_slots:
            if slot.end_time >= start_time >= slot.start_time:
                slot.end_time = end_time
            elif slot.start_time <= end_time <= slot.end_time:
                slot.start_time = start_time
        return True

    engulfing_slot = Availability.query.filter(
        Availability.user_id == user_id,
        Availability.start_time >= start_time,
        Availability.end_time <= end_time
    ).first()

    if engulfing_slot:
        engulfing_slot.start_time = start_time
        engulfing_slot.end_time = end_time
        return True

    return False


def schedule_meeting(user1_id: int, user2_id: int, meeting_start_time: int, meeting_end_time: int):
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


def create_meeting(user1_id: int, user2_id: int, meeting_start_time: int, meeting_end_time: int):
    # Create new meeting entry
    meeting = Meeting(user1_id=user1_id, user2_id=user2_id, meeting_time=meeting_start_time)
    db.session.add(meeting)

    # Adjust availability for user1
    _update_availability(user1_id, meeting_start_time, meeting_end_time)

    # Adjust availability for user2
    _update_availability(user2_id, meeting_start_time, meeting_end_time)

    db.session.commit()


def _update_availability(user_id: int, meeting_start_time: int, meeting_end_time: int):
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


def is_valid_timestamps(start_time: int, end_time: int) -> bool:
    current_time = int(time.time())
    if start_time >= end_time or start_time < current_time or end_time < current_time:
        return False
    return True
