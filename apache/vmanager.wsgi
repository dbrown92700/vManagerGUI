import sys
import logging

sys.path.insert(0, '/var/www/vManagerGUI')
sys.path.insert(0, '/var/www/vManagerGUI/venv/lib/python3.10/site-packages/')

from dotenv import load_dotenv
load_dotenv('/var/www/vManagerGUI/.env')

# Set up logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# Import and run the Flask app
from main import app as application