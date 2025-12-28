import os
##############  This file is run from the tasks daily to reload the website
##############  This is done to fix the schedule API from returning an empty response

# os.utime("/var/www/dev_oicwebapps_com_wsgi.py") # Development server
os.utime("/var/www/www_oicwebapp_com_wsgi.py") # Production server
