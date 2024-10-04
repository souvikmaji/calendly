# Calendly APIs

Rest APIs for Calendly like applications.

## Key Features

- **Set Own Availability**: Users can define their available time slots.
- **Show Own Availability**: Retrieve the user's available time slots.
- **Find Overlap in Schedule Between 2 Users**: Compare the schedules of two users to find matching available slots.
- **Schedule Meetings**: Create meetings if an overlap is found in the availability of two users.
- **Get All Users**: Retrieve all users. (Possible use case: admin dashboard)


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
    python3 -m venv venv
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
   By default, it will start the server at port 5000. You can change the port in the `.env` file.
7. Seed the database with some initial data
    ```sh
    python seed.py
    ```
8. Access the API documentation at [http://localhost:5000/api/docs](http://localhost:5000/api/docs)
9. Run tests
    ```sh
    make test
    ```
   


