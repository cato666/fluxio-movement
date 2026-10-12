"""Streaming S16 archive format v2; v1 restore compatibility is retained."""
import hashlib,json,os,struct,tarfile
from pathlib import Path,PurePosixPath
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
import pilot_backup_ops as legacy

MAGIC=b'FXS16GCM2'
CHUNK=1024*1024
class BundleError(Exception):pass

def sha(path):
 digest=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for chunk in iter(lambda:stream.read(CHUNK),b''):digest.update(chunk)
 return digest.hexdigest()

def seal(plain,target,key,metadata):
 if len(key)!=32:raise BundleError('key_invalid')
 meta=json.dumps(metadata,sort_keys=True,separators=(',',':')).encode()
 if len(meta)>4096:raise BundleError('header_invalid')
 nonce=os.urandom(12);header=MAGIC+struct.pack('>I',len(meta))+meta+nonce
 cipher=Cipher(algorithms.AES(key),modes.GCM(nonce)).encryptor();cipher.authenticate_additional_data(header)
 with Path(plain).open('rb') as source,Path(target).open('xb') as out:
  os.chmod(target,0o600);out.write(header)
  for chunk in iter(lambda:source.read(CHUNK),b''):out.write(cipher.update(chunk))
  out.write(cipher.finalize());out.write(cipher.tag);out.flush();os.fsync(out.fileno())
 return sha(target)

def unseal(source,target,key,key_id,max_bytes):
 source=Path(source)
 if len(key)!=32 or source.stat().st_size>max_bytes+8192:raise BundleError('key_or_size_invalid')
 with source.open('rb') as stream:
  if stream.read(9)!=MAGIC:raise BundleError('format_invalid')
  size=struct.unpack('>I',stream.read(4))[0]
  if not 1<=size<=4096:raise BundleError('header_invalid')
  data=stream.read(size);meta=json.loads(data);nonce=stream.read(12)
  if meta.get('key_id')!=key_id or meta.get('format')!='FXS16GCM2' or meta.get('cipher')!='AES-256-GCM':raise BundleError('key_id_mismatch')
  header=MAGIC+struct.pack('>I',size)+data+nonce
  start=stream.tell();length=source.stat().st_size-start-16
  if length<0 or length>max_bytes:raise BundleError('size_invalid')
  stream.seek(-16,2);tag=stream.read(16);stream.seek(start)
  cipher=Cipher(algorithms.AES(key),modes.GCM(nonce,tag)).decryptor();cipher.authenticate_additional_data(header)
  with Path(target).open('xb') as out:
   os.chmod(target,0o600)
   while length:
    chunk=stream.read(min(CHUNK,length))
    if not chunk:raise BundleError('truncated')
    length-=len(chunk);out.write(cipher.update(chunk))
   out.write(cipher.finalize());out.flush();os.fsync(out.fileno())
 return meta

def verify_archive(plain,max_bytes):
 seen=set();members={};total=0;directories=set()
 with tarfile.open(plain,'r:') as archive:
  for info in archive:
   name=PurePosixPath(info.name);canonical=name.as_posix()
   if name.is_absolute() or '..' in name.parts or '\\' in info.name or ':' in info.name or canonical in seen or not(info.isdir() or info.isfile()):raise BundleError('unsafe_archive')
   seen.add(canonical)
   if info.isdir():
    if canonical=='storage':continue
    if not canonical.startswith('storage/'):raise BundleError('unknown_directory')
    directories.add(canonical[len('storage/'):]);continue
   if not(canonical in ('postgres.dump','manifest.json') or canonical.startswith('storage/')):raise BundleError('unknown_member')
   total+=info.size
   if total>max_bytes:raise BundleError('size_invalid')
   digest=hashlib.sha256();stream=archive.extractfile(info)
   if canonical=='manifest.json':
    if info.size>8*1024*1024:raise BundleError('manifest_too_large')
    manifest=json.loads(stream.read())
   else:
    for chunk in iter(lambda:stream.read(CHUNK),b''):digest.update(chunk)
    members[canonical]={'bytes':info.size,'sha256':digest.hexdigest()}
 if 'manifest' not in locals() or members!=manifest.get('files') or 'postgres.dump' not in members:raise BundleError('integrity_failed')
 if directories!=set(manifest.get('storage_directories',[])) or not legacy.REQUIRED.issubset(directories):raise BundleError('storage_incomplete')
 return manifest

def extract_entries(archive,destination):
 """Python 3.11-compatible extraction with explicit validation; no tar.extractall."""
 destination=Path(destination);seen=set()
 for info in archive:
  name=PurePosixPath(info.name);canonical=name.as_posix()
  if name.is_absolute() or '..' in name.parts or '\\' in info.name or ':' in info.name or canonical in seen or not(info.isdir() or info.isfile()):raise BundleError('unsafe_archive')
  seen.add(canonical);target=destination/name
  if info.isdir():target.mkdir(parents=True,exist_ok=True,mode=0o700);continue
  if canonical=='.':raise BundleError('unsafe_archive')
  target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
  with target.open('xb') as stream:
   os.chmod(target,0o600);source=archive.extractfile(info)
   for chunk in iter(lambda:source.read(CHUNK),b''):stream.write(chunk)

def unpack_verified(plain,destination,max_bytes):
 manifest=verify_archive(plain,max_bytes);destination=Path(destination)
 if destination.exists():raise BundleError('restore_target_exists')
 destination.mkdir(mode=0o700)
 with tarfile.open(plain,'r:') as archive:extract_entries(archive,destination)
 return manifest
