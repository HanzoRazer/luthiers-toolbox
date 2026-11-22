"""Findings and the verifier exit contract.

Severities: ``io``, ``authority``, ``integrity`` and ``malformed`` each set
an exit code. ``warning`` records an accepted uncertainty (for example an
unknown scale length with a stated reason); it is reported but does not
change the exit code.
"""

from __future__ import annotations

from dataclasses import dataclass

EXIT_OK = 0
EXIT_MALFORMED = 1
EXIT_INTEGRITY = 2
EXIT_INCOMPLETE_RUN = 3
EXIT_AUTHORITY = 4


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "code": self.code, "message": self.message}


def finding(severity: str, code: str, message: str) -> Finding:
    return Finding(severity, code, message)


def exit_code(findings: list[Finding]) -> int:
    severities = {item.severity for item in findings}
    if "io" in severities:
        return EXIT_INCOMPLETE_RUN
    if "authority" in severities:
        return EXIT_AUTHORITY
    if "integrity" in severities:
        return EXIT_INTEGRITY
    if "malformed" in severities:
        return EXIT_MALFORMED
    return EXIT_OK
