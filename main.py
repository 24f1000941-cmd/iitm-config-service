
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    return str(value).strip().lower() in {
        "true", "1", "yes", "on"
    }


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = dict(DEFAULTS)

    # YAML configuration
    env_name = os.getenv("APP_ENV", "development")
    yaml_path = BASE_DIR / f"config.{env_name}.yaml"

    if yaml_path.exists():
        with open(yaml_path, encoding="utf-8") as file:
            config.update(yaml.safe_load(file) or {})

    # .env configuration
    env_values = dotenv_values(BASE_DIR / ".env")

    for key, value in env_values.items():
        if value is None:
            continue
        if key == "NUM_WORKERS":
            config["workers"] = value
        elif key.startswith("APP_"):
            config[key[4:].lower()] = value

    # OS environment variables
    for key, value in os.environ.items():
        if key.startswith("APP_") and key != "APP_ENV":
            config[key[4:].lower()] = value

    # Query-string overrides
    for item in set:
        if "=" in item:
            key, value = item.split("=", 1)
            key = key.strip().lower()
            if key:
                config[key] = value

    config["port"] = int(config["port"])
    config["workers"] = int(config["workers"])
    config["debug"] = to_bool(config["debug"])

    for key in config:
        if key not in ("port", "workers", "debug"):
            config[key] = str(config[key])

    config["api_key"] = "****"
    return config
