import os

# Ensure project root is on path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Expose WSGI application for cPanel Passenger
from app import app as application

# Optional: set strict UTF-8
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


