import sys
import os

# Replace 'yourusername' with your actual PythonAnywhere username
path = '/home/yourusername/DIFFPHYS'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'diffphys.settings'
os.environ['SECRET_KEY'] = 'replace-with-a-strong-secret-key'
os.environ['DEBUG'] = 'False'
os.environ['ALLOWED_HOSTS'] = 'yourusername.pythonanywhere.com'
os.environ['HF_TOKEN'] = 'your-huggingface-token-here'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
