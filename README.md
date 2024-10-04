# Calendly APIs

Rest APIs for Calendly like applications.

## Key Features

1. **User Management**  
- Retrieve the list of users with user details. Useful for admin users.

2. **Availability Management**
- Set availability for a user.
- Retrieve availability for a user.
- If consecutive & overlapping availability slots are set, they are merged into a single slot.
- If a new availability slot engulfs an existing slot, the existing slot is removed and the larger slot is added.
- Prevent setting availability if the user is already available in the requested time.

3. **Overlap Management**  
- Find overlap (partial & full) in availability between two users.
- Find partial overlap in availability between two users.

4. **Meeting Scheduling**
- Schedule a meeting when both users are available.
- Ensure availability is removed after scheduling a meeting.
- If a meeting is scheduled in between an availability slot, the remaining slot is split into two slots.

5. **Timezone handling**
-  The backend saves all timestamp fields in epoch timestamp. The frontend can convert it to the user's timezone (or any timezone of the user's choice).

6. **Swagger Documentation**

## Installation

### Easy Mode
Get [docker](https://docs.docker.com/engine/install/) installed, if not already.

Then from the project root, run

```sh
docker compose up
```

This will seed the database with some initial data and start the server at port 5001.

Access the API documentation at [http://localhost:5001/api/docs](http://localhost:5001/api/docs)

### Hard Mode

1. Clone the repository
2. Setup virtual environment using [conda](https://docs.anaconda.com/miniconda/#quick-command-line-install)
    ```sh
    conda create -n calendly python=3.9 anaconda
    conda activate calendly
    ```
   
    Alternatively, you can use `virtualenv` or `pipenv` for creating a virtual environment.
    ```sh
    python -m venv venv
    source venv/bin/activate
    ```
3. Install the dependencies
    ```sh
    pip install -r requirements.txt
    ```
4. Install [postgresql](https://www.postgresql.org/download/) and create a database named `calendly`.
   Alternative: If postgres is not installed, you can use [sqllite](https://www.sqlite.org/) by changing the database url in the `.env` file.
5. Update the database url in the .env file as per your configuration.
    ```sh
    DATABASE_URL=postgresql://username:password@localhost:5432/calendly
    ```
   
    or for sqllite
    ```sh
    DATABASE_URL=sqlite:///calendly.db
    ```
   The values in the `.env` file can be overridden by exporting the same environment variables.
6. Start the server
    ```sh
    make run
    ```
   By default, it will start the server at port 5001. You can change the port in the `.env` file.
7. Seed the database with some initial data
    ```sh
    python seed.py
    ```
8. Access the API documentation at [http://localhost:5001/api/docs](http://localhost:5001/api/docs)
9. Run tests
    ```sh
    make test
    ```
   
### Tech Stack
- Python + Flask: Micro framework for fast prototyping.
- Postgresql: Primary data store ( the data model fits well with a relational database).
- Gunicorn: WSGI server.
- Docker: For containerization.
- Heroku: For deployment.
- Swagger: For API documentation.
- ER Diagram:

```
+-----------------+ N             1 +-----------------+ 1           N +-----------------+
|   Availability  |<---------------|      User       |-------------->|     Meeting     |
+-----------------+                +-----------------+               +-----------------+
| id (PK)         |                | id (PK)         |               | id (PK)         |
| user_id (FK)    |                | name            |               | user1_id (FK)   |
| start_time (IDX)|                +-----------------+               | user2_id (FK)   |
| end_time (IDX)  |                                                  | meeting_time    |
+-----------------+                                                  +-----------------+
```

### Assumptions
- The user can set availability and schedule meetings for any time in the future not in the past.
- Authentication & authorization is someone else's responsibility (ex: API Gateway).
- Users are already existing in the system, sign up might be implemented in a different service.
- Timezone handling is the responsibility of the frontend. The backend saves all timestamps in epoch timestamp.
- There is no daylight saving time handling. 
   
## Future Improvements
- Add authentication and authorization (one user should not be able to set availability of another user).
- If two users try to set availability or meetings at the same time, it may lead to concurrency issues. But kept it Out Of Scope for now.
- The meeting feature can be improved to support meeting invitation, recurring meetings, meeting location etc.
- We can implement another useful API, Timeline view API, which will return all the available slots and scheduled meetings
  for a user in a timeline view.
- The list APIs can be paginated.
- API to add users.
