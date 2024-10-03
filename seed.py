import random
from faker import Faker
from datetime import datetime, timedelta

from app import create_app
from models import db, User, Availability

fake = Faker()


def seed_users_and_availability(num_users=10, num_slots_per_user=5):
    app = create_app()
    with app.app_context():
        # Create users
        for _ in range(num_users):
            user = User(name=fake.user_name())
            db.session.add(user)
            db.session.commit()

            # Create random availability slots for each user
            for _ in range(num_slots_per_user):
                # Generate random start and end times within the next week
                start_time = fake.date_time_between(start_date="now", end_date="+7d")
                end_time = start_time + timedelta(hours=random.randint(1, 4))  # Random duration between 1 to 4 hours

                # Convert to epoch timestamps
                start_epoch = int(start_time.timestamp())
                end_epoch = int(end_time.timestamp())

                # Add availability slot for the user
                availability = Availability(user_id=user.id, start_time=start_epoch, end_time=end_epoch)
                db.session.add(availability)

        # Commit all changes to the database
        db.session.commit()
        print(f"Seeded {num_users} users with {num_slots_per_user} availability slots each.")


if __name__ == '__main__':
    seed_users_and_availability()