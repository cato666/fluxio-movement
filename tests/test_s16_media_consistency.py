from pathlib import Path
import threading
import pytest
from sqlalchemy import text
from app.database import engine
from app.media_protocol import GC_LOCK, publish_bytes, publish_writer, reference_path
from app.services.media_lifecycle import remove_private

def test_partial_not_published_and_no_overwrite(tmp_path):
    target=tmp_path/'image.jpg'
    with pytest.raises(RuntimeError):
        with publish_writer(target) as out:
            out.write(b'partial')
            assert not target.exists()
            raise RuntimeError('interrupted')
    assert not target.exists()
    assert not list(tmp_path.iterdir())
    publish_bytes(target,b'first')
    with pytest.raises(FileExistsError):publish_bytes(target,b'other')
    assert target.read_bytes()==b'first'

def test_backup_pin_defers_delete_without_blocking(tmp_path):
    target=tmp_path/'photo';publish_bytes(target,b'photo')
    with engine.connect() as connection:
        connection.execute(text('SELECT pg_advisory_lock_shared(:k)'),{'k':GC_LOCK});connection.commit()
        result=[]
        thread=threading.Thread(target=lambda:result.append(remove_private(target)))
        thread.start();thread.join(3)
        assert not thread.is_alive() and result==[False] and target.exists()
        connection.execute(text('SELECT pg_advisory_unlock_shared(:k)'),{'k':GC_LOCK});connection.commit()
    assert remove_private(target) and not target.exists()

@pytest.mark.parametrize('table,path,result',[
 ('analyses','uploads/a.mp4','original/a.mp4'),
 ('analyses','results/x/annotated.mp4','annotated/x/annotated.mp4'),
 ('training_images','id.jpg','training-images/id.jpg'),
 ('whatsapp_media','/data/storage/original/whatsapp/a.mp4','original/whatsapp/a.mp4')])
def test_legacy_reference_mapping(table,path,result):
    assert reference_path(table,path,'/data/storage')==result

@pytest.mark.parametrize('path',['../bad','original/../../etc/passwd','/etc/passwd','temp/a','original/a\\b'])
def test_reference_rejects_unsafe(path):
    with pytest.raises(ValueError):reference_path('analyses',path,'/data/storage')


def test_unknown_commit_keeps_referenced_photo(session,tmp_path,monkeypatch):
    from uuid import uuid4
    from app.models import TrainingImage
    from app.seed import DEMO_ATHLETE_ID
    from app.services.training_service import TrainingService
    identifier=uuid4();target=tmp_path/(str(identifier)+'.jpg')
    class Media:
        def save_image(self,raw):
            publish_bytes(target,raw)
            return identifier,target
    service=TrainingService(session,DEMO_ATHLETE_ID,media=Media())
    def uncertain_commit():
        session.commit()
        raise RuntimeError('synthetic connection failure after successful commit')
    monkeypatch.setattr(service,'_persist',uncertain_commit)
    with pytest.raises(RuntimeError):service.store_image(b'complete synthetic photo')
    assert session.get(TrainingImage,identifier) is not None
    assert target.read_bytes()==b'complete synthetic photo'


@pytest.mark.parametrize('shared_analysis',[False,True])
def test_expired_whatsapp_media_is_pinned_and_shared_original_is_retained(session,tmp_path,monkeypatch,shared_analysis):
    from uuid import uuid4
    from datetime import datetime,timezone,timedelta
    from app.models import Analysis
    from app.seed import DEMO_ATHLETE_ID
    from app.whatsapp.models import WhatsAppInbox,WhatsAppMedia
    from app.whatsapp.worker import cleanup
    monkeypatch.setenv('STORAGE_PATH',str(tmp_path))
    relative='original/whatsapp/fixture.mp4';target=tmp_path/relative
    publish_bytes(target,b'synthetic complete video')
    inbox=WhatsAppInbox(provider='kapso',provider_message_id='synthetic.'+uuid4().hex,message_type='video',event='received',key_version='synthetic',happened_at=datetime.now(timezone.utc),expires_at=datetime.now(timezone.utc)+timedelta(hours=24))
    session.add(inbox);session.flush()
    media=WhatsAppMedia(inbox_id=inbox.id,athlete_id=DEMO_ATHLETE_ID,path=relative,media_type='video',expires_at=datetime.now(timezone.utc)-timedelta(seconds=1))
    session.add(media)
    if shared_analysis:
        session.add(Analysis(id=uuid4().hex,athlete_id=DEMO_ATHLETE_ID,status='FAILED',error='synthetic',original_filename='fixture.mp4',video_path='uploads/whatsapp/fixture.mp4'))
    session.commit()
    with engine.connect() as connection:
        connection.execute(text('SELECT pg_advisory_lock_shared(:k)'),{'k':GC_LOCK});connection.commit()
        cleanup(session)
        assert session.get(WhatsAppMedia,media.id) is not None and target.exists()
        connection.execute(text('SELECT pg_advisory_unlock_shared(:k)'),{'k':GC_LOCK});connection.commit()
    cleanup(session)
    assert session.get(WhatsAppMedia,media.id) is None
    assert target.exists()==shared_analysis
