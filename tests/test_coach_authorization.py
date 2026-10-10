"""S03 isolation: two athletes, two coaches, admin, and no external providers."""
from datetime import datetime, timezone
from uuid import uuid4
import pytest
from sqlalchemy import select, func
from app import main
from app.models import User, Athlete, Analysis, CoachReview, PlanInteraction, Repetition, CoachAnnotation, AIObservation
from app.seed import DEMO_ATHLETE_ID, DEMOS

COACH_A = DEMOS[1][0]
COACH_B = DEMOS[2][0]


def login(client, username='carlos'):
    result = client.post('/api/auth/login', json={'username': username, 'password': 'demo1234'})
    assert result.status_code == 200, result.text


@pytest.fixture
def resources(session, client):
    other = uuid4()
    session.add(User(id=other, name='Other athlete fixture', demo_key='other.fixture', role='ATHLETE',
        password_hash=session.get(User, DEMO_ATHLETE_ID).password_hash))
    session.flush()
    session.add(Athlete(user_id=other))
    session.flush()
    rows = []
    for identifier, athlete in [('alpha', DEMO_ATHLETE_ID), ('beta', other), ('alpha-unassigned', DEMO_ATHLETE_ID)]:
        row = Analysis(id=identifier, athlete_id=athlete, status='COMPLETED', exercise='Press',
            objective='Private fixture objective', original_filename=identifier+'.mp4', video_path='uploads/'+identifier+'.mp4',
            annotated_video_path='results/'+identifier+'.mp4', analysis_json_path='analysis/'+identifier+'.json',
            thumbnail_path='results/'+identifier+'.jpg', completed_at=datetime.now(timezone.utc),
            result={'video': {'duration_s': 12}, 'summary_metrics': {}})
        session.add(row)
        rows.append(row)
        for root, filename in [(main.UPLOADS,identifier+'.mp4'),(main.RESULTS,identifier+'.mp4'),
                               (main.RESULTS,identifier+'.jpg'),(main.ANALYSIS_FILES,identifier+'.json')]:
            (root/filename).write_bytes(b'private-fixture')
    session.flush()
    reviews = [CoachReview(analysis_id='alpha', athlete_id=DEMO_ATHLETE_ID, coach_id=COACH_A),
               CoachReview(analysis_id='beta', athlete_id=other, coach_id=COACH_B)]
    session.add_all(reviews)
    session.commit()
    login(client)
    return other, reviews


def test_lists_are_scoped_and_not_searchable_by_foreign_athlete(resources, client):
    other, reviews = resources
    for suffix in ('', '?athlete_id='+str(other), '?search=Other'):
        result = client.get('/api/coach/athletes'+suffix)
        assert result.status_code == 200
        assert [u['id'] for u in result.json()['items']] == [str(DEMO_ATHLETE_ID)]
        assert 'Other athlete fixture' not in result.text
    result = client.get('/api/coach/reviews', params={'coach_id': str(COACH_A)})
    assert [u['id'] for u in result.json()['items']] == [str(reviews[0].id)]
    login(client, 'anais')
    assert [u['id'] for u in client.get('/api/coach/athletes').json()['items']] == [str(other)]


@pytest.mark.parametrize('analysis', ['alpha', 'beta', 'alpha-unassigned', 'missing'])
def test_upload_denied_even_with_existing_review(resources, client, session, monkeypatch, analysis):
    monkeypatch.setattr(main, '_prepare_async_analysis', lambda *_: pytest.fail('Unauthorized upload'))
    monkeypatch.setattr(main, 'consume', lambda *_: pytest.fail('Unauthorized quota'))
    target = str(resources[0]) if analysis == 'beta' else str(DEMO_ATHLETE_ID) if analysis != 'missing' else str(uuid4())
    response = client.post('/api/coach/analyses', data={'athlete_id': target, 'exercise': 'Press', 'objective': 'Test'},
        files={'file': ('fixture.mp4', b'video', 'video/mp4')})
    assert response.status_code == 403
    assert session.scalar(select(func.count()).select_from(Analysis)) == 3
    assert session.scalar(select(func.count()).select_from(PlanInteraction)) == 0


OPERATIONS = [
    ('GET', '', None), ('PATCH','/start', None),
    ('GET','/annotations',None), ('POST','/annotations',{'timestamp_s':1,'type':'COMMENT','text':'fixture'}),
    ('PATCH','/annotations/{child}',{'text':'fixture'}), ('DELETE','/annotations/{child}',None),
    ('GET','/ai-observations',None), ('PATCH','/ai-observations/{child}',{'decision':'CONFIRMED'}),
    ('PATCH','/repetitions/{child}',{'classification':'BEST'}),
    ('POST','/repetitions',{'start_s':0,'bottom_s':1,'end_s':2}),
    ('PATCH','/summary',{'main_focus':'fixture','next_session':'fixture'}), ('POST','/complete',None),
]


@pytest.mark.parametrize('method,suffix,body', OPERATIONS)
def test_foreign_review_ids_and_missing_have_same_error(resources, client, session, method, suffix, body):
    child = str(uuid4())
    suffix = suffix.format(child=child)
    foreign = resources[1][1].id
    responses = [client.request(method, f'/api/coach/reviews/{identifier}{suffix}',
        params={'coach_id':str(COACH_A)}, json=body) for identifier in (foreign,uuid4())]
    assert responses[0].status_code == responses[1].status_code == 404
    assert responses[0].json() == responses[1].json()
    assert 'Other athlete fixture' not in responses[0].text
    session.expire_all()
    assert session.get(CoachReview,foreign).status == 'PENDING'


@pytest.mark.parametrize('root,extension', [('uploads','.mp4'),('results','.mp4'),('results','.jpg'),('analysis','.json')])
def test_media_analysis_scope_and_no_cache(resources, client, root, extension):
    own = client.get('/'+root+'/alpha'+extension)
    assert own.status_code == 200
    assert own.headers['cache-control'] == 'private, no-store'
    denied = [client.get('/'+root+'/'+name+extension) for name in ('beta','alpha-unassigned','missing')]
    assert all(r.status_code == 403 for r in denied)
    assert denied[0].json() == denied[2].json()


def test_query_identity_cannot_be_spoofed_or_duplicated(resources, client):
    url = '/api/coach/reviews/'+str(resources[1][1].id)
    assert client.get(url, params={'coach_id':str(COACH_B)}).status_code == 403
    assert client.get(url).status_code == 422
    assert client.get(url+'?coach_id='+str(COACH_A)+'&coach_id='+str(COACH_B)).status_code == 403
    assert client.get(url+'?coach_id='+str(COACH_B)+'&coach_id='+str(COACH_A)).status_code == 404


def test_coach_cannot_use_athlete_or_global_admin_apis(resources, client, session):
    session.get(User, COACH_A).is_internal = True
    session.commit()
    for path in ('/api/admin/users','/api/internal/ai-usage','/api/analyses/alpha',
                 '/api/analyses/beta','/api/training-sessions', '/api/training-sessions/images/'+str(uuid4())):
        assert client.get(path).status_code == 403


def test_admin_operations_and_athlete_owner_access(resources, client):
    login(client, 'admin')
    assert client.get('/api/admin/users').status_code == 200
    assert client.get('/api/internal/ai-usage').status_code == 200
    created = client.post('/api/admin/users', json={'name':'Pilot fixture','username':'pilot.fixture',
        'password':'fixture1234','role':'ATHLETE'})
    assert created.status_code == 201
    login(client,'gaston')
    assert client.get('/api/analyses/alpha').status_code == 200
    assert client.get('/uploads/alpha.mp4').status_code == 200
    assert client.get('/api/analyses/beta').status_code == 404
    assert client.get('/uploads/beta.mp4').status_code == 403
    assert client.get('/api/training-sessions').status_code == 200


def test_inactive_athlete_hides_assigned_data_and_coach_disabled_cookie(resources, client, session):
    session.get(User, DEMO_ATHLETE_ID).is_active = False
    session.commit()
    assert client.get('/api/coach/athletes').json()['items'] == []
    assert client.get('/api/coach/reviews',params={'coach_id':str(COACH_A)}).json()['items'] == []
    assert client.get('/api/coach/reviews/'+str(resources[1][0].id),params={'coach_id':str(COACH_A)}).status_code == 404
    assert client.get('/uploads/alpha.mp4').status_code == 403
    session.get(User, COACH_A).is_active = False
    session.commit()
    assert client.get('/api/coach/athletes').status_code == 401
    assert client.get('/uploads/alpha.mp4').status_code == 401


def test_inactive_coach_cannot_receive_new_grant(resources, client, session):
    session.get(User, COACH_B).is_active = False
    session.commit()
    login(client,'gaston')
    assert str(COACH_B) not in [u['id'] for u in client.get('/api/coaches').json()['items']]
    assert client.post('/api/analyses/alpha/request-review',json={'coach_id':str(COACH_B)}).status_code == 404


def test_reanalysis_shared_original_respects_assigned_reference(resources, client, session):
    session.get(Analysis,'alpha').video_path = 'uploads/alpha-unassigned.mp4'
    session.commit()
    assert client.get('/uploads/alpha-unassigned.mp4').status_code == 200
    assert client.get('/results/alpha-unassigned.mp4').status_code == 403


def test_owned_review_cannot_reference_foreign_children(resources, client, session):
    foreign = resources[1][1]
    rep = Repetition(analysis_id='beta',number=1,start_s=0,bottom_s=1,end_s=2,metrics={})
    obs = AIObservation(analysis_id='beta', body='Private observation')
    note = CoachAnnotation(review_id=foreign.id, coach_id=COACH_B,timestamp_s=1,annotation_type='COMMENT',text='Private note')
    session.add_all([rep,obs,note]);session.commit()
    base = '/api/coach/reviews/'+str(resources[1][0].id)
    for path, body in [('/repetitions/'+str(rep.id),{'classification':'BEST'}),
                       ('/ai-observations/'+str(obs.id),{'decision':'CONFIRMED'}),
                       ('/annotations/'+str(note.id),{'text':'changed'})]:
        assert client.patch(base+path,params={'coach_id':str(COACH_A)},json=body).status_code == 404
    session.expire_all()
    assert session.get(CoachAnnotation,note.id).text == 'Private note'


def test_owner_request_to_assigned_coach_completion(resources, client):
    login(client,'gaston')
    requested = client.post('/api/analyses/alpha-unassigned/request-review',json={'coach_id':str(COACH_A)})
    assert requested.status_code == 201
    identifier = requested.json()['id']
    login(client)
    query = {'coach_id':str(COACH_A)}
    base = '/api/coach/reviews/'+identifier
    assert client.get(base,params=query).status_code == 200
    assert client.patch(base+'/start',params=query).json()['status'] == 'IN_REVIEW'
    assert client.post(base+'/annotations',params=query,json={'timestamp_s':1,'type':'PRIORITY','text':'Fixture focus'}).status_code == 201
    assert client.patch(base+'/summary',params=query,json={'main_focus':'Fixture focus','next_session':'Fixture practice'}).status_code == 200
    assert client.post(base+'/complete',params=query).json()['status'] == 'COMPLETED'
    login(client,'gaston')
    detail = client.get('/api/analyses/alpha-unassigned').json()
    assert any(r['id']==identifier and r['status']=='COMPLETED' for r in detail['coach_reviews'])
