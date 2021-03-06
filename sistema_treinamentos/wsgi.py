"""
WSGI config for sistema_treinamentos project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from dj_static import Cling, MediaCling
from static_ranges import Ranges

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_treinamentos.settings')

#application = get_wsgi_application()
#application = Cling(get_wsgi_application())
application = Ranges(Cling(MediaCling(get_wsgi_application())))
