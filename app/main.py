from datetime import datetime, timezone
import base64
import json
from math import isfinite
from pathlib import Path
from uuid import UUID, uuid4
import logging
import os
import shutil
import subprocess
from alembic.config import Config
from alembic.script import ScriptDirectory

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import BadSignature, TimestampSigner
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .database import SessionLocal, get_session
from .models import AIObservation, AIObservationDecision, AIReasoningRun, AIReviewMoment, Analysis, Athlete, Coach, CoachAnnotation, CoachReview, Repetition, User
from .seed import DEMO_ATHLETE_ID
from .services.analyzer import analyze_video
from .services.ai_reasoning import run_reasoning
from .services.exercise_validation import validate_video_exercise
from .services.review_moments import rank_review_moments
from .services.auth import hash_password, verify_password

ROOT = Path(__file__).resolve().parents[1]
STORAGE_PATH = Path(os.environ.get('STORAGE_PATH', '/data/storage'))
ORIGINALS = STORAGE_PATH / 'original'
ANNOTATED = STORAGE_PATH / 'annotated'
ANALYSIS_FILES = STORAGE_PATH / 'analysis'
TEMP = STORAGE_PATH / 'temp'
# Compatibility names used by the existing analysis flow and test suite.
UPLOADS = ORIGINALS
RESULTS = ANNOTATED
try:
    MAX_UPLOAD_MB = int(os.environ.get('MAX_UPLOAD_MB', '250'))
except ValueError:
    MAX_UPLOAD_MB = 250
MAX_UPLOAD_BYTES = max(1, MAX_UPLOAD_MB) * 1024 * 1024
for directory in (ORIGINALS, ANNOTATED, ANALYSIS_FILES, TEMP):
    directory.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)
app = FastAPI(title='Movement Coach MVP')
SCHEMA_HEADS = set(ScriptDirectory.from_config(Config(str(ROOT / 'alembic.ini'))).get_heads())


@app.exception_handler(SQLAlchemyError)
async def persistence_unavailable(request: Request, exc: SQLAlchemyError):
    logger.error('Persistence unavailable on %s', request.url.path)
    return JSONResponse(status_code=503, content={'detail': 'Persistencia no disponible'})
app.mount('/static', StaticFiles(directory=str(ROOT / 'app' / 'static')), name='static')
app.mount('/results', StaticFiles(directory=str(RESULTS)), name='results')
app.mount('/uploads', StaticFiles(directory=str(UPLOADS)), name='uploads')
app.mount('/analysis', StaticFiles(directory=str(ANALYSIS_FILES)), name='analysis')


def _authenticated_user(request: Request, session: Session) -> User:
    user_id = request.session.get('user_id')
    user = session.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(401, 'Inicia sesión para continuar')
    return user


def _guard_user(request: Request, session: Session) -> User | None:
    """Read the signed Starlette session cookie from the outer route guard."""
    cookie = request.cookies.get('session')
    if not cookie:
        return None
    try:
        raw = TimestampSigner(os.environ.get('SESSION_SECRET', 'local-development-change-me')).unsign(cookie, max_age=60 * 60 * 24 * 14)
        payload = json.loads(base64.b64decode(raw))
        user_id = payload.get('user_id')
    except (BadSignature, ValueError, TypeError, json.JSONDecodeError):
        return None
    return session.get(User, user_id) if user_id else None


def require_athlete(request: Request, session: Session = Depends(get_session)) -> User:
    user = _authenticated_user(request, session)
    if user.role != 'ATHLETE':
        raise HTTPException(403, 'Esta sección es solo para atletas')
    return user


def require_coach(request: Request, session: Session = Depends(get_session)) -> User:
    user = _authenticated_user(request, session)
    if user.role != 'COACH':
        raise HTTPException(403, 'Esta sección es solo para coaches')
    return user


def require_internal(request: Request, session: Session = Depends(get_session)) -> User:
    user = _authenticated_user(request, session)
    if not user.is_internal:
        raise HTTPException(403, 'No tienes acceso a esta vista interna')
    return user


@app.middleware('http')
async def protect_application_routes(request: Request, call_next):
    """Central guard for the SPA, API and video assets.

    Endpoint-level checks still constrain ownership. This guard prevents an
    unauthenticated browser from opening a functional route or a stored video.
    """
    path = request.url.path
    public = {'/', '/demo', '/login', '/para-atletas', '/para-coaches', '/health', '/api/health', '/api/auth/login'}
    if path in public or path.startswith('/static') or path.startswith('/docs') or path.startswith('/openapi'):
        return await call_next(request)
    with SessionLocal() as session:
        try:
            user = _guard_user(request, session)
            if user is None:
                raise HTTPException(401)
        except HTTPException:
            if path.startswith('/api/') or path.startswith(('/uploads/', '/results/', '/analysis/')):
                return JSONResponse(status_code=401, content={'detail': 'Inicia sesión para continuar'})
            return RedirectResponse(url=f'/login?next={path}', status_code=303)
        except SQLAlchemyError:
            return JSONResponse(status_code=503, content={'detail': 'Persistencia no disponible'})
        if path.startswith('/internal/') or path.startswith('/api/internal/'):
            if not user.is_internal:
                if not path.startswith('/api/'):
                    return RedirectResponse(url='/login', status_code=303)
                return JSONResponse(status_code=403, content={'detail': 'No tienes acceso a esta vista interna'})
        elif path.startswith('/coach/') or path.startswith('/api/coach/'):
            if user.role != 'COACH':
                if not path.startswith('/api/'):
                    return RedirectResponse(url='/analyses', status_code=303)
                return JSONResponse(status_code=403, content={'detail': 'Esta sección es solo para coaches'})
            requested_coach = request.query_params.get('coach_id')
            if requested_coach and requested_coach != str(user.id):
                return JSONResponse(status_code=403, content={'detail': 'No puedes operar como otro coach'})
        elif path.startswith('/analyses') or path.startswith('/api/analyses') or path == '/api/analyze' or path == '/api/coaches':
            if user.role != 'ATHLETE':
                if not path.startswith('/api/'):
                    return RedirectResponse(url='/coach/reviews', status_code=303)
                return JSONResponse(status_code=403, content={'detail': 'Esta sección es solo para atletas'})
        if path.startswith(('/uploads/', '/results/', '/analysis/')):
            relative = path.lstrip('/')
            row = session.scalar(select(Analysis).where(
                (Analysis.video_path == relative) | (Analysis.annotated_video_path == relative) |
                (Analysis.analysis_json_path == relative) | (Analysis.thumbnail_path == relative)
            ))
            is_owner = row is not None and row.athlete_id == user.id
            is_assigned_coach = row is not None and user.role == 'COACH' and session.scalar(
                select(CoachReview.id).where(CoachReview.analysis_id == row.id, CoachReview.coach_id == user.id)
            ) is not None
            if not (is_owner or is_assigned_coach):
                return JSONResponse(status_code=403, content={'detail': 'No tienes acceso a este archivo'})
    return await call_next(request)


# Added after the route guard so the session is available to it on each request.
app.add_middleware(SessionMiddleware, secret_key=os.environ.get('SESSION_SECRET', 'local-development-change-me'), https_only=os.environ.get('APP_ENV') == 'production', same_site='lax')


@app.on_event('startup')
def recover_interrupted_analyses():
    with SessionLocal() as session:
        rows = session.scalars(select(Analysis).where(Analysis.status.in_(('PENDING', 'PROCESSING')))).all()
        for row in rows:
            row.status, row.stage = 'FAILED', None
            row.error = 'El análisis se interrumpió porque el servidor se reinició.'
            row.completed_at = datetime.now(timezone.utc)
        if rows:
            session.commit()


@app.get('/')
@app.get('/demo')
@app.get('/login')
@app.get('/para-atletas')
@app.get('/para-coaches')
@app.get('/analyses')
@app.get('/analyses/new')
@app.get('/analyses/{analysis_id}/request-review')
@app.get('/analyses/{analysis_id}')
@app.get('/coach/reviews/{review_id}')
@app.get('/coach/reviews')
@app.get('/coach/analyses/new')
@app.get('/coach/athletes/new')
@app.get('/internal/usage')
def home():
    return FileResponse(ROOT / 'app' / 'static' / 'index.html')


class LoginPayload(BaseModel):
    username: str
    password: str


@app.post('/api/auth/login')
def login(payload: LoginPayload, request: Request, session: Session = Depends(get_session)):
    username = payload.username.strip().casefold()
    user = session.scalar(select(User).where((User.demo_key == username) | (func.lower(User.name) == username)))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, 'Credenciales inválidas')
    request.session['user_id'] = str(user.id)
    next_path = '/analyses' if user.role == 'ATHLETE' else '/coach/reviews' if user.role == 'COACH' else '/internal/usage'
    return {'id': user.id, 'name': user.name, 'role': user.role, 'is_internal': user.is_internal, 'next': next_path}


@app.post('/api/auth/logout')
def logout(request: Request):
    request.session.clear()
    return {'ok': True}


@app.get('/api/auth/me')
def current_user(request: Request, session: Session = Depends(get_session)):
    user = _authenticated_user(request, session)
    return {'id': user.id, 'name': user.name, 'role': user.role, 'is_internal': user.is_internal}


@app.get('/api/health')
def health(session: Session = Depends(get_session)):
    try:
        session.execute(text('SELECT 1'))
        revision = session.execute(text('SELECT version_num FROM alembic_version')).scalar_one_or_none()
        if revision not in SCHEMA_HEADS:
            return JSONResponse(status_code=503, content={'ok': False, 'database': 'schema_not_ready'})
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={'ok': False, 'database': 'unavailable'})
    return {'ok': True, 'database': 'ready'}


@app.get('/health')
def deployment_health(session: Session = Depends(get_session)):
    try:
        session.execute(text('SELECT 1'))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={'ok': False})
    return {'ok': True}


@app.get('/api/internal/ai-usage')
def internal_ai_usage(_user: User = Depends(require_internal), session: Session = Depends(get_session)):
    """Demo-only operational view; exposes usage totals, never credentials."""
    completed = AIReasoningRun.status == 'COMPLETED'
    totals = session.execute(
        select(
            func.count(AIReasoningRun.id),
            func.coalesce(func.sum(AIReasoningRun.input_tokens), 0),
            func.coalesce(func.sum(AIReasoningRun.output_tokens), 0),
            func.coalesce(func.sum(AIReasoningRun.reasoning_tokens), 0),
        ).where(completed)
    ).one()
    by_model = session.execute(
        select(
            AIReasoningRun.model,
            func.count(AIReasoningRun.id),
            func.coalesce(func.sum(AIReasoningRun.input_tokens), 0),
            func.coalesce(func.sum(AIReasoningRun.output_tokens), 0),
        )
        .where(completed)
        .group_by(AIReasoningRun.model)
        .order_by(func.sum(AIReasoningRun.input_tokens + AIReasoningRun.output_tokens).desc())
    ).all()
    recent = session.execute(
        select(AIReasoningRun, Analysis)
        .join(Analysis, Analysis.id == AIReasoningRun.analysis_id)
        .order_by(AIReasoningRun.created_at.desc())
        .limit(25)
    ).all()
    input_tokens, output_tokens, reasoning_tokens = (int(value or 0) for value in totals[1:])
    return {
        'totals': {
            'completed_runs': int(totals[0] or 0),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'reasoning_tokens': reasoning_tokens,
            'total_tokens': input_tokens + output_tokens,
        },
        'by_model': [
            {
                'model': model or 'Sin modelo', 'runs': int(runs),
                'input_tokens': int(input_total or 0), 'output_tokens': int(output_total or 0),
                'total_tokens': int(input_total or 0) + int(output_total or 0),
            }
            for model, runs, input_total, output_total in by_model
        ],
        'recent_runs': [
            {
                'analysis_id': run.analysis_id, 'exercise': analysis.exercise,
                'status': run.status, 'model': run.model, 'input_tokens': run.input_tokens or 0,
                'output_tokens': run.output_tokens or 0, 'reasoning_tokens': run.reasoning_tokens or 0,
                'total_tokens': (run.input_tokens or 0) + (run.output_tokens or 0),
                'latency_ms': run.latency_ms, 'created_at': run.created_at,
            }
            for run, analysis in recent
        ],
    }


def _validate_upload(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(('.mp4', '.mov', '.m4v', '.avi')):
        raise HTTPException(400, 'Formato de video no soportado')
    if len(file.filename) > 255:
        raise HTTPException(400, 'Nombre de archivo demasiado largo')
    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f'El video supera el máximo de {MAX_UPLOAD_MB} MB')


class UploadTooLarge(Exception):
    pass


class _LimitedWriter:
    def __init__(self, target, maximum: int):
        self.target = target
        self.maximum = maximum
        self.written = 0

    def write(self, data):
        self.written += len(data)
        if self.written > self.maximum:
            raise UploadTooLarge()
        return self.target.write(data)


def _validate_metadata(exercise: str, objective: str, load_kg: float | None):
    exercise = exercise.strip()
    objective = objective.strip()
    if not exercise or len(exercise) > 100:
        raise HTTPException(400, 'Indica un ejercicio de hasta 100 caracteres')
    if not objective or len(objective) > 1000:
        raise HTTPException(400, 'Indica un objetivo de hasta 1000 caracteres')
    if load_kg is not None and (not isfinite(load_kg) or load_kg < 0):
        raise HTTPException(400, 'La carga debe ser un número no negativo en kg')
    return exercise, objective


def _validate_view(view: str) -> str:
    normalized = (view or '').strip().casefold()
    if normalized not in {'side', 'front'}:
        raise HTTPException(400, 'La vista debe ser de lado o de frente')
    return normalized


def _run_analysis(
    file: UploadFile, exercise: str, objective: str, load_kg: float | None,
    session: Session, legacy_response: bool = False, view: str = 'side',
    athlete_id: UUID = DEMO_ATHLETE_ID,
):
    _validate_upload(file)
    exercise, objective = _validate_metadata(exercise, objective, load_kg)
    view = _validate_view(view)
    job = uuid4().hex[:12]
    filename = Path(file.filename.replace('\\', '/')).name
    video = UPLOADS / f'{job}{Path(filename).suffix.lower()}'
    out = TEMP / job
    annotated = RESULTS / job / 'annotated.mp4'
    analysis_file = ANALYSIS_FILES / job / 'analysis.json'
    analysis = Analysis(
        id=job, athlete_id=athlete_id, exercise=exercise,
        load_kg=load_kg, objective=objective, original_filename=filename,
        video_path=f'uploads/{video.name}', view=view, status='PENDING',
    )
    try:
        if session.get(Athlete, athlete_id) is None:
            raise HTTPException(503, 'Ejecuta el seed demo antes de analizar')
        session.add(analysis)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot create analysis')
        raise HTTPException(503, 'Persistencia no disponible')

    try:
        with video.open('wb') as destination:
            shutil.copyfileobj(file.file, _LimitedWriter(destination, MAX_UPLOAD_BYTES))
        analysis.status = 'PROCESSING'
        session.commit()

        preflight = validate_video_exercise(str(video), exercise)

        # La vista lateral es la convención del flujo existente. Mantener esa
        # llamada posicional conserva integraciones previas; una vista elegida
        # explícitamente llega al analizador para validarla contra el perfil.
        if view.strip().casefold() == 'side':
            result = analyze_video(str(video), str(out), exercise)
        else:
            result = analyze_video(str(video), str(out), exercise, view)
        if preflight is not None:
            result['preflight'] = preflight
            (out / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        annotated.parent.mkdir(parents=True, exist_ok=True)
        analysis_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(out / 'annotated.mp4'), annotated)
        shutil.move(str(out / 'analysis.json'), analysis_file)
        shutil.rmtree(out, ignore_errors=True)
        result['job_id'] = job
        result['annotated_video_url'] = f'/results/{job}/annotated.mp4'
        result['analysis_url'] = f'/analysis/{job}/analysis.json'
        analysis.result = result
        analysis.status, analysis.progress, analysis.stage = 'COMPLETED', 100, None
        analysis.annotated_video_path = f'results/{job}/annotated.mp4'
        analysis.analysis_json_path = f'analysis/{job}/analysis.json'
        analysis.completed_at = datetime.now(timezone.utc)
        for rep in result['repetitions']:
            session.add(Repetition(
                analysis_id=job, number=rep['repetition'], start_s=rep['start_s'],
                bottom_s=rep['bottom_s'], end_s=rep['end_s'], metrics=rep,
            ))
        session.commit()
        _run_ai_reasoning(job, exercise, view, result)
        _generate_review_moments_safely(job, result)
        return result
    except Exception as exc:
        session.rollback()
        logger.exception('Analysis %s failed', job)
        try:
            saved = session.get(Analysis, job)
            saved.status = 'FAILED'
            saved.error = str(exc)[:2000] or type(exc).__name__
            saved.completed_at = datetime.now(timezone.utc)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            logger.exception('Cannot persist failure for %s', job)
        if legacy_response:
            raise HTTPException(500, 'Error de análisis; revisa los registros del servidor')
        if isinstance(exc, UploadTooLarge):
            video.unlink(missing_ok=True)
            raise HTTPException(413, {'message': f'El video supera el máximo de {MAX_UPLOAD_MB} MB', 'analysis_id': job})
        raise HTTPException(500, {'message': 'Error de análisis', 'analysis_id': job})


def _thumbnail(original: Path, target: Path, duration_s: float | None) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    moment = 1.0 if duration_s is None or duration_s >= 2 else max(0.0, duration_s / 2)
    result = subprocess.run([
        'ffmpeg', '-y', '-ss', str(moment), '-i', str(original), '-frames:v', '1',
        '-vf', 'scale=480:-2', '-q:v', '4', str(target),
    ], capture_output=True, text=True)
    if result.returncode or not target.exists() or not target.stat().st_size:
        logger.warning('Thumbnail failed for %s: %s', original.name, result.stderr[-300:])
        target.unlink(missing_ok=True)
        return False
    return True


def _set_progress(job: str, progress: int, stage: str):
    with SessionLocal() as session:
        row = session.get(Analysis, job)
        if row is not None and row.status == 'PROCESSING':
            row.progress, row.stage = max(0, min(100, int(progress))), stage
            session.commit()


def _process_analysis(job: str, exercise: str, view: str):
    """Runs in Starlette's threadpool after the 202 response is sent."""
    with SessionLocal() as session:
        row = session.get(Analysis, job)
        if row is None:
            return
        video = UPLOADS / Path(row.video_path).name
        out = TEMP / job
        annotated = RESULTS / job / 'annotated.mp4'
        analysis_file = ANALYSIS_FILES / job / 'analysis.json'
        try:
            _set_progress(job, 7, 'validating_exercise')
            preflight = validate_video_exercise(str(video), exercise)
            result = analyze_video(str(video), str(out), exercise, view, progress_callback=lambda p, s: _set_progress(job, p, s))
            if preflight is not None:
                result['preflight'] = preflight
                (out / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            _set_progress(job, 96, 'finalizing')
            annotated.parent.mkdir(parents=True, exist_ok=True)
            analysis_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(out / 'annotated.mp4'), annotated)
            shutil.move(str(out / 'analysis.json'), analysis_file)
            thumbnail = annotated.parent / 'thumbnail.jpg'
            has_thumbnail = _thumbnail(video, thumbnail, result.get('video', {}).get('duration_s'))
            shutil.rmtree(out, ignore_errors=True)
            row = session.get(Analysis, job)
            row.result = result
            row.status, row.progress, row.stage = 'PROCESSING', 97, 'generating_observations'
            row.annotated_video_path = f'results/{job}/annotated.mp4'
            row.analysis_json_path = f'analysis/{job}/analysis.json'
            row.thumbnail_path = f'results/{job}/thumbnail.jpg' if has_thumbnail else None
            row.completed_at = None
            for rep in result['repetitions']:
                session.add(Repetition(analysis_id=job, number=rep['repetition'], start_s=rep['start_s'], bottom_s=rep['bottom_s'], end_s=rep['end_s'], metrics=rep))
            session.commit()
            _run_ai_reasoning(job, exercise, view, result)
            _generate_review_moments_safely(job, result)
            row = session.get(Analysis, job)
            if row is not None:
                row.status, row.progress, row.stage = 'COMPLETED', 100, None
                row.completed_at = datetime.now(timezone.utc)
                session.commit()
        except Exception as exc:
            session.rollback()
            logger.exception('Async analysis %s failed', job)
            row = session.get(Analysis, job)
            if row is not None:
                row.status, row.stage = 'FAILED', None
                row.error, row.completed_at = (str(exc)[:2000] or type(exc).__name__), datetime.now(timezone.utc)
                session.commit()


def _run_ai_reasoning(analysis_id: str, exercise: str, view: str, result: dict):
    """Persists AI output separately: a provider failure never fails biomechanics."""
    with SessionLocal() as session:
        run = session.scalar(select(AIReasoningRun).where(AIReasoningRun.analysis_id == analysis_id))
        if run is None:
            run = AIReasoningRun(analysis_id=analysis_id, status='RUNNING')
            session.add(run)
            session.commit()
        try:
            reasoning = run_reasoning(exercise, view, result)
            if reasoning is None:
                run.status, run.completed_at = 'DISABLED', datetime.now(timezone.utc)
                session.commit()
                return
            analysis = session.get(Analysis, analysis_id)
            if analysis is not None:
                persisted_result = dict(analysis.result or {})
                persisted_result['ai_reasoning_summary'] = reasoning.summary
                analysis.result = persisted_result
            for observation in reasoning.observations[:5]:
                title = str(observation['title']).strip()[:240]
                description = str(observation['description']).strip()[:800]
                session.add(AIObservation(
                    analysis_id=analysis_id, body=f'{title}: {description}',
                    repetition_number=observation.get('repetition'), timestamp_s=observation.get('timestamp'),
                    category=str(observation['category']).strip()[:80], severity=observation['severity'],
                    title=title, description=description, evidence=str(observation['evidence']).strip()[:500],
                    confidence=observation['confidence'], model=reasoning.model,
                ))
            usage = reasoning.usage
            output_details = usage.get('output_tokens_details') or {}
            run.status, run.model = 'COMPLETED', reasoning.model
            run.error = None
            run.input_tokens = usage.get('input_tokens')
            run.output_tokens = usage.get('output_tokens')
            run.reasoning_tokens = output_details.get('reasoning_tokens') or usage.get('reasoning_tokens')
            run.latency_ms, run.completed_at = reasoning.latency_ms, datetime.now(timezone.utc)
            session.commit()
        except Exception as exc:
            session.rollback()
            run = session.scalar(select(AIReasoningRun).where(AIReasoningRun.analysis_id == analysis_id))
            if run is not None:
                run.status, run.completed_at = 'FAILED', datetime.now(timezone.utc)
                run.error = f'{type(exc).__name__}: {str(exc)[:400]}'
                session.commit()
            logger.warning('AI reasoning failed for analysis %s: %s', analysis_id, type(exc).__name__)


def _generate_review_moments_safely(analysis_id: str, result: dict):
    """Moments are advisory: an error here must never fail biomechanics."""
    try:
        _generate_review_moments(analysis_id, result)
    except Exception:
        logger.warning('Could not generate review moments for analysis %s', analysis_id, exc_info=True)


def _generate_review_moments(analysis_id: str, result: dict):
    with SessionLocal() as session:
        existing = session.scalars(select(AIReviewMoment).where(AIReviewMoment.analysis_id == analysis_id)).all()
        if existing:
            return
        observations = session.scalars(select(AIObservation).where(AIObservation.analysis_id == analysis_id)).all()
        source = [_ai_observation_fields(item) for item in observations]
        for item in rank_review_moments(result, source):
            observation = AIObservation(analysis_id=analysis_id, body=f"{item['title']}: {item['description']}", repetition_number=item['repetition_number'], timestamp_s=item['timestamp'], category='review_moment', severity='priority' if item['priority_score'] >= .9 else 'review', title=item['title'], description=item['description'], confidence=item['confidence'], model='deterministic-review-moments')
            session.add(observation); session.flush()
            session.add(AIReviewMoment(analysis_id=analysis_id, observation_id=observation.id, repetition_number=item['repetition_number'], timestamp_s=item['timestamp'], reason=item['reason'], confidence=item['confidence'], priority_score=item['priority_score']))
        session.commit()


def _prepare_async_analysis(file: UploadFile, exercise: str, objective: str, load_kg: float | None, view: str, session: Session, athlete_id: UUID = DEMO_ATHLETE_ID) -> Analysis:
    _validate_upload(file)
    exercise, objective = _validate_metadata(exercise, objective, load_kg)
    view = _validate_view(view)
    job = uuid4().hex[:12]
    filename = Path(file.filename.replace('\\', '/')).name
    video = UPLOADS / f'{job}{Path(filename).suffix.lower()}'
    row = Analysis(id=job, athlete_id=athlete_id, exercise=exercise, load_kg=load_kg, objective=objective, original_filename=filename, video_path=f'uploads/{video.name}', view=view, status='PENDING', progress=0, stage='uploading')
    if session.get(Athlete, athlete_id) is None:
        raise HTTPException(404, 'Atleta no encontrado')
    session.add(row)
    session.commit()
    try:
        with video.open('wb') as destination:
            shutil.copyfileobj(file.file, _LimitedWriter(destination, MAX_UPLOAD_BYTES))
        row.status, row.progress, row.stage = 'PROCESSING', 5, 'analyzing'
        session.commit()
        return row
    except Exception as exc:
        session.rollback()
        saved = session.get(Analysis, job)
        saved.status, saved.stage = 'FAILED', None
        saved.error, saved.completed_at = (str(exc)[:2000] or type(exc).__name__), datetime.now(timezone.utc)
        session.commit()
        if isinstance(exc, UploadTooLarge):
            video.unlink(missing_ok=True)
            raise HTTPException(413, {'message': f'El video supera el máximo de {MAX_UPLOAD_MB} MB', 'analysis_id': job})
        raise HTTPException(500, {'message': 'No se pudo guardar el video', 'analysis_id': job})


def _analysis_fields(row: Analysis, repetition_count: int):
    return {
        'id': row.id,
        'athlete_id': row.athlete_id,
        'created_at': row.created_at,
        'completed_at': row.completed_at,
        'exercise': row.exercise,
        'load_kg': row.load_kg,
        'objective': row.objective,
        'view': row.view,
        'source_analysis_id': row.source_analysis_id,
        'status': row.status,
        'progress': row.progress,
        'stage': row.stage,
        'thumbnail_url': f'/{row.thumbnail_path}' if row.thumbnail_path else None,
        'repetitions_detected': repetition_count,
    }


def _review_fields(review: CoachReview, coach: Coach, user: User):
    return {
        'id': review.id,
        'analysis_id': review.analysis_id,
        'athlete_id': review.athlete_id,
        'status': review.status,
        'created_at': review.created_at,
        'coach': {
            'id': coach.user_id,
            'name': user.name,
            'specialty': coach.specialty,
            'bio': coach.bio,
        },
    }


def _coach_context(coach_id: UUID, session: Session) -> Coach:
    coach = session.get(Coach, coach_id)
    if coach is None:
        raise HTTPException(404, 'Coach no encontrado')
    return coach


def _coach_review_fields(
    review: CoachReview, analysis: Analysis, athlete: User, repetition_count: int,
):
    return {
        'id': review.id,
        'status': review.status,
        'created_at': review.created_at,
        'athlete': {'id': athlete.id, 'name': athlete.name},
        'analysis': {
            **_analysis_fields(analysis, repetition_count),
            'original_filename': analysis.original_filename,
            'original_video_url': f'/{analysis.video_path}' if analysis.video_path else None,
            'annotated_video_url': f'/{analysis.annotated_video_path}' if analysis.annotated_video_path else None,
            'analysis_json_url': f'/{analysis.analysis_json_path}' if analysis.analysis_json_path else None,
            'analysis_json': analysis.result,
        },
    }


class CoachReviewRequest(BaseModel):
    coach_id: UUID


class CoachAnnotationCreate(BaseModel):
    timestamp_s: float
    type: str
    text: str
    repetition_number: int | None = None


class CoachAnnotationUpdate(BaseModel):
    type: str | None = None
    text: str | None = None
    repetition_number: int | None = None


class RepetitionClassificationUpdate(BaseModel):
    classification: str | None = None
    correction_status: str | None = None
    correction_note: str | None = None


class ManualRepetitionCreate(BaseModel):
    start_s: float
    bottom_s: float
    end_s: float
    correction_note: str | None = None


class CoachReviewSummaryUpdate(BaseModel):
    strengths: str | None = None
    main_focus: str | None = None
    next_session: str | None = None
    summary: str | None = None


class AIObservationDecisionUpdate(BaseModel):
    decision: str
    title: str | None = None
    description: str | None = None
    severity: str | None = None


class AnalysisReanalyzeRequest(BaseModel):
    exercise: str
    view: str = 'side'


class CoachAthleteCreate(BaseModel):
    name: str
    username: str
    password: str


@app.post('/api/analyze')
def analyze(
    file: UploadFile = File(...), athlete: User = Depends(require_athlete),
    session: Session = Depends(get_session),
):
    """Original API contract, retained for the F1.1 client."""
    return _run_analysis(
        file, 'Sin especificar', 'Análisis técnico', None, session,
        legacy_response=True, athlete_id=athlete.id,
    )


@app.post('/api/analyses', status_code=202)
def create_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), exercise: str = Form(...),
    objective: str = Form(...), load_kg: float | None = Form(None), view: str = Form('side'),
    athlete: User = Depends(require_athlete), session: Session = Depends(get_session),
):
    row = _prepare_async_analysis(file, exercise, objective, load_kg, view, session, athlete.id)
    background_tasks.add_task(_process_analysis, row.id, exercise, view)
    session.expire_all()
    return _get_analysis(row.id, athlete.id, session)


@app.get('/api/coach/athletes')
def list_coach_athletes(_coach: User = Depends(require_coach), session: Session = Depends(get_session)):
    rows = session.execute(select(Athlete, User).join(User, User.id == Athlete.user_id).order_by(User.name)).all()
    return {'items': [{'id': athlete.user_id, 'name': user.name} for athlete, user in rows]}


@app.post('/api/coach/athletes', status_code=201)
def create_coach_athlete(payload: CoachAthleteCreate, _coach: User = Depends(require_coach), session: Session = Depends(get_session)):
    name = payload.name.strip()
    username = payload.username.strip().casefold()
    if not name or len(name) > 160:
        raise HTTPException(400, 'Indica el nombre del atleta')
    if len(username) < 3 or len(username) > 40 or any(char not in 'abcdefghijklmnopqrstuvwxyz0123456789._-' for char in username):
        raise HTTPException(400, 'El usuario debe tener entre 3 y 40 caracteres: letras, números, punto, guion o guion bajo')
    if len(payload.password) < 8 or len(payload.password) > 200:
        raise HTTPException(400, 'La contraseña debe tener entre 8 y 200 caracteres')
    athlete_id = uuid4()
    user = User(id=athlete_id, demo_key=username, name=name, role='ATHLETE', password_hash=hash_password(payload.password), is_internal=False)
    try:
        session.add(user)
        session.flush()
        session.add(Athlete(user_id=athlete_id))
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, 'Ese usuario ya está registrado')
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, 'No se pudo registrar el atleta')
    return {'id': athlete_id, 'name': name, 'username': username}


@app.post('/api/coach/analyses', status_code=202)
def create_coach_analysis(
    background_tasks: BackgroundTasks, athlete_id: UUID = Form(...), file: UploadFile = File(...),
    exercise: str = Form(...), objective: str = Form(...), load_kg: float | None = Form(None), view: str = Form('side'),
    coach: User = Depends(require_coach), session: Session = Depends(get_session),
):
    row = _prepare_async_analysis(file, exercise, objective, load_kg, view, session, athlete_id)
    review = CoachReview(analysis_id=row.id, athlete_id=athlete_id, coach_id=coach.id, status='PENDING')
    try:
        session.add(review)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, 'No se pudo asignar la revisión al coach')
    background_tasks.add_task(_process_analysis, row.id, exercise, view)
    return {'id': row.id, 'review_id': review.id, 'status': row.status, 'athlete_id': athlete_id}


@app.post('/api/analyses/{analysis_id}/reanalyze', status_code=202)
def reanalyze_analysis(
    analysis_id: str, payload: AnalysisReanalyzeRequest,
    background_tasks: BackgroundTasks, athlete: User = Depends(require_athlete),
    session: Session = Depends(get_session),
):
    source = session.get(Analysis, analysis_id)
    if source is None or source.athlete_id != athlete.id:
        raise HTTPException(404, 'Análisis no encontrado')
    if source.status not in {'COMPLETED', 'FAILED'}:
        raise HTTPException(409, 'Espera a que el análisis actual termine antes de reanalizarlo')
    if not source.video_path or not (UPLOADS / Path(source.video_path).name).exists():
        raise HTTPException(409, 'El video original ya no está disponible para reanalizar')
    exercise, objective = _validate_metadata(payload.exercise, source.objective or 'Reanálisis técnico', source.load_kg)
    view = _validate_view(payload.view)
    job = uuid4().hex[:12]
    row = Analysis(
        id=job, athlete_id=athlete.id, status='PROCESSING', progress=5, stage='reanalyzing',
        exercise=exercise, view=view, load_kg=source.load_kg, objective=objective,
        original_filename=source.original_filename, video_path=source.video_path, source_analysis_id=source.id,
    )
    try:
        session.add(row)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot create reanalysis for %s', analysis_id)
        raise HTTPException(503, 'Persistencia no disponible')
    background_tasks.add_task(_process_analysis, row.id, exercise, view)
    session.expire_all()
    return _get_analysis(row.id, athlete.id, session)


@app.get('/api/analyses')
def list_analyses(athlete: User = Depends(require_athlete), session: Session = Depends(get_session)):
    counts = (
        select(Repetition.analysis_id, func.count().label('count'))
        .group_by(Repetition.analysis_id).subquery()
    )
    rows = session.execute(
        select(Analysis, func.coalesce(counts.c.count, 0))
        .outerjoin(counts, counts.c.analysis_id == Analysis.id)
        .where(Analysis.athlete_id == athlete.id)
        .order_by(Analysis.created_at.desc(), Analysis.id.desc())
    ).all()
    # Fetch review metadata once for this athlete's analyses, without N+1 reads.
    reviews_by_analysis = {}
    if rows:
        review_rows = session.execute(
            select(CoachReview, Coach, User)
            .join(Coach, Coach.user_id == CoachReview.coach_id)
            .join(User, User.id == Coach.user_id)
            .where(CoachReview.analysis_id.in_([row.id for row, _ in rows]))
            .order_by(CoachReview.created_at.desc())
        ).all()
        for review, coach, user in review_rows:
            reviews_by_analysis.setdefault(review.analysis_id, []).append(_review_fields(review, coach, user))
    return {'items': [dict(_analysis_fields(row, count), coach_reviews=reviews_by_analysis.get(row.id, [])) for row, count in rows]}


@app.get('/api/coaches')
def list_coaches(session: Session = Depends(get_session)):
    rows = session.execute(
        select(Coach, User)
        .join(User, User.id == Coach.user_id)
        .order_by(User.name)
    ).all()
    return {'items': [
        {'id': coach.user_id, 'name': user.name, 'specialty': coach.specialty, 'bio': coach.bio}
        for coach, user in rows
    ]}


@app.post('/api/analyses/{analysis_id}/request-review', status_code=201)
def request_review(
    analysis_id: str, payload: CoachReviewRequest,
    athlete: User = Depends(require_athlete), session: Session = Depends(get_session),
):
    analysis = session.get(Analysis, analysis_id)
    if analysis is None or analysis.athlete_id != athlete.id:
        raise HTTPException(404, 'Análisis no encontrado')
    if analysis.status != 'COMPLETED':
        raise HTTPException(409, 'Solo puedes solicitar revisión de un análisis completado')
    coach = session.get(Coach, payload.coach_id)
    if coach is None:
        raise HTTPException(404, 'Coach no encontrado')
    user = session.get(User, payload.coach_id)
    review = CoachReview(
        analysis_id=analysis.id, athlete_id=analysis.athlete_id,
        coach_id=coach.user_id, status='PENDING',
    )
    try:
        session.add(review)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, 'Ya existe una solicitud activa para este coach y análisis')
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot create review request for %s', analysis_id)
        raise HTTPException(503, 'Persistencia no disponible')
    return _review_fields(review, coach, user)


@app.get('/api/coach/reviews')
def list_coach_reviews(
    coach_id: UUID, status: str | None = None,
    session: Session = Depends(get_session),
):
    _coach_context(coach_id, session)
    valid_statuses = {'PENDING', 'IN_REVIEW', 'COMPLETED'}
    if status is not None and status not in valid_statuses:
        raise HTTPException(400, 'Estado de revisión no válido')
    counts = select(Repetition.analysis_id, func.count().label('count')).where(Repetition.correction_status == 'ACTIVE').group_by(Repetition.analysis_id).subquery()
    statement = (
        select(CoachReview, Analysis, User, func.coalesce(counts.c.count, 0))
        .join(Analysis, Analysis.id == CoachReview.analysis_id)
        .join(User, User.id == CoachReview.athlete_id)
        .outerjoin(counts, counts.c.analysis_id == Analysis.id)
        .where(CoachReview.coach_id == coach_id)
        .order_by(CoachReview.created_at.desc())
    )
    if status is not None:
        statement = statement.where(CoachReview.status == status)
    return {'items': [
        _coach_review_fields(review, analysis, athlete, count)
        for review, analysis, athlete, count in session.execute(statement).all()
    ]}


def _get_coach_review(review_id: UUID, coach_id: UUID, session: Session):
    _coach_context(coach_id, session)
    count = select(func.count()).select_from(Repetition).where(Repetition.analysis_id == CoachReview.analysis_id, Repetition.correction_status == 'ACTIVE').scalar_subquery()
    row = session.execute(
        select(CoachReview, Analysis, User, count)
        .join(Analysis, Analysis.id == CoachReview.analysis_id)
        .join(User, User.id == CoachReview.athlete_id)
        .where(CoachReview.id == review_id, CoachReview.coach_id == coach_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(404, 'Revisión no encontrada')
    review, analysis, athlete, repetition_count = row
    return review, _coach_review_fields(review, analysis, athlete, repetition_count)


@app.get('/api/coach/reviews/{review_id}')
def get_coach_review(
    review_id: UUID, coach_id: UUID, session: Session = Depends(get_session),
):
    review, payload = _get_coach_review(review_id, coach_id, session)
    reps = session.scalars(
        select(Repetition).where(Repetition.analysis_id == review.analysis_id).order_by(Repetition.number)
    ).all()
    payload['analysis']['repetitions'] = [
        {'id': rep.id, 'number': rep.number, 'start_s': rep.start_s,
         'bottom_s': rep.bottom_s, 'end_s': rep.end_s, 'metrics': rep.metrics,
         'source': rep.source, 'correction_status': rep.correction_status,
         'correction_note': rep.correction_note,
         'classification': (
             'BEST' if rep.id == review.best_repetition_id else
             'NEEDS_WORK' if rep.id == review.work_repetition_id else 'NORMAL'
         )}
        for rep in reps
    ]
    payload['summary'] = {
        'strengths': review.strengths,
        'main_focus': review.main_focus,
        'next_session': review.next_session,
        'summary': review.summary,
    }
    decisions = {item.observation_id: item.decision for item in session.scalars(
        select(AIObservationDecision).where(AIObservationDecision.review_id == review.id)
    ).all()}
    moment_rows = session.scalars(select(AIReviewMoment).where(AIReviewMoment.analysis_id == review.analysis_id).order_by(AIReviewMoment.priority_score.desc())).all()
    moment_ids = {row.observation_id for row in moment_rows}
    observations = session.scalars(
        select(AIObservation).where(AIObservation.analysis_id == review.analysis_id)
        .order_by(AIObservation.timestamp_s, AIObservation.created_at)
    ).all()
    payload['ai_observations'] = [
        _ai_observation_fields(observation, decisions.get(observation.id)) for observation in observations if observation.id not in moment_ids
    ]
    payload['review_moments'] = [{**_ai_observation_fields(session.get(AIObservation, row.observation_id), decisions.get(row.observation_id)), 'reason': row.reason, 'priority_score': row.priority_score} for row in moment_rows]
    return payload


@app.patch('/api/coach/reviews/{review_id}/start')
def start_coach_review(
    review_id: UUID, coach_id: UUID, session: Session = Depends(get_session),
):
    review, payload = _get_coach_review(review_id, coach_id, session)
    if review.status == 'PENDING':
        review.status = 'IN_REVIEW'
        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            logger.exception('Cannot start review %s', review_id)
            raise HTTPException(503, 'Persistencia no disponible')
        payload['status'] = review.status
    return payload


ANNOTATION_TYPES = {'COMMENT', 'REVIEW', 'CORRECT', 'PRIORITY'}


def _annotation_fields(annotation: CoachAnnotation):
    return {
        'id': annotation.id,
        'timestamp_s': annotation.timestamp_s,
        'type': annotation.annotation_type,
        'text': annotation.text,
        'repetition_number': annotation.repetition_number,
        'created_at': annotation.created_at,
        'updated_at': annotation.updated_at,
    }


def _ai_observation_fields(observation: AIObservation, decision: str | None = None):
    return {
        'id': observation.id, 'analysis_id': observation.analysis_id,
        'repetition': observation.repetition_number, 'timestamp': observation.timestamp_s,
        'category': observation.category or 'observación', 'severity': observation.severity or 'review',
        'title': observation.title or observation.body, 'description': observation.description or observation.body,
        'evidence': observation.evidence,
        'confidence': observation.confidence or 'low', 'model': observation.model,
        'created_at': observation.created_at, 'decision': decision,
    }


def _editable_review(review_id: UUID, coach_id: UUID, session: Session) -> CoachReview:
    review, _ = _get_coach_review(review_id, coach_id, session)
    if review.status == 'COMPLETED':
        raise HTTPException(409, 'No se puede modificar una revisión completada')
    return review


def _validate_annotation(
    analysis: Analysis, timestamp_s: float, annotation_type: str, body: str,
    repetition_number: int | None, session: Session,
):
    if not isfinite(timestamp_s) or timestamp_s < 0:
        raise HTTPException(400, 'El timestamp debe ser un número no negativo')
    duration = (analysis.result or {}).get('video', {}).get('duration_s')
    try:
        duration = float(duration)
    except (TypeError, ValueError):
        raise HTTPException(409, 'El análisis no tiene duración de video disponible')
    if not isfinite(duration):
        raise HTTPException(409, 'El análisis no tiene duración de video disponible')
    if timestamp_s > duration:
        raise HTTPException(400, 'El timestamp supera la duración del video')
    if annotation_type not in ANNOTATION_TYPES:
        raise HTTPException(400, 'Tipo de anotación no válido')
    if not body.strip() or len(body) > 2000:
        raise HTTPException(400, 'El comentario debe tener entre 1 y 2000 caracteres')
    if repetition_number is not None:
        exists = session.scalar(
            select(Repetition.id).where(
                Repetition.analysis_id == analysis.id,
                Repetition.number == repetition_number,
            )
        )
        if exists is None:
            raise HTTPException(400, 'La repetición indicada no existe en este análisis')


@app.get('/api/coach/reviews/{review_id}/annotations')
def list_coach_annotations(
    review_id: UUID, coach_id: UUID, session: Session = Depends(get_session),
):
    _get_coach_review(review_id, coach_id, session)
    items = session.scalars(
        select(CoachAnnotation)
        .where(CoachAnnotation.review_id == review_id, CoachAnnotation.coach_id == coach_id)
        .order_by(CoachAnnotation.timestamp_s, CoachAnnotation.created_at)
    ).all()
    return {'items': [_annotation_fields(item) for item in items]}


@app.post('/api/coach/reviews/{review_id}/annotations', status_code=201)
def create_coach_annotation(
    review_id: UUID, payload: CoachAnnotationCreate, coach_id: UUID,
    session: Session = Depends(get_session),
):
    review = _editable_review(review_id, coach_id, session)
    analysis = session.get(Analysis, review.analysis_id)
    _validate_annotation(
        analysis, payload.timestamp_s, payload.type, payload.text,
        payload.repetition_number, session,
    )
    annotation = CoachAnnotation(
        review_id=review.id, coach_id=coach_id, timestamp_s=payload.timestamp_s,
        annotation_type=payload.type, text=payload.text.strip(),
        repetition_number=payload.repetition_number,
    )
    if review.status == 'PENDING':
        review.status = 'IN_REVIEW'
    try:
        session.add(annotation)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot create annotation for review %s', review_id)
        raise HTTPException(503, 'Persistencia no disponible')
    return _annotation_fields(annotation)


@app.patch('/api/coach/reviews/{review_id}/annotations/{annotation_id}')
def update_coach_annotation(
    review_id: UUID, annotation_id: UUID, payload: CoachAnnotationUpdate,
    coach_id: UUID, session: Session = Depends(get_session),
):
    review = _editable_review(review_id, coach_id, session)
    annotation = session.scalar(select(CoachAnnotation).where(
        CoachAnnotation.id == annotation_id,
        CoachAnnotation.review_id == review.id,
        CoachAnnotation.coach_id == coach_id,
    ))
    if annotation is None:
        raise HTTPException(404, 'Anotación no encontrada')
    fields = payload.model_fields_set
    if not fields:
        raise HTTPException(400, 'Indica un cambio para la anotación')
    annotation_type = payload.type if 'type' in fields else annotation.annotation_type
    body = payload.text if 'text' in fields else annotation.text
    repetition_number = payload.repetition_number if 'repetition_number' in fields else annotation.repetition_number
    analysis = session.get(Analysis, review.analysis_id)
    _validate_annotation(analysis, annotation.timestamp_s, annotation_type, body, repetition_number, session)
    annotation.annotation_type = annotation_type
    annotation.text = body.strip()
    annotation.repetition_number = repetition_number
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot update annotation %s', annotation_id)
        raise HTTPException(503, 'Persistencia no disponible')
    return _annotation_fields(annotation)


@app.delete('/api/coach/reviews/{review_id}/annotations/{annotation_id}', status_code=204)
def delete_coach_annotation(
    review_id: UUID, annotation_id: UUID, coach_id: UUID,
    session: Session = Depends(get_session),
):
    review = _editable_review(review_id, coach_id, session)
    annotation = session.scalar(select(CoachAnnotation).where(
        CoachAnnotation.id == annotation_id,
        CoachAnnotation.review_id == review.id,
        CoachAnnotation.coach_id == coach_id,
    ))
    if annotation is None:
        raise HTTPException(404, 'Anotación no encontrada')
    try:
        session.delete(annotation)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot delete annotation %s', annotation_id)
        raise HTTPException(503, 'Persistencia no disponible')


@app.get('/api/coach/reviews/{review_id}/ai-observations')
def list_ai_observations_for_coach(
    review_id: UUID, coach_id: UUID, session: Session = Depends(get_session),
):
    review, _ = _get_coach_review(review_id, coach_id, session)
    decisions = {item.observation_id: item.decision for item in session.scalars(
        select(AIObservationDecision).where(AIObservationDecision.review_id == review.id)
    ).all()}
    items = session.scalars(
        select(AIObservation).where(AIObservation.analysis_id == review.analysis_id)
        .order_by(AIObservation.timestamp_s, AIObservation.created_at)
    ).all()
    return {'items': [_ai_observation_fields(item, decisions.get(item.id)) for item in items]}


@app.patch('/api/coach/reviews/{review_id}/ai-observations/{observation_id}')
def decide_ai_observation(
    review_id: UUID, observation_id: UUID, payload: AIObservationDecisionUpdate,
    coach_id: UUID, session: Session = Depends(get_session),
):
    review = _editable_review(review_id, coach_id, session)
    observation = session.scalar(select(AIObservation).where(
        AIObservation.id == observation_id, AIObservation.analysis_id == review.analysis_id,
    ))
    if observation is None:
        raise HTTPException(404, 'Observación IA no encontrada')
    if payload.decision not in {'CONFIRMED', 'DISMISSED'}:
        raise HTTPException(400, 'Decisión IA no válida')
    if payload.title is not None:
        if not payload.title.strip() or len(payload.title) > 240:
            raise HTTPException(400, 'El título debe tener entre 1 y 240 caracteres')
        observation.title = payload.title.strip()
    if payload.description is not None:
        if not payload.description.strip() or len(payload.description) > 800:
            raise HTTPException(400, 'La descripción debe tener entre 1 y 800 caracteres')
        observation.description = payload.description.strip()
    if payload.severity is not None:
        if payload.severity not in {'info', 'review', 'priority'}:
            raise HTTPException(400, 'Severidad IA no válida')
        observation.severity = payload.severity
    observation.body = f'{observation.title or observation.body}: {observation.description or observation.body}'
    decision = session.get(AIObservationDecision, (review.id, observation.id))
    if decision is None:
        decision = AIObservationDecision(
            review_id=review.id, observation_id=observation.id,
            analysis_id=review.analysis_id, decision=payload.decision,
        )
        session.add(decision)
    else:
        decision.decision = payload.decision
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot decide AI observation %s', observation_id)
        raise HTTPException(503, 'Persistencia no disponible')
    return _ai_observation_fields(observation, decision.decision)


@app.patch('/api/coach/reviews/{review_id}/repetitions/{repetition_id}')
def classify_review_repetition(
    review_id: UUID, repetition_id: UUID, payload: RepetitionClassificationUpdate,
    coach_id: UUID, session: Session = Depends(get_session),
):
    review = _editable_review(review_id, coach_id, session)
    repetition = session.scalar(select(Repetition).where(
        Repetition.id == repetition_id, Repetition.analysis_id == review.analysis_id,
    ))
    if repetition is None:
        raise HTTPException(404, 'Repetición no encontrada')
    if payload.classification is None and payload.correction_status is None and payload.correction_note is None:
        raise HTTPException(400, 'Indica una clasificación o corrección')
    if payload.correction_status is not None:
        if payload.correction_status not in {'ACTIVE', 'DISCARDED'}:
            raise HTTPException(400, 'Estado de corrección no válido')
        repetition.correction_status = payload.correction_status
        if payload.correction_status == 'DISCARDED':
            if review.best_repetition_id == repetition.id:
                review.best_repetition_id = None
            if review.work_repetition_id == repetition.id:
                review.work_repetition_id = None
    if payload.correction_note is not None:
        if len(payload.correction_note) > 1000:
            raise HTTPException(400, 'La nota debe tener hasta 1000 caracteres')
        repetition.correction_note = payload.correction_note.strip() or None
    if payload.classification is not None and payload.classification not in {'BEST', 'NEEDS_WORK', 'NORMAL'}:
        raise HTTPException(400, 'Clasificación no válida')
    if payload.classification == 'BEST':
        if repetition.correction_status != 'ACTIVE':
            raise HTTPException(409, 'Restaura la repetición antes de clasificarla')
        review.best_repetition_id = repetition.id
        if review.work_repetition_id == repetition.id:
            review.work_repetition_id = None
    elif payload.classification == 'NEEDS_WORK':
        if repetition.correction_status != 'ACTIVE':
            raise HTTPException(409, 'Restaura la repetición antes de clasificarla')
        review.work_repetition_id = repetition.id
        if review.best_repetition_id == repetition.id:
            review.best_repetition_id = None
    elif payload.classification == 'NORMAL':
        if review.best_repetition_id == repetition.id:
            review.best_repetition_id = None
        if review.work_repetition_id == repetition.id:
            review.work_repetition_id = None
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot classify repetition %s', repetition_id)
        raise HTTPException(503, 'Persistencia no disponible')
    return {
        'repetition_id': repetition.id,
        'classification': payload.classification,
        'correction_status': repetition.correction_status,
        'correction_note': repetition.correction_note,
        'best_repetition_id': review.best_repetition_id,
        'work_repetition_id': review.work_repetition_id,
    }


@app.post('/api/coach/reviews/{review_id}/repetitions', status_code=201)
def create_manual_repetition(
    review_id: UUID, payload: ManualRepetitionCreate, coach_id: UUID,
    session: Session = Depends(get_session),
):
    review = _editable_review(review_id, coach_id, session)
    analysis = session.get(Analysis, review.analysis_id)
    duration = float((analysis.result or {}).get('video', {}).get('duration_s') or 0)
    if not (0 <= payload.start_s <= payload.bottom_s <= payload.end_s):
        raise HTTPException(400, 'Los timestamps de la repetición no son válidos')
    if duration and payload.end_s > duration:
        raise HTTPException(400, 'La repetición no puede exceder la duración del video')
    if payload.end_s - payload.start_s < .15:
        raise HTTPException(400, 'La repetición manual debe durar al menos 0.15 segundos')
    number = (session.scalar(select(func.max(Repetition.number)).where(Repetition.analysis_id == review.analysis_id)) or 0) + 1
    repetition = Repetition(
        analysis_id=review.analysis_id, number=number, start_s=payload.start_s,
        bottom_s=payload.bottom_s, end_s=payload.end_s, source='MANUAL',
        correction_status='ACTIVE', correction_note=(payload.correction_note or '').strip() or None,
        metrics={'manual': True, 'count_confidence': 'coach'},
    )
    try:
        session.add(repetition)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot add manual repetition to %s', review_id)
        raise HTTPException(503, 'Persistencia no disponible')
    return {'id': repetition.id, 'number': repetition.number, 'source': repetition.source,
            'correction_status': repetition.correction_status, 'start_s': repetition.start_s,
            'bottom_s': repetition.bottom_s, 'end_s': repetition.end_s}


@app.patch('/api/coach/reviews/{review_id}/summary')
def update_coach_review_summary(
    review_id: UUID, payload: CoachReviewSummaryUpdate, coach_id: UUID,
    session: Session = Depends(get_session),
):
    review = _editable_review(review_id, coach_id, session)
    fields = payload.model_fields_set
    if not fields:
        raise HTTPException(400, 'Indica un cambio para el resumen')
    for field in fields:
        value = getattr(payload, field)
        if value is not None and len(value) > 4000:
            raise HTTPException(400, 'Cada campo debe tener hasta 4000 caracteres')
        setattr(review, field, value.strip() if value is not None else None)
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot update review summary %s', review_id)
        raise HTTPException(503, 'Persistencia no disponible')
    return {
        'strengths': review.strengths, 'main_focus': review.main_focus,
        'next_session': review.next_session, 'summary': review.summary,
    }


@app.post('/api/coach/reviews/{review_id}/complete')
def complete_coach_review(
    review_id: UUID, coach_id: UUID, session: Session = Depends(get_session),
):
    review = _editable_review(review_id, coach_id, session)
    if review.status != 'IN_REVIEW':
        raise HTTPException(409, 'La revisión debe estar en curso para finalizarla')
    has_annotations = session.scalar(select(CoachAnnotation.id).where(
        CoachAnnotation.review_id == review.id, CoachAnnotation.coach_id == coach_id,
    ))
    if has_annotations is None:
        raise HTTPException(409, 'Agrega al menos una anotación antes de finalizar')
    if not review.main_focus or not review.main_focus.strip():
        raise HTTPException(409, 'Indica el principal punto a trabajar')
    if not review.next_session or not review.next_session.strip():
        raise HTTPException(409, 'Indica la próxima sesión')
    review.status = 'COMPLETED'
    review.completed_at = datetime.now(timezone.utc)
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('Cannot complete review %s', review_id)
        raise HTTPException(503, 'Persistencia no disponible')
    return {'id': review.id, 'status': review.status, 'completed_at': review.completed_at}


def _get_analysis(analysis_id: str, athlete_id: UUID, session: Session):
    row = session.get(Analysis, analysis_id)
    if row is None or row.athlete_id != athlete_id:
        raise HTTPException(404, 'Análisis no encontrado')
    reps = session.scalars(
        select(Repetition).where(Repetition.analysis_id == analysis_id, Repetition.correction_status == 'ACTIVE').order_by(Repetition.number)
    ).all()
    review_rows = session.execute(
        select(CoachReview, Coach, User)
        .join(Coach, Coach.user_id == CoachReview.coach_id)
        .join(User, User.id == Coach.user_id)
        .where(CoachReview.analysis_id == analysis_id)
        .order_by(CoachReview.created_at.desc())
    ).all()
    repetitions_by_id = {rep.id: rep for rep in reps}
    ai_observations = session.scalars(
        select(AIObservation).where(AIObservation.analysis_id == analysis_id).order_by(AIObservation.timestamp_s, AIObservation.created_at)
    ).all()
    review_moment_observation_ids = set(session.scalars(
        select(AIReviewMoment.observation_id).where(AIReviewMoment.analysis_id == analysis_id)
    ).all())
    reasoning_run = session.scalar(select(AIReasoningRun).where(AIReasoningRun.analysis_id == analysis_id))
    completed_reviews = []
    for review, coach, user in review_rows:
        if review.status != 'COMPLETED':
            continue
        annotations = session.scalars(
            select(CoachAnnotation)
            .where(CoachAnnotation.review_id == review.id)
            .order_by(CoachAnnotation.timestamp_s, CoachAnnotation.created_at)
        ).all()
        def selected_repetition(rep_id: UUID | None):
            rep = repetitions_by_id.get(rep_id)
            return None if rep is None else {
                'id': rep.id, 'number': rep.number, 'start_s': rep.start_s,
                'bottom_s': rep.bottom_s, 'end_s': rep.end_s,
            }
        completed_reviews.append({
            'id': review.id,
            'completed_at': review.completed_at,
            'coach': {'id': coach.user_id, 'name': user.name, 'specialty': coach.specialty},
            'best_repetition': selected_repetition(review.best_repetition_id),
            'work_repetition': selected_repetition(review.work_repetition_id),
            'strengths': review.strengths,
            'main_focus': review.main_focus,
            'next_session': review.next_session,
            'summary': review.summary,
            'annotations': [_annotation_fields(annotation) for annotation in annotations],
        })
    return {
        **_analysis_fields(row, len(reps)),
        'original_filename': row.original_filename,
        'original_video_url': f'/{row.video_path}' if row.video_path else None,
        'annotated_video_url': f'/{row.annotated_video_path}' if row.annotated_video_path else None,
        'analysis_json_url': f'/{row.analysis_json_path}' if row.analysis_json_path else None,
        'analysis_json': row.result,
        'repetitions': [
            {'id': rep.id, 'number': rep.number, 'start_s': rep.start_s,
             'bottom_s': rep.bottom_s, 'end_s': rep.end_s, 'metrics': rep.metrics,
             'source': rep.source, 'correction_status': rep.correction_status}
            for rep in reps
        ],
        'coach_reviews': [
            _review_fields(review, coach, user)
            for review, coach, user in review_rows
        ],
        'completed_coach_reviews': completed_reviews,
        # Review moments are rendered separately for coaches. They may originate from
        # the same IA observation and must not be repeated in the athlete view.
        'ai_observations': [
            _ai_observation_fields(observation)
            for observation in ai_observations
            if observation.id not in review_moment_observation_ids
        ],
        'ai_reasoning': None if reasoning_run is None else {
            'status': reasoning_run.status, 'model': reasoning_run.model,
            'summary': (row.result or {}).get('ai_reasoning_summary'),
        },
        'error': row.error,
    }


@app.get('/api/analyses/{analysis_id}')
def get_analysis(
    analysis_id: str, athlete: User = Depends(require_athlete),
    session: Session = Depends(get_session),
):
    return _get_analysis(analysis_id, athlete.id, session)
