"""Mythica auth compatibility exports."""

from meshwork.auth.authorization import RoleError, Scope, validate_roles
from meshwork.auth.generate_token import decode_token, generate_token
from meshwork.auth.roles import *  # noqa: F403

__all__ = [
    "RoleError",
    "Scope",
    "decode_token",
    "generate_token",
    "validate_roles",
]
