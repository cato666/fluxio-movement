"""Idempotent demo data. Run explicitly: python -m app.seed."""
import os
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert

from .database import SessionLocal
from .models import Athlete, Coach, User
from .services.auth import hash_password

DEMO_ATHLETE_ID = UUID("00000000-0000-4000-8000-000000000001")
DEMOS = (
    (DEMO_ATHLETE_ID, "gaston", "Gastón Demo", "ATHLETE", None, False),
    (UUID("00000000-0000-4000-8000-000000000002"), "carlos", "Carlos", "COACH", "Weightlifting", "Técnica de levantamientos olímpicos y progresiones de fuerza.", False),
    (UUID("00000000-0000-4000-8000-000000000003"), "anais", "Annais", "COACH", "Fuerza", "Entrenamiento de fuerza para construir movimiento sólido y sostenible.", False),
    (UUID("00000000-0000-4000-8000-000000000004"), "pablo", "Pablo", "COACH", "CrossFit", "Rendimiento funcional y técnica aplicada a movimientos de CrossFit.", False),
    (UUID("00000000-0000-4000-8000-000000000005"), "admin", "Administrador del sistema", "SYSTEM_ADMIN", None, True),
)


def seed(session):
    for demo in DEMOS:
        user_id, key, name, role, specialty, *bio, is_internal = demo
        session.execute(insert(User).values(id=user_id, demo_key=key, name=name, role=role, password_hash=hash_password(os.environ.get('DEMO_PASSWORD', 'demo1234')), is_internal=is_internal).on_conflict_do_update(index_elements=[User.id], set_={'demo_key': key, 'password_hash': hash_password(os.environ.get('DEMO_PASSWORD', 'demo1234')), 'is_internal': is_internal}))
        profile = Athlete if role == "ATHLETE" else Coach if role == "COACH" else None
        if profile is None:
            continue
        values = {"user_id": user_id}
        if specialty:
            values["specialty"] = specialty
            values["bio"] = bio[0]
        session.execute(insert(profile).values(**values).on_conflict_do_nothing(index_elements=[profile.user_id]))


if __name__ == "__main__":
    with SessionLocal.begin() as session:
        seed(session)
    print("Demo seed ready: 1 athlete, 3 coaches")
