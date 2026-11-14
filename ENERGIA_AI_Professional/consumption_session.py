"""Stockage temporaire des analyses energetiques par session."""

from collections import OrderedDict
from copy import deepcopy
from threading import RLock
from time import monotonic

MAX_SESSIONS = 100
SESSION_TTL_SECONDS = 3600

_sessions = OrderedDict()
_lock = RLock()


def _cleanup(now):
    expired = [
        key for key, entry in _sessions.items()
        if now - entry["updated_at"] > SESSION_TTL_SECONDS
    ]

    for key in expired:
        del _sessions[key]

    while len(_sessions) > MAX_SESSIONS:
        _sessions.popitem(last=False)


def save_consumption_session(session_id, report):
    """Enregistrer un rapport pour une session existante."""

    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("Identifiant de session invalide.")

    if len(session_id) > 256:
        raise ValueError("Identifiant de session trop long.")

    if not isinstance(report, dict):
        raise ValueError("Rapport invalide.")

    now = monotonic()

    with _lock:
        _cleanup(now)

        _sessions[session_id] = {
            "report": deepcopy(report),
            "updated_at": now
        }

        _sessions.move_to_end(session_id)
        _cleanup(now)


def get_consumption_session(session_id):
    """Recuperer un rapport sans exposer l'objet stocke."""

    if not isinstance(session_id, str) or not session_id.strip():
        return None

    now = monotonic()

    with _lock:
        _cleanup(now)

        entry = _sessions.get(session_id)

        if entry is None:
            return None

        _sessions.move_to_end(session_id)

        return deepcopy(entry["report"])


def clear_consumption_session(session_id):
    """Effacer les donnees temporaires d'une session."""

    with _lock:
        return _sessions.pop(session_id, None) is not None


def get_authenticated_consumption_key(request):
    """Construire une cle isolee pour la session authentifiee.

    Ne conserve ni le cookie brut ni les identifiants en clair.
    """
    import hashlib
    import hmac
    import os

    from enterprise.auth import COOKIE, get_user

    user = get_user(request)
    cookie = request.cookies.get(COOKIE)

    if not cookie:
        raise ValueError("Cookie de session absent.")

    secret = os.environ.get("ENERGIA_SESSION_SECRET", "")

    if len(secret) < 32:
        raise RuntimeError(
            "Secret de session ENERGIA invalide."
        )

    identity = (
        str(user["organization_id"]) + ":" +
        str(user["id"]) + ":" +
        cookie
    )

    digest = hmac.new(
        secret.encode("utf-8"),
        identity.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return "energia-consumption:" + digest
