from dotenv import load_dotenv

load_dotenv()

class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "ucpc-secret-key"
    )

    DATABASE_URL = os.getenv("DATABASE_URL")

    DEBUG = False

    JSON_AS_ASCII = False


config = {
    "production": Config,
    "default": Config
}