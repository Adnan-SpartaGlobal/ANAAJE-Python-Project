"""Makes `import config` and `from checks.tcp import check_tcp` work from inside tests/.

pytest adds the test file's own directory to the path, not the project root, so
without this the imports fail with ModuleNotFoundError. This is the usual fix
for a flat project layout and you can leave it alone.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
