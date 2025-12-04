# db.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from config import DB_PATH

Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    ativo = Column(String)
    minuto_entrada = Column(DateTime)
    tipo = Column(String)
    confluencias = Column(Integer)
    probabilidade = Column(Float)
    detalhes = Column(JSON)
    expiracao_sugerida_min = Column(Integer)

class Candle(Base):
    __tablename__ = "candles"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime)
    ativo = Column(String)
    o = Column(Float)
    h = Column(Float)
    l = Column(Float)
    c = Column(Float)
    v = Column(Float)

def init_db():
    Base.metadata.create_all(bind=engine)
