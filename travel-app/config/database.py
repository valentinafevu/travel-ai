import json
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def database_config(base_dir, environ=None):
    """Selecciona Oracle al instalar credentials/oracle/connection.json."""
    environ = os.environ if environ is None else environ
    base_dir = Path(base_dir)
    mode = environ.get("DATABASE_BACKEND", "auto")
    if mode not in {"auto", "sqlite", "oracle"}:
        raise ImproperlyConfigured("DATABASE_BACKEND debe ser auto, sqlite u oracle.")
    directory = base_dir / "credentials" / "oracle"
    credentials = directory / "connection.json"
    if mode == "sqlite" or (mode == "auto" and not credentials.exists()):
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": base_dir / "db.sqlite3"}

    try:
        values = json.loads(credentials.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ImproperlyConfigured(
            "Oracle requiere credentials/oracle/connection.json legible y con JSON válido."
        ) from None
    required = ("user", "password", "dsn", "wallet_password")
    if not isinstance(values, dict) or any(
        not isinstance(values.get(key), str) or not values[key].strip() for key in required
    ):
        raise ImproperlyConfigured(
            "Completa user, password, dsn y wallet_password en connection.json."
        )
    wallet = directory / "wallet"
    for filename in ("tnsnames.ora", "ewallet.pem"):
        if not (wallet / filename).is_file():
            raise ImproperlyConfigured(f"Falta credentials/oracle/wallet/{filename}; descomprime el wallet de Autonomous Database.")
    return {
        "ENGINE": "django.db.backends.oracle",
        "NAME": values["dsn"],
        "USER": values["user"],
        "PASSWORD": values["password"],
        "HOST": "",
        "PORT": "",
        "OPTIONS": {
            "config_dir": str(wallet),
            "wallet_location": str(wallet),
            "wallet_password": values["wallet_password"],
            "ssl_server_dn_match": True,
        },
    }
