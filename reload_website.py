import os
# Daily task: touching the WSGI file makes PythonAnywhere reload the site, which works
# around the schedule API starting to return an empty response after a long uptime.
# Point this at /var/www/dev_oicwebapps_com_wsgi.py to reload the dev server instead.

os.utime("/var/www/www_oicwebapp_com_wsgi.py") # Production server
