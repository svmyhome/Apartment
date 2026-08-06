from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings


Engine = create_engine(settings.database_url)
SessionLocal = sessionmaker()
SessionLocal.configure(bind=Engine)