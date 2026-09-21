"""
WSGI config for OIC_Web_Apps project.

It exposes the WSGI callable as a module-level variable named ``application``.

reload_website.py touches the production copy of this file to force a reload.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

application = get_wsgi_application()
