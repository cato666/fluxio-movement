"""Isolated live HTTP fixture. Never import this in production.

Only external AI responses and pose inference use deterministic fixtures.
Routes, auth, training service, FFmpeg, media and PostgreSQL are real.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

if os.getenv('PHASE01_E2E') != '1' or os.getenv('TEST_DATABASE_RESET') != '1':
    raise RuntimeError('Explicit disposable E2E environment required')

from sqlalchemy import text
from app import main
from app.database import Base, SessionLocal, engine
from app.seed import seed
from app.services import workout_interpretation, training_transcription
from tests.test_api import RESULT
from tests.test_training_interpretation import draft, photo

if engine.url.database != 'movement_test':
    raise RuntimeError('E2E fixture must never target the application database')

os.environ['OPENAI_API_KEY'] = 'fixture-not-a-real-key'
os.environ['AI_REASONING_ENABLED'] = 'false'
os.environ['TRAINING_AI_ENABLED'] = 'true'
os.environ['TRAINING_VOICE_ENABLED'] = 'true'


def fixture_interpretation(body, key):
    assert body['store'] is False
    return {'output_text': json.dumps(draft()), 'model': 'fixture',
            'usage': {'input_tokens': 120, 'output_tokens': 80}}


class TranscriptionResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return json.dumps({'text': 'Hice 5 rondas de thrusters.',
                           'usage': {'input_tokens': 40, 'output_tokens': 10}}).encode()


def fixture_transcription(request, timeout):
    assert b'RIFF' in request.data  # Actual browser audio was decoded by FFmpeg.
    return TranscriptionResponse()


workout_interpretation._request = fixture_interpretation
training_transcription.urlopen = fixture_transcription

fixtures = Path('results/phase01/e2e-fixtures')
fixtures.mkdir(parents=True, exist_ok=True)
(fixtures / 'board.png').write_bytes(photo())
video = fixtures / 'video.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                'color=c=black:s=320x240:r=15:d=3', '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p', str(video)], check=True)
fixture_hash = hashlib.sha256(video.read_bytes()).digest()
real_preflight = main.validate_video_exercise


def preflight(path, exercise):
    if hashlib.sha256(Path(path).read_bytes()).digest() == fixture_hash:
        return None
    return real_preflight(path, exercise)


def fixture_analyzer(source, output, *args, **kwargs):
    assert hashlib.sha256(Path(source).read_bytes()).digest() == fixture_hash
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target / 'annotated.mp4')
    result = copy.deepcopy(RESULT)
    (target / 'analysis.json').write_text(json.dumps(result))
    return result


main.validate_video_exercise = preflight
main.analyze_video = fixture_analyzer
with engine.begin() as connection:
    names = ', '.join('"' + table.name + '"' for table in Base.metadata.sorted_tables)
    connection.execute(text(f'TRUNCATE {names} CASCADE'))
with SessionLocal.begin() as session:
    seed(session)

app = main.app
