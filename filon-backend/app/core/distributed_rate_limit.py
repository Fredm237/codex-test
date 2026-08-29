"""Compteur de quota Redis atomique, pseudonymisé et strictement borné."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Protocol


class RedisEvalClient(Protocol):
    """Surface Redis minimale utilisée par le limiteur distribué."""

    async def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: object,
    ) -> object: ...


class DistributedRateLimitUnavailable(RuntimeError):
    """Le quota distribué ne peut pas produire une décision fiable."""


# L'horloge Redis évite qu'un décalage entre réplicas ouvre plusieurs quotas.
# Le registre global borne le nombre de couples pseudonyme/classe actifs. Les
# deux clés partagent un hash tag pour rester compatibles avec Redis Cluster.
_ATOMIC_SLIDING_WINDOW_SCRIPT = """
local now_parts = redis.call("TIME")
local now_us = (tonumber(now_parts[1]) * 1000000) + tonumber(now_parts[2])
local window_us = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local member = ARGV[3]
local identity = ARGV[4]
local max_identities = tonumber(ARGV[5])
local cutoff_us = now_us - window_us

redis.call("ZREMRANGEBYSCORE", KEYS[1], "-inf", cutoff_us)

redis.call("ZREMRANGEBYSCORE", KEYS[2], "-inf", cutoff_us)
local known_identity = redis.call("ZSCORE", KEYS[2], identity)
if not known_identity and redis.call("ZCARD", KEYS[2]) >= max_identities then
    return 2
end

redis.call("ZADD", KEYS[2], now_us, identity)
redis.call("PEXPIRE", KEYS[2], math.ceil(window_us / 1000))

if redis.call("ZCARD", KEYS[1]) >= limit then
    redis.call("PEXPIRE", KEYS[1], math.ceil(window_us / 1000))
    return 1
end

redis.call("ZADD", KEYS[1], now_us, member)
redis.call("PEXPIRE", KEYS[1], math.ceil(window_us / 1000))
return 0
""".strip()


class RedisSlidingWindowRateLimiter:
    """Applique une fenêtre glissante exacte partagée entre réplicas."""

    _KEY_PREFIX = "filon:rate-limit:{v1}"

    def __init__(
        self,
        client: RedisEvalClient,
        *,
        identity_secret: bytes,
        window_seconds: float,
        max_tracked_identities: int,
    ) -> None:
        if len(identity_secret) < 32:
            raise ValueError("Le secret de pseudonymisation est trop court")
        if window_seconds <= 0:
            raise ValueError("La fenêtre doit être strictement positive")
        if max_tracked_identities < 1:
            raise ValueError("Le plafond d'identités doit être positif")
        self._client = client
        self._identity_secret = identity_secret
        self._window_microseconds = int(window_seconds * 1_000_000)
        self._max_tracked_identities = max_tracked_identities

    def _identity(self, client_address: str, policy_class: str) -> str:
        payload = (
            policy_class.encode("ascii")
            + b"\0"
            + client_address.encode("utf-8", errors="replace")
        )
        digest = hmac.new(
            self._identity_secret,
            payload,
            hashlib.sha256,
        ).hexdigest()
        return f"{policy_class}:{digest}"

    async def is_rate_limited(
        self,
        client_address: str,
        *,
        policy_class: str,
        limit: int,
    ) -> bool:
        if limit < 1:
            raise ValueError("La limite doit être strictement positive")
        if policy_class not in {"expensive", "general"}:
            raise ValueError("Classe de rate limit inconnue")

        identity = self._identity(client_address, policy_class)
        window_key = f"{self._KEY_PREFIX}:window:{identity}"
        registry_key = f"{self._KEY_PREFIX}:registry"
        member = secrets.token_hex(16)
        try:
            raw_decision = await self._client.eval(
                _ATOMIC_SLIDING_WINDOW_SCRIPT,
                2,
                window_key,
                registry_key,
                self._window_microseconds,
                limit,
                member,
                identity,
                self._max_tracked_identities,
            )
            decision = int(raw_decision)
        except Exception as exc:
            raise DistributedRateLimitUnavailable(
                "Le quota distribué est indisponible"
            ) from exc

        if decision == 0:
            return False
        if decision in {1, 2}:
            return True
        raise DistributedRateLimitUnavailable(
            "Le quota distribué a renvoyé une décision invalide"
        )
