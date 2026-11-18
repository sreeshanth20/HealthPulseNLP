"""Backend application package.

Bootstraps sys.path so the sibling `ml` package is importable regardless of
how the app is launched (uvicorn, pytest, seed scripts, Docker).
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
for _p in (str(_PROJECT_ROOT), str(_BACKEND_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
