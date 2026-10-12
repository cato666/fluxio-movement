"""Shared S16 media protocol: immutable publication and canonical DB references."""
from contextlib import contextmanager
from pathlib import Path
import os
import shutil
import tempfile

PROTOCOL = 'immutable-v1'
GC_LOCK = 6416012601
REFERENCE_COLUMNS = {
    'training_images': ('path',),
    'analyses': ('video_path', 'annotated_video_path', 'analysis_json_path', 'thumbnail_path'),
    'whatsapp_media': ('path',),
}

def sync_directory(path):
    if os.name == 'posix':
        fd = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)

@contextmanager
def publish_writer(target):
    """Publish a complete file without replacing any existing generation."""
    target = Path(target)
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError('unsafe_media_path')
    target.parent.mkdir(parents=True, exist_ok=True)
    sync_directory(target.parent.parent)
    fd, name = tempfile.mkstemp(prefix='.unpublished-', dir=target.parent)
    temporary = Path(name)
    # Private owner/group read enables the explicitly mounted backup read group.
    os.chmod(temporary, 0o640)
    try:
        with os.fdopen(fd, 'wb') as stream:
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        # Hard-link is atomic and fails if destination exists (no overwrite).
        os.link(temporary, target)
        sync_directory(target.parent)
    finally:
        temporary.unlink(missing_ok=True)
        sync_directory(target.parent)

def publish_bytes(target, data):
    with publish_writer(target) as stream: stream.write(data)

def publish_file(source, target):
    with Path(source).open('rb') as source_stream, publish_writer(target) as destination:
        shutil.copyfileobj(source_stream, destination)

def reference_path(table, value, application_root):
    """Keep legacy uploads/results aliases; never silently accept traversal."""
    if not value: return None
    if not isinstance(value, str) or '\\' in value or '\x00' in value:
        raise ValueError('invalid_media_reference')
    path = Path(value)
    if path.is_absolute():
        path = path.relative_to(Path(application_root))
    if any(p in ('..', '.', '') for p in path.parts) or not path.parts:
        raise ValueError('invalid_media_reference')
    parts = list(path.parts)
    if table == 'training_images' and len(parts) == 1:
        parts.insert(0, 'training-images')
    parts[0] = {'uploads': 'original', 'results': 'annotated'}.get(parts[0], parts[0])
    if parts[0] not in ('training-images', 'original', 'annotated', 'analysis') or len(parts) < 2:
        raise ValueError('invalid_media_reference')
    return '/'.join(parts)
