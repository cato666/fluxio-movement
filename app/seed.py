"""Idempotent demo data. Run explicitly: python -m app.seed."""
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert

from .database import SessionLocal
from .models import Athlete, Coach, User

DEMO_ATHLETE_ID = UUID("00000000-0000-4000-8000-000000000001")
DEMOS = (
    (DEMO_ATHLETE_ID, "gaston", "Gastón Demo", "ATHLETE", None),
    (UUID("00000000-0000-4000-8000-000000000002"), "carlos", "Carlos", "COACH", "Weightlifting", "Técnica de levantamientos olímpicos y progresiones de fuerza."),
    (UUID("00000000-0000-4000-8000-000000000003"), "andrea", "Andrea", "COACH", "Fuerza", "Entrenamiento de fuerza para construir movimiento sólido y sostenible."),
    (UUID("00000000-0000-4000-8000-000000000004"), "pablo", "Pablo", "COACH", "CrossFit", "Rendimiento funcional y técnica aplicada a movimientos de CrossFit."),
)


def seed(session):
    for demo in DEMOS:
        user_id, key, name, role, specialty, *bio = demo
        session.execute(insert(User).values(id=user_id, demo_key=key, name=name, role=role).on_conflict_do_nothing(index_elements=[User.id]))
        profile = Athlete if role == "ATHLETE" else Coach
        values = {"user_id": user_id}
        if specialty:
            values["specialty"] = specialty
            values["bio"] = bio[0]
        session.execute(insert(profile).values(**values).on_conflict_do_nothing(index_elements=[profile.user_id]))


if __name__ == "__main__":
    with SessionLocal.begin() as session:
        seed(session)
    print("Demo seed ready: 1 athlete, 3 coaches")
