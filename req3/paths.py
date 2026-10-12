"""Well-known asset paths (repo layout, design §13).

The package lives at <root>/req3, assets at <root>/schemas and
<root>/profiles — identical in the dev repo and the Docker image.
"""
from __future__ import annotations

from pathlib import Path

import req3

REPO_ROOT = Path(req3.__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
PROFILES_DIR = REPO_ROOT / "profiles"
