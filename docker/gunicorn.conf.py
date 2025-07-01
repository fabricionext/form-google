# Gunicorn configuration for Form Google - PRODUCTION
import multiprocessing

# Bind to a TCP port, not a Unix socket, for communication within the container
bind = "0.0.0.0:8000"

# Adjust the number of workers based on CPU cores
workers = multiprocessing.cpu_count() * 2 + 1

# Log to stdout and stderr to be handled by Docker/Supervisor
errorlog = "-"
accesslog = "-"
loglevel = "info"