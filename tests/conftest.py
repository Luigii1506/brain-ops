"""Test isolation — keeps the test suite away from production data.

Setting the environment variables HERE guarantees they are in effect for the
entire test process (pytest or unittest), including imports that happen before
any test function runs.

Campaña 0.5 safety contract:

    BRAIN_OPS_NO_MIGRATE=1
        `apply_migrations()` returns [] without touching any DB. The only way
        to run a real migration in a test is to pass `_force=True` explicitly.

    BRAIN_OPS_BLOCK_REAL_VAULT=1
        `load_validated_vault()` raises RealVaultAccessError if a test tries
        to load the user's real vault (the path listed in the default
        `config/vault.yaml`).

Both guards are reinforced by a `sys.modules` check in the code itself: even
if this file somehow doesn't run (rare: running a test file from outside
the tests/ tree), the guards still trigger because pytest/_pytest or
unittest.loader/unittest.runner appear in sys.modules.

If a test genuinely needs to exercise either guarded path, it must
explicitly monkeypatch the env var and pass `_force=True` to the function.
"""

from __future__ import annotations

import os


os.environ.setdefault("BRAIN_OPS_NO_MIGRATE", "1")
os.environ.setdefault("BRAIN_OPS_BLOCK_REAL_VAULT", "1")
