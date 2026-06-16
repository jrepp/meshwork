import jwt
import pytest
from gcid.gcid import profile_seq_to_id

from meshwork.auth import decode_token, generate_token, roles

TEST_EMAIL = "test@test.com"

profile_seq = 5
profile_id = profile_seq_to_id(profile_seq)
not_sent = 0
sent = 1
location = "localhost"
environment = "test"
auth_roles = []


def tamper_token(token: str) -> str:
    """Change the signature segment without changing token shape."""
    replacement = "a" if token[-1] != "a" else "b"
    return f"{token[:-1]}{replacement}"


def test_auth_token_with_roles():
    auth_roles = [roles.tag_create, roles.org_create]
    token = generate_token(
        profile_id, TEST_EMAIL, sent, location, environment, auth_roles
    )
    assert token is not None
    decode_profile = decode_token(token)
    assert TEST_EMAIL == decode_profile.email
    assert profile_seq == decode_profile.profile_seq
    assert location == decode_profile.location
    assert decode_profile.email_validate_state == sent
    assert roles.tag_create in decode_profile.auth_roles
    assert roles.org_create in decode_profile.auth_roles
    assert "" not in decode_profile.auth_roles


def test_auth_token_defaults_to_empty_roles():
    token = generate_token(profile_id, TEST_EMAIL, sent, location, environment)

    decode_profile = decode_token(token)

    assert decode_profile.auth_roles == set()
    assert decode_profile.auth_token == token
    assert decode_profile.environment == environment


def test_auth_token_tracks_impersonation_state():
    token = generate_token(
        profile_id,
        TEST_EMAIL,
        sent,
        location,
        environment,
        impersonated_by="admin-profile",
    )

    decode_profile = decode_token(token)

    assert decode_profile.impersonated is True


def test_auth_token_rejects_modified_signature():
    token = generate_token(
        profile_id, TEST_EMAIL, sent, location, environment, [roles.tag_create]
    )

    with pytest.raises(jwt.InvalidSignatureError):
        decode_token(tamper_token(token))
