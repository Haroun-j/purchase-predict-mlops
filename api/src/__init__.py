import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

for env_var in ["ENV", "MLFLOW_SERVER", "MLFLOW_REGISTRY_NAME"]:
    if not os.getenv(env_var):
        raise Exception("Environment variable {} must be defined.".format(env_var))
