import random

from dotenv import load_dotenv
from faker import Faker
from datetime import datetime, timedelta

from app import create_app
from src.models import db, User, Availability
from sqlalchemy_utils import create_database, database_exists, get_tables

fake = Faker()


def seed_users_and_availability(num_users=10, num_slots_per_user=5):
    app = create_app()
    load_dotenv()  # take environment variables from .env
    with app.app_context():

        database_uri = app.config['SQLALCHEMY_DATABASE_URI']
        database_name = database_uri.split("/")[-1]

        if not database_exists(database_uri):
            create_database(database_uri)
            print(f"Created database: {database_name}")
        else:
            print(f"Database {database_name} already exists")

        # create all tables
        db.create_all()

        # Create users
        for _ in range(num_users):
            user = User(name=fake.user_name())
            db.session.add(user)
            db.session.commit()

            # Create random availability slots for each user
            for i in range(num_slots_per_user):
                # Generate random start and end times within the next week
                start_time = fake.date_time_between(start_date="now", end_date="+7d")
                end_time = start_time + timedelta(hours=i + 1)

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