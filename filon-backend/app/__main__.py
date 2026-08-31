"""Point d'entrée robuste : `python -m app`.

Lit le port depuis la variable d'environnement PORT (fournie par Railway et la
plupart des PaaS) directement en Python — aucune dépendance à l'expansion `$PORT`
par un shell, qui échouait sur Railway ("'$PORT' is not a valid integer").
"""

from __future__ import annotations

import ipaddress
import os

import uvicorn


def _trusted_proxy_allowlist() -> str:
    """Retourne une allowlist explicite ; le wildcard rendrait XFF falsifiable."""
    value = os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1")
    entries = [entry.strip() for entry in value.split(",") if entry.strip()]
    if not entries:
        return "127.0.0.1"

    normalized: list[str] = []
    networks: dict[int, list[ipaddress.IPv4Network | ipaddress.IPv6Network]] = {
        4: [],
        6: [],
    }
    for entry in entries:
        if entry == "*":
            raise RuntimeError("Le proxy wildcard est interdit")
        try:
            if "/" in entry:
                network = ipaddress.ip_network(entry, strict=True)
                if network.prefixlen == 0:
                    raise RuntimeError("Un réseau proxy universel est interdit")
                normalized.append(str(network))
                networks[network.version].append(network)
            else:
                address = ipaddress.ip_address(entry)
                normalized.append(str(address))
                networks[address.version].append(
                    ipaddress.ip_network(
                        f"{address}/{address.max_prefixlen}",
                    )
                )
        except ValueError as exc:
            raise RuntimeError("Allowlist proxy invalide") from exc

    for family_networks in networks.values():
        collapsed = list(ipaddress.collapse_addresses(family_networks))
        if any(network.prefixlen == 0 for network in collapsed):
            raise RuntimeError("Une union de réseaux proxy universelle est interdite")
    return ",".join(normalized)


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        access_log=False,
        proxy_headers=True,
        forwarded_allow_ips=_trusted_proxy_allowlist(),
    )


if __name__ == "__main__":
    main()
