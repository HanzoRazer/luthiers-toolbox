"""
Runtime Manifest Exceptions.

Sprint: MRP-5T
Status: FROZEN
"""


class RuntimeManifestError(Exception):
    """Base exception for runtime manifest errors."""

    pass


class VersionMismatchError(RuntimeManifestError):
    """Raised when versions are incompatible."""

    def __init__(self, current: str, required: str, message: str = None):
        self.current = current
        self.required = required
        self.message = message or f"Version {current} incompatible with {required}"
        super().__init__(self.message)


class ContractBreakError(RuntimeManifestError):
    """Raised when a contract has breaking changes."""

    def __init__(self, contract_name: str, breaking_changes: list):
        self.contract_name = contract_name
        self.breaking_changes = breaking_changes
        message = f"Breaking changes in {contract_name}: {breaking_changes}"
        super().__init__(message)


class ManifestBuildError(RuntimeManifestError):
    """Raised when manifest building fails."""

    pass


class ContractNotFoundError(RuntimeManifestError):
    """Raised when a required contract is not found."""

    def __init__(self, contract_name: str):
        self.contract_name = contract_name
        super().__init__(f"Contract not found: {contract_name}")


class InvalidContractError(RuntimeManifestError):
    """Raised when a contract definition is invalid."""

    def __init__(self, contract_name: str, reason: str):
        self.contract_name = contract_name
        self.reason = reason
        super().__init__(f"Invalid contract {contract_name}: {reason}")
