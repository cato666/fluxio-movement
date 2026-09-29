import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import Base, SessionLocal, engine
from app import main
from app.seed import seed


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    # Fail closed: never erase the normal application database.
    if os.getenv('TEST_DATABASE_RESET') != '1' or engine.url.database != 'movement_test':
        raise RuntimeError('Tests require TEST_DATABASE_RESET=1 and database movement_test')
    command.upgrade(Config('alembic.ini'), 'head')
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(migrated_database):
    with engine.begin() as connection:
        names = ', '.join('"' + table.name + '"' for table in Base.metadata.sorted_tables)
        connection.execute(text(f'TRUNCATE {names} CASCADE'))
    with SessionLocal.begin() as session:
        seed(session)


@pytest.fixture
def session():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client(tmp_path, monkeypatch):
    uploads = tmp_path / 'uploads'
    results = tmp_path / 'results'
    analysis = tmp_path / 'analysis'
    temp = tmp_path / 'temp'
    uploads.mkdir()
    results.mkdir()
    analysis.mkdir()
    temp.mkdir()
    monkeypatch.setattr(main, 'UPLOADS', uploads)
    monkeypatch.setattr(main, 'RESULTS', results)
    monkeypatch.setattr(main, 'ANALYSIS_FILES', analysis)
    monkeypatch.setattr(main, 'TEMP', temp)
    static = next(route.app for route in main.app.routes if route.path == '/results')
    monkeypatch.setattr(static, 'all_directories', [str(results)])
    upload_static = next(route.app for route in main.app.routes if route.path == '/uploads')
    monkeypatch.setattr(upload_static, 'all_directories', [str(uploads)])
    analysis_static = next(route.app for route in main.app.routes if route.path == '/analysis')
    monkeypatch.setattr(analysis_static, 'all_directories', [str(analysis)])
    with TestClient(main.app) as client:
        yield client
