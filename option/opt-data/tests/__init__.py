# Ensure imports resolve to the local test package even if a site-packages
# `tests` module is present. Also allow legacy `import helpers` style used in
# existing tests.
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
