"""Test package init — activates Campaña 0.5 safety guards at import time.

Setting environment variables here (rather than only in conftest.py)
guarantees they are active for BOTH pytest and unittest. pytest calls
conftest.py as well (redundant but harmless); unittest doesn't, so this
file is what catches it.

The guards themselves are enforced by:
- `src/brain_ops/storage/sqlite/migrations/__init__.py` — checks
  BRAIN_OPS_NO_MIGRATE and sys.modules for test runners.
- `src/brain_ops/interfaces/cli/runtime.py` — checks
  BRAIN_OPS_BLOCK_REAL_VAULT and sys.modules for test runners.

Setting the env var here is the PRIMARY layer; sys.modules detection is
the secondary (belt-and-suspenders) layer. Both are present because
test discovery can sometimes import modules before this file runs.

See docs/operations/MIGRATIONS.md.
"""

from __future__ import annotations

import os


os.environ.setdefault("BRAIN_OPS_NO_MIGRATE", "1")
os.environ.setdefault("BRAIN_OPS_BLOCK_REAL_VAULT", "1")
