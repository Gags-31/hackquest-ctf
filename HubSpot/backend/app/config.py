import os


class Settings:
    PROJECT_NAME = "HubSpot"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hubspot.db")
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    VECTOR_DB = os.getenv("VECTOR_DB", "in-memory")
    KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")


settings = Settings()
