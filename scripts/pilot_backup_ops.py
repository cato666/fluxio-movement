"""S16 operations around the validated FXS16GCM1 backup format.

No database collection, infrastructure installation, restore, or deletion here.
The collector and transport must be supplied and authorized by the operator.
"""
import argparse
import hashlib
import io
import json
import os
import tarfile
from datetime import datetime, timezone, timedelta
from pathlib import Path, PurePosixPath
from uuid import uuid4
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b'FXS16GCM1'
AAD = b'fluxio-s16-synthetic-v1'  # Compatibility with the validated synthetic format.
REQUIRED = {'training-images', 'original', 'annotated', 'analysis'}
MAX_BYTES = 128 * 1024 * 1024
CODES = {'BACKUP_COMPLETE','BACKUP_FAILED','BACKUP_INCOMPLETE','BACKUP_MISSING','BACKUP_STALE','BACKUP_BUSY','ALERT_DELIVERY_FAILED'}

class BackupError(Exception):
    """Fixed operational code; never carries private paths or provider bodies."""

def utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is None:
        raise BackupError('invalid_timestamp')
    return value.astimezone(timezone.utc)

def archive_bytes(parts, directories=()):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w') as archive:
        for name in sorted(directories):
            info = tarfile.TarInfo(name)
            info.type = tarfile.DIRTYPE
            info.mode = 0o700
            archive.addfile(info)
        for name, value in parts.items():
            info = tarfile.TarInfo(name)
            info.size = len(value)
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(value))
    return stream.getvalue()

def members(blob):
    if len(blob) > MAX_BYTES:
        raise BackupError('size_limit')
    result = {}
    seen = set()
    total = 0
    with tarfile.open(fileobj=io.BytesIO(blob), mode='r:') as archive:
        for info in archive:
            name = PurePosixPath(info.name)
            canonical = name.as_posix()
            if (name.is_absolute() or '..' in name.parts or canonical in seen
                    or info.size < 0 or not (info.isfile() or info.isdir())):
                raise BackupError('unsafe_archive')
            seen.add(canonical)
            if info.isdir():
                continue  # Includes safe ./ directories from the original trial tar.
            if canonical == '.':
                raise BackupError('unsafe_archive')
            total += info.size
            if total > MAX_BYTES:
                raise BackupError('size_limit')
            result[canonical] = archive.extractfile(info).read()
    return result

def seal_snapshot(dump, storage, key):
    """Caller must already have a coherent, authorized dump/storage snapshot."""
    if len(key) != 32 or not dump.startswith(b'PGDMP'):
        raise BackupError('invalid_snapshot')
    storage = Path(storage)
    if storage.is_symlink() or not storage.is_dir():
        raise BackupError('invalid_storage')
    if any(not (storage / name).is_dir() or (storage / name).is_symlink() for name in REQUIRED):
        raise BackupError('incomplete_storage')
    parts = {}
    directories = set()
    size = len(dump)
    for path in sorted(storage.rglob('*')):
        if path.is_symlink():
            raise BackupError('unsafe_storage')
        if path.is_file():
            size += path.stat().st_size
            if size > MAX_BYTES:
                raise BackupError('size_limit')
            parts[path.relative_to(storage).as_posix()] = path.read_bytes()
        elif path.is_dir():
            directories.add(path.relative_to(storage).as_posix())
        else:
            raise BackupError('unsafe_storage')
    payloads = {'postgres.dump': dump, 'storage.tar': archive_bytes(parts, directories)}
    manifest = {name: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
                for name, data in payloads.items()}
    payloads['manifest.json'] = json.dumps(manifest, sort_keys=True).encode()
    plain = archive_bytes(payloads)
    if len(plain) > MAX_BYTES:
        raise BackupError('size_limit')
    nonce = os.urandom(12)
    return MAGIC + nonce + AESGCM(key).encrypt(nonce, plain, AAD)

def verify_bundle(blob, key):
    if not blob.startswith(MAGIC) or len(blob) > MAX_BYTES + 64 or len(key) != 32:
        raise BackupError('invalid_bundle')
    try:
        plain = AESGCM(key).decrypt(blob[9:21], blob[21:], AAD)
        payloads = members(plain)
        if set(payloads) != {'postgres.dump', 'storage.tar', 'manifest.json'}:
            raise BackupError('incomplete_bundle')
        manifest = json.loads(payloads['manifest.json'])
        if set(manifest) != {'postgres.dump', 'storage.tar'}:
            raise BackupError('invalid_manifest')
        for name in manifest:
            data = payloads[name]
            if len(data) != manifest[name]['bytes'] or hashlib.sha256(data).hexdigest() != manifest[name]['sha256']:
                raise BackupError('integrity_failed')
        if not payloads['postgres.dump'].startswith(b'PGDMP'):
            raise BackupError('invalid_dump')
        members(payloads['storage.tar'])  # Validate safe entries without extracting anything.
        return payloads
    except BackupError:
        raise
    except Exception:
        raise BackupError('verification_failed') from None

def receipt(path, value):
    """Opaque operational fields only; atomic publish after verified remote read."""
    path = Path(path)
    temp = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    with temp.open('x', encoding='utf-8') as stream:
        os.chmod(temp, 0o600)
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)

def event(code, backup_id=None):
    if code not in CODES:
        raise BackupError('invalid_event')
    if backup_id is not None and (len(backup_id) != 32 or any(c not in '0123456789abcdef' for c in backup_id)):
        raise BackupError('invalid_id')
    return {'code': code, 'backup_id': backup_id}

def run_job(state, kind, collect, put, get, key, notify, now=None):
    """Injection points preserve the existing collector/S3 implementation.

    collect returns bytes dump + a quiesced snapshot directory, never a live
    storage root. notify must positively acknowledge delivery. No retries or deletes.
    """
    if kind not in ('daily', 'pre-release'):
        raise BackupError('invalid_kind')
    now = utc(now or datetime.now(timezone.utc))
    state = Path(state)
    state.mkdir(parents=True, exist_ok=True)
    lock = state / 'backup.lock'
    try:
        lock.mkdir()
    except FileExistsError:
        return {'status': 'BLOCKED', 'code': 'BACKUP_BUSY'}
    identifier = uuid4().hex
    value = {'id': identifier, 'kind': kind, 'status': 'INCOMPLETE', 'started_at': now.isoformat()}
    try:
        receipt(state / (identifier + '.json'), value)
        dump, storage = collect()
        blob = seal_snapshot(dump, storage, key)
        verify_bundle(blob, key)
        object_name = 'backups/' + kind + '/' + identifier + '.aes256gcm'
        put(object_name, blob)
        remote = get(object_name)
        if hashlib.sha256(remote).digest() != hashlib.sha256(blob).digest():
            raise BackupError('remote_integrity_failed')
        verify_bundle(remote, key)
        value.update(status='COMPLETE', verified_at=datetime.now(timezone.utc).isoformat(),
                     snapshot_at=now.isoformat(), encrypted_bytes=len(blob),
                     encrypted_sha256=hashlib.sha256(blob).hexdigest())
        receipt(state / (identifier + '.json'), value)
        return value
    except Exception:
        value['status'] = 'INCOMPLETE'
        receipt(state / (identifier + '.json'), value)
        try:
            delivered = notify(event('BACKUP_FAILED', identifier)) is True
        except Exception:
            delivered = False
        value['alert_delivery'] = 'ACKNOWLEDGED' if delivered else 'FAILED'
        receipt(state / (identifier + '.json'), value)
        return value
    finally:
        lock.rmdir()  # Only this invocation's empty lock; never touches backups.

def health(records, now, stale_hours=24):
    now = utc(now)
    if stale_hours <= 0:
        raise BackupError('invalid_threshold')
    complete = [r for r in records if r['status'] == 'COMPLETE']
    codes = []
    if not complete:
        codes.append('BACKUP_MISSING')
    else:
        latest = max(complete, key=lambda r: utc(r['snapshot_at']))
        age = now - utc(latest['snapshot_at'])
        if age < timedelta(0):
            raise BackupError('future_timestamp')
        if age >= timedelta(hours=stale_hours):
            codes.append('BACKUP_STALE')
    if records and max(records, key=lambda r: utc(r['started_at']))['status'] != 'COMPLETE':
        codes.append('BACKUP_INCOMPLETE')
    return [event(code) for code in codes]

def retention_plan(records):
    """Seven complete daily copies + all pre-release; planning ONLY, no DELETE."""
    daily = sorted((r for r in records if r['kind'] == 'daily' and r['status'] == 'COMPLETE'),
                   key=lambda r: utc(r['snapshot_at']), reverse=True)
    keep = {r['id'] for r in daily[:7]} | {r['id'] for r in records if r['kind'] == 'pre-release'}
    proposed = [r['id'] for r in daily[7:]]
    return {'keep': sorted(keep), 'proposed_manual_review': proposed, 'automatic_deletion': False}

def configured_run(config_path, kind):
    """Deployment adapter is operator-approved code, never constructed from .env."""
    import importlib.util
    config = json.loads(Path(config_path).read_text(encoding='utf-8'))
    gates = [config.get('execution_enabled') is True,
             config.get('approval', {}).get('infrastructure_approved') is True,
             config.get('destination', {}).get('private_access_verified') is True,
             config.get('credentials', {}).get('least_privilege_verified') is True,
             config.get('recovery_secrets', {}).get('independent_recovery_verified') is True,
             kind != 'daily' or config.get('scheduler_enabled') is True]
    if not all(gates):
        raise BackupError('configuration_not_approved')
    adapter = config.get('operational_adapter', {})
    path = Path(adapter.get('path') or '')
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise BackupError('adapter_not_approved')
    if hashlib.sha256(path.read_bytes()).hexdigest() != adapter.get('sha256'):
        raise BackupError('adapter_not_approved')
    spec = importlib.util.spec_from_file_location('approved_backup_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Adapter owns approved maintenance/quiescence, pg_dump, storage snapshot,
    # TLS transport and key-store access. None are inferred from a boolean.
    state = config.get('state_directory')
    if not state or not Path(state).is_absolute():
        raise BackupError('state_not_configured')
    return run_job(state, kind, module.collect_quiesced_snapshot,
                   module.put_encrypted, module.get_encrypted,
                   module.recover_backup_key(), module.notify_operator)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run','health','retention'])
    parser.add_argument('--state')
    parser.add_argument('--config')
    parser.add_argument('--kind', choices=['daily','pre-release'], default='daily')
    args = parser.parse_args()
    try:
        if args.action == 'run':
            if not args.config:
                raise BackupError('config_missing')
            result = configured_run(args.config, args.kind)
            print(json.dumps(result))
            return 0 if result['status'] == 'COMPLETE' else 1
        if not args.state or not Path(args.state).is_dir():
            raise BackupError('state_missing')
        records = [json.loads(p.read_text(encoding='utf-8')) for p in Path(args.state).glob('*.json')]
        result = health(records, datetime.now(timezone.utc)) if args.action == 'health' else retention_plan(records)
        print(json.dumps(result))
        return 1 if args.action == 'health' and result else 0
    except Exception:
        print(json.dumps(event('BACKUP_FAILED')))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
