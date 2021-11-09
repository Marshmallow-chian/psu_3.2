from dotenv import load_dotenv
from pathlib import Path
import os


def s_key():
    load_dotenv()
    env_path = Path('.')/'.env'
    load_dotenv(dotenv_path=env_path)

    secret_key = os.getenv("SECRET_KEY")

    return secret_key