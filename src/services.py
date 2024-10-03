# Business logic for handling availability and overlaps
import time

from src.models import Availability, Meeting, User, db
from src.api_exceptions import AvailabilityError, UserNotFoundError


def get_all_users():
    return User.query.all()


def get_availability(user_id):
    availability = Availability.query.filter_by(user_id=user_id).all()
    return availability


def find_overlap(user1_id, user2_id):
    user1_slots = get_availability(user1_id)
    user2_slots = get_availability(user2_id)

    overlaps = []

    for slot1 in user1_slots:
        for slot2 in user2_slots:
            overlap_start = max(slot1.start_time, slot2.start_time)
            overlap_end = min(slot1.end_time, slot2.end_time)

            if overlap_start < overlap_end:
                overlaps.append({"start_time": overlap_start, "end_time": overlap_end})

    return overlaps


def check_availability(user_id, start_time, end_time):
    """ Check if a user has availability during the requested meeting time. """
    available_slots = get_availability(user_id)

    for slot in available_slots:
        if slot.start_time <= start_time and slot.end_time >= end_time:
            return True  # Available
    return False


def set_user_availability(user_id, start_time, end_time):
    user = User.query.get(user_id)
    if not user:
        raise UserNotFoundError("User does not exist")

    current_time = int(time.time())
    if start_time >= end_time or start_time < current_time or end_time < current_time:
        raise AvailabilityError("Invalid time")

    # TODO: Check if the user is already available in the requested time, if there is a consecutive slot, merge them
    if check_availability(user_id, start_time, end_time):
        raise AvailabilityError("User is not available in the requested time")

    availability = Availability(user_id=user_id, start_time=start_time, end_time=end_time)
    db.session.add(availability)
    db.session.commit()


def schedule_meeting(user1_id, user2_id, meeting_start_time, meeting_end_time):
    """ Schedule a meeting between two users and update their availability. """
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
