import sys
from pathlib import Path
# Add parent to path so src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from mangum import Mangum

handler = Mangum(app, lifespan="off")
