from fastapi import FastAPI, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import os

from database import engine, SessionLocal, Base
from models import License, Activation

Base.metadata.create_all(bind=engine)

app = FastAPI()

# ==============================
# 🔐 ADMIN SECURITY
# ==============================

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")


def verify_admin_key(x_api_key: str = Header(None)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="No autorizado")


# ==============================
# 📦 DATABASE SESSION
# ==============================


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================
# 🌐 ROOT
# ==============================


@app.get("/")
def root():
    return {"message": "Licensing Server Running"}


# ==============================
# 🛠 CREAR LICENCIA (ADMIN)
# ==============================


@app.post("/create_license")
def create_license(
    license_type: str,
    max_devices: int,
    days_valid: int,
    _: str = Depends(verify_admin_key),
):
    db: Session = SessionLocal()

    license_key = secrets.token_hex(16)
    expiration = datetime.utcnow() + timedelta(days=days_valid)

    new_license = License(
        license_key=license_key,
        license_type=license_type,
        max_devices=max_devices,
        expiration_date=expiration,
        is_active=True,
    )

    db.add(new_license)
    db.commit()
    db.close()

    return {"license_key": license_key}


# ==============================
# 🔓 ACTIVAR LICENCIA
# ==============================


@app.post("/activate")
def activate_license(license_key: str, machine_id: str):
    db: Session = SessionLocal()

    license = db.query(License).filter(License.license_key == license_key).first()

    if not license:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")

    if not license.is_active:
        raise HTTPException(status_code=400, detail="Licencia inactiva")

    if license.expiration_date < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Licencia vencida")

    activations = (
        db.query(Activation).filter(Activation.license_key == license_key).all()
    )

    if len(activations) >= license.max_devices:
        raise HTTPException(status_code=400, detail="Máximo de dispositivos alcanzado")

    # Verificar si ya está activado en esa máquina
    existing = (
        db.query(Activation)
        .filter(
            Activation.license_key == license_key, Activation.machine_id == machine_id
        )
        .first()
    )

    if existing:
        db.close()
        return {"message": "Licencia ya activada en este dispositivo"}

    new_activation = Activation(license_key=license_key, machine_id=machine_id)

    db.add(new_activation)
    db.commit()
    db.close()

    return {"message": "Licencia activada correctamente"}


# ==============================
# ✅ VALIDAR LICENCIA
# ==============================


@app.post("/validate")
def validate_license(license_key: str, machine_id: str):
    db: Session = SessionLocal()

    license = db.query(License).filter(License.license_key == license_key).first()

    if not license:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")

    if not license.is_active:
        raise HTTPException(status_code=400, detail="Licencia inactiva")

    if license.expiration_date < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Licencia vencida")

    activation = (
        db.query(Activation)
        .filter(
            Activation.license_key == license_key, Activation.machine_id == machine_id
        )
        .first()
    )

    if not activation:
        raise HTTPException(status_code=400, detail="Dispositivo no autorizado")

    db.close()

    return {"message": "Licencia válida"}
