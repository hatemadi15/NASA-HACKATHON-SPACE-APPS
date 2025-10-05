"""Minimal local implementation of :mod:`email_validator` used for testing.

This stub provides enough functionality for Pydantic's ``EmailStr`` type
without requiring the external dependency, which can be difficult to install
in restricted environments.  It performs lightweight validation suitable for
local development and CI but is **not** a full RFC compliant implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

__all__ = [
    "EmailNotValidError",
    "ValidatedEmail",
    "validate_email",
]


class EmailNotValidError(ValueError):
    """Exception raised when an email address fails validation."""


@dataclass(slots=True)
class ValidatedEmail:
    """Simple container mimicking the public attributes returned upstream."""

    local_part: str
    domain: str
    normalized: str


# Basic, pragmatic email pattern: local@domain.tld
# This intentionally rejects uncommon but syntactically valid forms because the
# upstream application only needs a sanity check.
_EMAIL_PATTERN = re.compile(
    r"^(?P<local>[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+)@(?P<domain>[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)$"
)


def validate_email(email: str, *, check_deliverability: bool | None = None) -> ValidatedEmail:
    """Validate ``email`` and return :class:`ValidatedEmail` data.

    Parameters
    ----------
    email:
        The email address to check.  Leading and trailing whitespace is ignored.
    check_deliverability:
        Accepted for API compatibility but ignored by this lightweight
        implementation.

    Raises
    ------
    EmailNotValidError
        If ``email`` does not resemble a typical ``local@domain`` address.
    """

    candidate = (email or "").strip()
    if not candidate:
        raise EmailNotValidError("The email address is empty")

    match = _EMAIL_PATTERN.fullmatch(candidate)
    if not match:
        raise EmailNotValidError("The email address is not valid")

    local_part = match.group("local")
    domain = match.group("domain")
    normalized = f"{local_part}@{domain}".lower()

    return ValidatedEmail(local_part=local_part, domain=domain, normalized=normalized)
