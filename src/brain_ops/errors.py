class BrainOpsError(Exception):
    """Base application error."""


class ConfigError(BrainOpsError):
    """Raised when configuration is missing or invalid."""


class VaultSafetyError(BrainOpsError):
    """Raised when an operation escapes the vault boundary."""
