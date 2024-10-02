# Business logic for handling availability and overlaps

from models import Availability


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
