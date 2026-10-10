import sys
from pathlib import Path

# Add project root to path
project_path = Path(__file__).parent
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

# ASGI to WSGI adapter for PythonAnywhere
from a2wsgi import ASGIMiddleware
from src.main import app

application = ASGIMiddleware(app)
