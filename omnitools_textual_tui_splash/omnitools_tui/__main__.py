import sys
from pathlib import Path

# Add project root to path to access modules/
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from .app import launch

try:
    from modules.handlers_bridge import HANDLERS
except ImportError:
    HANDLERS = None

if __name__ == "__main__":
    launch(handlers=HANDLERS)
