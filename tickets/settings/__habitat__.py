
"""
Django Environments 0.3.0-alpha2

All settings here will override another ones
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENVIRONMENT_NAME = "Develop"
ENVIRONMENT_VERSION_CODE = "dev"

