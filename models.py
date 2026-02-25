from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from database import Base


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, unique=True, index=True)
    license_type = Column(String)  # individual / institutional
    max_devices = Column(Integer)
    expiration_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Activation(Base):
    __tablename__ = "activations"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String)
    machine_id = Column(String)
    activated_at = Column(DateTime, default=datetime.utcnow)
