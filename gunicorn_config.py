import multiprocessing
import os

# Gunicorn configuration settings

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Gunicorn timeout setting
timeout = 30

# Bind to the port assigned by Heroku (via environment variable $PORT)
bind = "0.0.0.0:{}".format(os.getenv("PORT", 5000))

# Log level
loglevel = 'info'

# Enable access and error logs
accesslog = '-'
errorlog = '-'