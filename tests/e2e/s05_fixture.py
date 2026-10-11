"""Fixture control for NEW, disposable S05 E2E databases only."""
import json
import os
import sys
from datetime import timedelta
from pathlib import Path
from uuid import UUID
from urllib.parse import urlsplit


def guard():
    url = urlsplit(os.environ.get('DATABASE_URL', ''))
    if (os.environ.get('S05_E2E_ISOLATED') != '1'
        or url.path != '/movement_e2e_s05'
        or url.hostname != os.environ.get('S05_E2E_DB_HOST')
        or not (url.hostname or '').startswith('fluxio-s05-e2e-db-')
        or Path(os.environ.get('STORAGE_PATH', '')).as_posix() != '/tmp/s05-e2e-storage'
        or any(os.environ.get(x, '').lower() != 'false' for x in
            ('WHATSAPP_ENABLED','TRAINING_AI_ENABLED','TRAINING_VOICE_ENABLED','AI_REASONING_ENABLED','ENABLE_DEMO_SEED'))
        or any(os.environ.get(x) for x in ('OPENAI_API_KEY','KAPSO_API_KEY'))):
        raise SystemExit('S05 E2E isolation guard rejected configuration')


guard()
from sqlalchemy import select, func
from app.database import SessionLocal
from app.models import User, Athlete, TrainingSession, WeeklyShare, TrainingImage, PlanInteraction
from app.services.auth import hash_password
from app.whatsapp.models import WhatsAppInbox, WhatsAppOutbox
from app.services.weekly_summary import now
OWNER = UUID('00000000-0000-4000-8000-000000000101')
OTHER = UUID('00000000-0000-4000-8000-000000000102')


def run(action, identifier=None):
    with SessionLocal() as session:
        if action == 'init':
            if session.scalar(select(func.count()).select_from(User)) != 0:
                raise RuntimeError('Fixture requires a newly migrated empty database')
            for identifier, username in ((OWNER, 's05-owner'), (OTHER, 's05-other')):
                session.add(User(id=identifier, demo_key=username, name='Synthetic E2E athlete',
                    role='ATHLETE', password_hash=hash_password('s05-synthetic-only')))
                session.flush()
                session.add(Athlete(user_id=identifier))
            session.commit()
            from PIL import Image
            Image.new('RGB',(32,32),'white').save('/tmp/s05-board.png')
            return {'initialized':True}
        if action == 'photo':
            import base64
            return {'png':base64.b64encode(Path('/tmp/s05-board.png').read_bytes()).decode()}
        if action == 'expire':
            share = session.get(WeeklyShare, UUID(identifier))
            if share is None or share.athlete_id != OWNER:
                raise RuntimeError('Unknown synthetic share')
            share.expires_at = now() - timedelta(seconds=1)
            session.commit()
            return {'expired':True}
        if action == 'deactivate':
            session.get(User, OWNER).is_active = False
            session.commit()
            return {'deactivated':True}
        if action != 'audit':
            raise RuntimeError('Unknown fixture action')
        images = list(session.scalars(select(TrainingImage)))
        root = Path(os.environ['STORAGE_PATH']).resolve()
        files_ok = all((root/'training-images'/image.path).resolve().is_relative_to(root)
            and (root/'training-images'/image.path).is_file() for image in images)
        shares = list(session.scalars(select(WeeklyShare).where(WeeklyShare.athlete_id == OWNER)))
        return {'sessions':session.scalar(select(func.count()).select_from(TrainingSession)),
            'shares':len(shares),'share_ids':[str(row.id) for row in shares],
            'consents_valid':all(row.snapshot.get('consent',{}).get('accepted') is True for row in shares),
            'images':len(images),'private_files_present':files_ok,
            'provider_operations':session.scalar(select(func.count()).select_from(PlanInteraction)),
            'inbox':session.scalar(select(func.count()).select_from(WhatsAppInbox)),
            'outbox':session.scalar(select(func.count()).select_from(WhatsAppOutbox))}


if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None)))
