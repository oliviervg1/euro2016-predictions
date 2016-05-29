import multiprocessing

user = "nobody"
group = "nobody"
bind = "unix:/tmp/gunicorn.sock"
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 10
daemon = True
accesslog = "/var/log/euro2016-access.log"
errorlog = "/var/log/euro2016-error.log"
