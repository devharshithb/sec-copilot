# app/config.py
import os
from dotenv import load_dotenv
from datetime import timedelta

# Load variables from .env
load_dotenv()

# Mongo settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "sec_copilot")

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

def jwt_expiration():
    return timedelta(minutes=JWT_EXPIRE_MINUTES)
