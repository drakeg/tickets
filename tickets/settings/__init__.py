
"""
Django Environments 0.3.0-alpha2
"""
from .common import *

try:
    from .__habitat__ import *
    print("Using %s environment" % ENVIRONMENT_NAME)
    if len(ENVIRONMENT_VERSION_CODE) > 0:
        VERSION += "." + ENVIRONMENT_VERSION_CODE
except ImportError:
    print("Environment starting fail!")
    print("Set the DEVELOP environment running: \"python manage.py switch-habitat develop\"")
