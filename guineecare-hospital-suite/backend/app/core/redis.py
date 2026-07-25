"""Redis client partagé — v2.9.2

Centralise la connexion Redis pour :
- Rate limiting distribué (slowapi RedisStorage)
- Cache partagé multi-instance
- File d'attente Celery (broker)

En mode dev/test (REDIS_URL non configurée), fallback en mémoire.
Aucune erreur n'est levée si Redis est absent : l'app reste fonctionnelle,
mais le rate limit n'est pas partagé entre les workers.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger("guineecare.redis")

# URL Redis lue depuis l'environnement. Exemples :
#   redis://localhost:6379/0
#   redis://:password@redis-host:6379/0
#   rediss://secure-redis.upstash.io:6379  (TLS)
REDIS_URL: str = os.environ.get("REDIS_URL", "").strip()


def get_redis_client():
    """Retourne un client Redis partagé, ou None si Redis n'est pas configuré.

    Lazy-import pour ne pas exiger `redis` en dev/test si REDIS_URL est vide.
    En production, l'absence de Redis log un warning mais ne plante pas.
    """
    if not REDIS_URL:
        return None
    try:
        # Import paresseux — évite une dépendance dure en dev
        import redis  # type: ignore

        client = redis.from_url(
            REDIS_URL,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
            retry_on_timeout=True,
            health_check_interval=30,
            decode_responses=False,  # slowapi attend des bytes
        )
        # Ping pour valider la connexion
        client.ping()
        return client
    except ImportError:
        logger.warning(
            "REDIS_URL configurée mais package 'redis' non installé. "
            "Fallback en mémoire. Installez avec: pip install redis>=5.0"
        )
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Connexion Redis échouée (%s). Fallback en mémoire. "
            "Rate limit NON partagé entre workers.",
            exc,
        )
        return None


def get_rate_limit_storage():
    """Storage slowapi — Redis si disponible, sinon mémoire (par défaut).

    Usage :
        from app.core.redis import get_rate_limit_storage
        from app.core.limiter import limiter
        storage = get_rate_limit_storage()
        if storage is not None:
            limiter._limiter.storage = storage
    """
    client = get_redis_client()
    if client is None:
        return None
    try:
        from slowapi.util import get_remote_address  # noqa: F401
        from slowapi.middleware import RateLimitMiddleware  # noqa: F401

        # slowapi wrap redis via un Storage abstrait
        # On utilise directement le backend Redis de limits (dépendance de slowapi)
        from limits.storage import RedisStorage  # type: ignore

        return RedisStorage(REDIS_URL)
    except ImportError:
        logger.warning(
            "limits[redis] non installé. Fallback mémoire. "
            "Installez avec: pip install 'slowapi[redis]' ou 'limits[redis]'"
        )
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Rate limit Redis storage init échoué: %s", exc)
        return None


def is_redis_available() -> bool:
    """True si Redis est configuré ET joignable."""
    return get_redis_client() is not None


# Eager init au démarrage : log une fois le statut Redis
if REDIS_URL:
    _client = get_redis_client()
    if _client is not None:
        logger.info("Redis connecté à %s — rate limit partagé multi-instance", REDIS_URL.split("@")[-1] if "@" in REDIS_URL else REDIS_URL)
    else:
        logger.warning("REDIS_URL configurée mais connexion échouée — fallback mémoire")
else:
    logger.debug("REDIS_URL non configurée — rate limit en mémoire (par worker)")
