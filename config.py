from dotenv import load_dotenv
from security.s_main import get_password_hash
from pathlib import Path
import os

admin_login = os.getenv("ADMIN_LOGIN")
admin_hashed_password = get_password_hash(os.getenv("ADMIN_PASSWORD"))
administrator = {'name': admin_login, 'hashed_password': admin_hashed_password, 'admin_rights': True}

