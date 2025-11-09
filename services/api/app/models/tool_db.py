from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from pathlib import Path

# Get the app directory and construct absolute path to database
APP_DIR = Path(__file__).parent.parent
DATA_DIR = APP_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "tool_library.sqlite"
DB_URL = f"sqlite:///{DB_PATH}"

Base = declarative_base()
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class Tool(Base):
    __tablename__ = "tools"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # flat, ball, vee
    diameter_mm = Column(Float, nullable=False)
    flute_count = Column(Integer, default=2)
    helix_deg = Column(Float, default=0.0)


class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    chipload_mm = Column(Float, nullable=False)
    max_rpm = Column(Integer, default=24000)


def init_db():
    Base.metadata.create_all(engine)
