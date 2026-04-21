import sys
import os

path = '/home/DiyorbekIslomov/DIFFPHYS'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'diffphys.settings'
os.environ['SECRET_KEY'] = 'replace-with-a-strong-secret-key'
os.environ['DEBUG'] = 'False'
os.environ['ALLOWED_HOSTS'] = 'DiyorbekIslomov.pythonanywhere.com'
os.environ['HF_TOKEN'] = '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'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
