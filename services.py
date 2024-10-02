# Business logic for handling availability and overlaps

from models import Availability, Meeting, db


def find_overlap(user1_id, user2_id):
    user1_slots = Availability.query.filter_by(user_id=user1_id).all()
    user2_slots = Availability.query.filter_by(user_id=user2_id).all()

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
    available_slots = Availability.query.filter_by(user_id=user_id).all()

    for slot in available_slots:
        if slot.start_time <= start_time and slot.end_time >= end_time:
            return True  # Available
    return False


def schedule_meeting(user1_id, user2_id, meeting_start_time, meeting_end_time):
    """ Schedule a meeting between two users and update their availability. """

    # Create new meeting entry
    meeting = Meeting(user1_id=user1_id, user2_id=user2_id, meeting_time=meeting_start_time)
    db.session.add(meeting)

    # Adjust availability for user1
    _update_availability(user1_id, meeting_start_time, meeting_end_time)

    # Adjust availability for user2
    _update_availability(user2_id, meeting_start_time, meeting_end_time)

    # Commit changes to the database
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
