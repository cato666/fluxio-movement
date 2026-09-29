"""Generate missing thumbnails without changing completed analysis results."""
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.main import RESULTS, UPLOADS, _thumbnail
from app.models import Analysis


def main():
    created = 0
    with SessionLocal() as session:
        rows = session.scalars(select(Analysis).where(Analysis.status == 'COMPLETED')).all()
        for row in rows:
            target = RESULTS / row.id / 'thumbnail.jpg'
            if row.thumbnail_path and target.exists():
                continue
            duration = (row.result or {}).get('video', {}).get('duration_s')
            if _thumbnail(UPLOADS / Path(row.video_path).name, target, duration):
                row.thumbnail_path = f'results/{row.id}/thumbnail.jpg'
                created += 1
        session.commit()
    print(f'Thumbnails generated: {created}')


if __name__ == '__main__':
    main()
