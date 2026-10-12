"""Nonblocking physical GC fence. Deferred files remain private for reconciliation."""
from contextlib import contextmanager
from sqlalchemy import text
from ..media_protocol import GC_LOCK, sync_directory, reference_path, REFERENCE_COLUMNS

@contextmanager
def deletion_guard():
    from ..database import engine
    with engine.connect() as connection:
        locked = connection.scalar(text('SELECT pg_try_advisory_lock(:key)'), {'key': GC_LOCK})
        connection.commit()
        try: yield bool(locked)
        finally:
            if locked:
                connection.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': GC_LOCK})
                connection.commit()

def remove_private(path):
    with deletion_guard() as allowed:
        if not allowed: return False
        path.unlink(missing_ok=True)
        sync_directory(path.parent)
        return True


def live_references(session, application_root):
    """All persistent reference owners, while caller holds the exclusive GC fence."""
    paths = set()
    try:
        for table, columns in REFERENCE_COLUMNS.items():
            for values in session.execute(text('SELECT ' + ','.join(columns) + ' FROM ' + table)):
                for value in values:
                    path = reference_path(table, value, application_root)
                    if path: paths.add(path)
    except ValueError:
        return None  # Never delete in the presence of an unrecognized legacy path.
    return paths


def discard_uncommitted_image(path, identifier):
    """After caller rollback, prove no live reference before removing its new file."""
    from ..database import SessionLocal
    from ..models import TrainingImage
    from sqlalchemy import select
    try:
        with deletion_guard() as allowed:
            if not allowed: return False
            with SessionLocal() as fresh:
                if fresh.scalar(select(TrainingImage.id).where(TrainingImage.id == identifier)):
                    return False
            path.unlink(missing_ok=True)
            sync_directory(path.parent)
            return True
    except Exception:
        return False  # Unknown commit/connectivity: retain private bytes, never guess.
