class BrainOpsError(Exception):
    """Base application error."""


class ConfigError(BrainOpsError):
    """Raised when configuration is missing or invalid."""


class VaultSafetyError(BrainOpsError):
    """Raised when an operation escapes the vault boundary."""


class AIProviderError(BrainOpsError):
    """Raised when a local AI provider cannot satisfy the request."""


class SchemaOutOfDateError(BrainOpsError):
    """Raised when the knowledge DB schema lacks columns added by a migration.

    Raised at the entry of write paths that depend on post-migration columns,
    to avoid silent corruption. Fix: run `brain migrate-knowledge-db`.
    """


class RealVaultAccessError(BrainOpsError):
    """Raised when code tries to open the user's real vault under test guard.

    Activated only when BRAIN_OPS_BLOCK_REAL_VAULT=1 (set by tests/conftest.py).
    A clear signal that a test is unintentionally touching production data.
    """
