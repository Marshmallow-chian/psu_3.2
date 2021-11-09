from security.s_main import get_password_hash
from dotenv import load_dotenv
from pathlib import Path
import os
import os

load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

admin_login = os.getenv("ADMIN_LOGIN")
admin_hashed_password = get_password_hash(os.getenv("ADMIN_PASSWORD"))
administrator = {'name': admin_login, 'hashed_password': admin_hashed_password, 'admin_rights': True}

