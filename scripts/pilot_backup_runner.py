"""Independent S16 Backup Runner. No Docker socket, EasyPanel API or providers."""
import argparse,hashlib,hmac,json,os,re,shutil,signal,subprocess,tarfile,tempfile,time,urllib.request,urllib.error,urllib.parse
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime,timezone,timedelta
from uuid import uuid4
import psycopg
import pilot_backup_ops as ops
import pilot_backup_bundle as bundle
import pilot_telegram_alerts as telegram
from pilot_resend_alerts import NoRedirect
try:
 from media_protocol import GC_LOCK, PROTOCOL, REFERENCE_COLUMNS, reference_path
except ImportError:
 from app.media_protocol import GC_LOCK, PROTOCOL, REFERENCE_COLUMNS, reference_path

class RunnerError(Exception):pass

def now():return datetime.now(timezone.utc)

def config(env):
 mode=env.get('BACKUP_CAPTURE_MODE','offline')
 if mode not in ('offline','online_v1'):raise RunnerError('capture_mode_invalid')
 if mode=='online_v1' and (env.get('BACKUP_MEDIA_PROTOCOL')!=PROTOCOL or env.get('BACKUP_ONLINE_WRITERS_VERIFIED')!='true' or not Path(env.get('BACKUP_APPLICATION_STORAGE_PATH','')).is_absolute()):raise RunnerError('online_protocol_not_verified')
 required=['BACKUP_STATE_PATH','BACKUP_WORK_PATH','STORAGE_PATH','BACKUP_AES_KEY_FILE','BACKUP_AES_KEY_ID','BACKUP_PG_SERVICE','PGSERVICEFILE','PGPASSFILE','BACKUP_SOURCE_COMMIT','R2_ENDPOINT','R2_BUCKET','R2_ACCESS_KEY_ID','R2_SECRET_ACCESS_KEY']
 if mode=='offline':required.append('BACKUP_QUIESCENCE_FILE')
 if env.get('BACKUP_RUNNER_ENABLED','').lower()!='true':raise RunnerError('runner_disabled')
 if any(not env.get(n) for n in required):raise RunnerError('secrets_or_config_missing')
 if not re.fullmatch('[a-f0-9]{40}',env['BACKUP_SOURCE_COMMIT']) or not re.fullmatch('[A-Za-z0-9_-]{1,100}',env['BACKUP_AES_KEY_ID']) or not re.fullmatch('[A-Za-z0-9_-]{1,64}',env['BACKUP_PG_SERVICE']):raise RunnerError('config_invalid')
 c=dict(env);c['max_bytes']=int(env.get('BACKUP_MAX_SET_BYTES',str(512*1024**2)));c['timeout']=int(env.get('BACKUP_COMMAND_TIMEOUT_SECONDS','600'))
 if not 1024<=c['max_bytes']<=4*1024**3 or not 1<=c['timeout']<=3600:raise RunnerError('limits_invalid')
 for name in ['BACKUP_STATE_PATH','BACKUP_WORK_PATH','STORAGE_PATH']:
  p=Path(c[name])
  if not p.is_absolute() or p.is_symlink() or not p.is_dir():raise RunnerError('mount_invalid')
 source=Path(c['STORAGE_PATH']).resolve()
 for name in ['BACKUP_STATE_PATH','BACKUP_WORK_PATH','BACKUP_AES_KEY_FILE']:
  p=Path(c[name]).resolve()
  if p==source or p.is_relative_to(source):raise RunnerError('mount_overlap')
 for name in ['BACKUP_AES_KEY_FILE','PGSERVICEFILE','PGPASSFILE']:
  p=Path(c[name])
  if p.is_symlink() or not p.is_file():raise RunnerError('secret_file_missing')
  if os.name=='posix' and p.stat().st_mode&0o077:raise RunnerError('secret_file_permissions')
 return c

def window(c):
 p=Path(c['BACKUP_QUIESCENCE_FILE'])
 if p.is_symlink() or not p.is_file():raise RunnerError('maintenance_required')
 w=json.loads(p.read_text(encoding='utf-8'));issued=ops.utc(w['issued_at']);expires=ops.utc(w['expires_at']);clock=now()
 if w.get('writers_paused') is not True or w.get('scope')!='all-db-and-storage-writers' or w.get('source_commit')!=c['BACKUP_SOURCE_COMMIT'] or w.get('storage_path')!=c['STORAGE_PATH'] or not issued<=clock<expires or expires-issued>timedelta(minutes=30):raise RunnerError('maintenance_invalid')
 return w

def inventory(root,max_bytes):
 root=Path(root);files={};dirs=[];size=0
 if any(not(root/n).is_dir() or (root/n).is_symlink() for n in ops.REQUIRED):raise RunnerError('storage_incomplete')
 for path in sorted(root.rglob('*')):
  if path.is_symlink():raise RunnerError('storage_symlink')
  relative=path.relative_to(root).as_posix()
  if path.is_dir():dirs.append(relative);continue
  if not path.is_file():raise RunnerError('storage_special_file')
  size+=path.stat().st_size
  if size>max_bytes or len(files)>=100000:raise RunnerError('size_limit')
  files[relative]={'bytes':path.stat().st_size,'sha256':bundle.sha(path)}
 return files,dirs

def clients(conn):
 return conn.execute("select count(*) from pg_stat_activity where datname=current_database() and pid<>pg_backend_pid() and backend_type='client backend'").fetchone()[0]

@contextmanager
def snapshot(c):
 # Read-only role, exported repeatable-read snapshot; no table locks requiring writes.
 try:
  conn=psycopg.connect('service='+c['BACKUP_PG_SERVICE'],application_name='fluxio-backup-guard',connect_timeout=10,autocommit=True)
  if c.get('BACKUP_CAPTURE_MODE')=='online_v1':
   if not conn.execute('SELECT pg_try_advisory_lock(%s)',(GC_LOCK+1,)).fetchone()[0]:raise RunnerError('backup_database_busy')
   if not conn.execute('SELECT pg_try_advisory_lock_shared(%s)',(GC_LOCK,)).fetchone()[0]:raise RunnerError('media_gc_busy')
  conn.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
  if c.get('BACKUP_CAPTURE_MODE')!='online_v1' and clients(conn):raise RunnerError('other_database_clients')
  unsafe=conn.execute("select rolsuper or rolcreatedb or rolcreaterole or rolreplication or rolbypassrls from pg_roles where rolname=current_user").fetchone()[0]
  if unsafe:raise RunnerError('backup_role_not_restricted')
  writable=conn.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema') and c.relkind in ('r','p') and (has_table_privilege(current_user,c.oid,'INSERT') or has_table_privilege(current_user,c.oid,'UPDATE') or has_table_privilege(current_user,c.oid,'DELETE') or has_table_privilege(current_user,c.oid,'TRUNCATE'))").fetchone()[0]
  if writable:raise RunnerError('backup_role_can_write')
  sid=conn.execute('select pg_export_snapshot()').fetchone()[0]
  head=conn.execute('select version_num from alembic_version').fetchone()[0]
  if c.get('BACKUP_CAPTURE_MODE')=='online_v1' and head!='0024_training_save_requests':raise RunnerError('online_schema_not_certified')
  yield conn,sid,head
 except RunnerError:raise
 except Exception:raise RunnerError('postgres_failed') from None
 finally:
  if 'conn' in locals():conn.close()

def reference_files(conn,application_root):
 paths=set()
 for table,columns in REFERENCE_COLUMNS.items():
  query_columns=columns+('status',) if table=='analyses' else columns
  for row in conn.execute('SELECT '+','.join(query_columns)+' FROM '+table):
   values=row[:len(columns)]
   if not values[0] and (table!='analyses' or row[-1]!='FAILED'):raise RunnerError('required_media_reference_empty')
   if table=='analyses' and row[-1]=='COMPLETED' and not values[1]:raise RunnerError('required_media_reference_empty')
   for value in values:
    try:path=reference_path(table,value,application_root)
    except (ValueError,TypeError):raise RunnerError('invalid_media_reference') from None
    if path:paths.add(path)
 if len(paths)>100000:raise RunnerError('size_limit')
 return sorted(paths)

def checked_source(root,relative):
 path=root/relative
 if any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):raise RunnerError('referenced_media_missing_or_unsafe')
 return path

def capture_online(c,work):
 with snapshot(c) as (conn,sid,head):
  stamp=now().isoformat()
  refs=reference_files(conn,c['BACKUP_APPLICATION_STORAGE_PATH'])
  root=Path(c['STORAGE_PATH']);dest=work/'storage';dest.mkdir(mode=0o700)
  for directory in ops.REQUIRED:(dest/directory).mkdir(mode=0o700)
  size=0
  for relative in refs:
   source=checked_source(root,relative);before={'bytes':source.stat().st_size,'sha256':bundle.sha(source)}
   size+=before['bytes']
   if size>c['max_bytes']:raise RunnerError('size_limit')
   target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True,mode=0o700);shutil.copyfile(source,target)
   if before!={'bytes':source.stat().st_size,'sha256':bundle.sha(source)} or before!={'bytes':target.stat().st_size,'sha256':bundle.sha(target)}:raise RunnerError('referenced_media_changed')
  dump=work/'postgres.dump'
  private_env=dict(os.environ);private_env.update(PGSERVICEFILE=c['PGSERVICEFILE'],PGPASSFILE=c['PGPASSFILE'],PGAPPNAME='fluxio-backup-dump',PGOPTIONS='-c default_transaction_read_only=on')
  result=subprocess.run(['pg_dump','--dbname=service='+c['BACKUP_PG_SERVICE'],'--snapshot='+sid,'--format=custom','--no-owner','--no-acl','--lock-wait-timeout=5000','--file='+str(dump)],env=private_env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=c['timeout'])
  if result.returncode:raise RunnerError('pg_dump_failed')
  # Recheck every pinned generation after dump; root growth is deliberately allowed.
  for relative in refs:
   source=checked_source(root,relative)
   if source.stat().st_size!=(dest/relative).stat().st_size or bundle.sha(source)!=bundle.sha(dest/relative):raise RunnerError('referenced_media_changed')
  if dump.stat().st_size+size>c['max_bytes']:raise RunnerError('size_limit')
  with dump.open('rb') as stream:
   if stream.read(5)!=b'PGDMP':raise RunnerError('dump_invalid')
  c['_snapshot_references']=refs
  return dump,dest,head,stamp

def capture(c,work):
 if c.get('BACKUP_CAPTURE_MODE')=='online_v1':return capture_online(c,work)
 window(c)
 with snapshot(c) as (conn,sid,head):
  before,dirs=inventory(c['STORAGE_PATH'],c['max_bytes']);dest=work/'storage';dest.mkdir(mode=0o700)
  for n in dirs:(dest/n).mkdir(parents=True,exist_ok=True,mode=0o700)
  for n in before:shutil.copyfile(Path(c['STORAGE_PATH'])/n,dest/n)
  dump=work/'postgres.dump'
  command=['pg_dump','--dbname=service='+c['BACKUP_PG_SERVICE'],'--snapshot='+sid,'--format=custom','--no-owner','--no-acl','--lock-wait-timeout=5000','--file='+str(dump)]
  private_env=dict(os.environ);private_env.update(PGSERVICEFILE=c['PGSERVICEFILE'],PGPASSFILE=c['PGPASSFILE'],PGAPPNAME='fluxio-backup-dump',PGOPTIONS='-c default_transaction_read_only=on')
  result=subprocess.run(command,env=private_env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=c['timeout'])
  if result.returncode:raise RunnerError('pg_dump_failed')
  conn.execute('select pg_stat_clear_snapshot()')
  if clients(conn):raise RunnerError('writers_reconnected')
  after,newdirs=inventory(c['STORAGE_PATH'],c['max_bytes']);copied,_=inventory(dest,c['max_bytes'])
  if before!=after or before!=copied or dirs!=newdirs:raise RunnerError('storage_changed')
  window(c) # Capture must finish while ALL writers remain paused externally.
  if dump.stat().st_size+sum(v['bytes'] for v in before.values())>c['max_bytes']:raise RunnerError('size_limit')
  with dump.open('rb') as stream:
   if stream.read(5)!=b'PGDMP':raise RunnerError('dump_invalid')
  return dump,dest,head,now().isoformat()

class R2:
 def __init__(self,c):
  self.c=c;url=urllib.parse.urlsplit(c['R2_ENDPOINT']);self.host=url.hostname
  if url.scheme!='https' or url.username or url.password or url.query or url.fragment or url.path not in ('','/') or url.port not in (None,443) or not re.fullmatch('[a-f0-9]{32}\\.r2\\.cloudflarestorage\\.com',self.host or '') or c['R2_BUCKET']!='fluxio-movement-backups':raise RunnerError('r2_destination_invalid')
 def request(self,method,name,file=None):
  path='/fluxio-movement-backups/'+urllib.parse.quote(name,safe='/');stamp=now().strftime('%Y%m%dT%H%M%SZ');day=stamp[:8];region=self.c.get('R2_REGION','auto');scope=f'{day}/{region}/s3/aws4_request';digest=bundle.sha(file) if file else hashlib.sha256(b'').hexdigest();signed='host;x-amz-content-sha256;x-amz-date';headers=f'host:{self.host}\nx-amz-content-sha256:{digest}\nx-amz-date:{stamp}\n';canonical='\n'.join([method,path,'',headers,signed,digest]);msg='AWS4-HMAC-SHA256\n'+stamp+'\n'+scope+'\n'+hashlib.sha256(canonical.encode()).hexdigest();key=('AWS4'+self.c['R2_SECRET_ACCESS_KEY']).encode()
  for item in [day,region,'s3','aws4_request']:key=hmac.new(key,item.encode(),hashlib.sha256).digest()
  signature=hmac.new(key,msg.encode(),hashlib.sha256).hexdigest();h={'Authorization':f"AWS4-HMAC-SHA256 Credential={self.c['R2_ACCESS_KEY_ID']}/{scope}, SignedHeaders={signed}, Signature={signature}",'x-amz-date':stamp,'x-amz-content-sha256':digest}
  def chunks():
   with Path(file).open('rb') as stream:
    for chunk in iter(lambda:stream.read(bundle.CHUNK),b''):yield chunk
  if file:h['Content-Length']=str(Path(file).stat().st_size)
  req=urllib.request.Request('https://'+self.host+path,data=chunks() if file else None,method=method,headers=h)
  return urllib.request.build_opener(NoRedirect).open(req,timeout=60)
 def put(self,name,file):
  with self.request('PUT',name,file) as response:
   if response.status not in (200,201,204):raise RunnerError('r2_put_failed')
 def get(self,name,target):
  with self.request('GET',name) as response,Path(target).open('xb') as out:
   os.chmod(target,0o600);total=0
   for chunk in iter(lambda:response.read(bundle.CHUNK),b''):
    total+=len(chunk)
    if total>self.c['max_bytes']+8192:raise RunnerError('r2_size_limit')
    out.write(chunk)

def notify(c,event):
 return telegram.notifier(c['BACKUP_STATE_PATH'],env=c,authorized=c.get('BACKUP_RUNNER_ENABLED','').lower()=='true')(event)

def acquire_lock(path):
 path=Path(path)
 if path.is_symlink() or path.is_dir():raise RunnerError('unsafe_lock')
 stream=path.open('a+b');os.chmod(path,0o600)
 try:
  if os.name=='nt':
   import msvcrt
   if path.stat().st_size==0:stream.write(b'0');stream.flush()
   stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
  else:
   import fcntl
   fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  return stream
 except (BlockingIOError,OSError):stream.close();return None

def release_lock(stream):
 if os.name=='nt':
  import msvcrt
  stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
 else:
  import fcntl
  fcntl.flock(stream.fileno(),fcntl.LOCK_UN)
 stream.close()

def backup(env,kind,store=None,collector=capture,notification=notify):
 c=None;record=None;lock=None
 try:
  c=config(env)
  if kind not in ('daily','pre-release'):raise RunnerError('kind_invalid')
  state=Path(c['BACKUP_STATE_PATH']);lock=acquire_lock(state/'runner.lock')
  if lock is None:return {'status':'BLOCKED','code':'BACKUP_BUSY'}
  bid=uuid4().hex;record={'id':bid,'kind':kind,'status':'INCOMPLETE','started_at':now().isoformat(),'key_id':c['BACKUP_AES_KEY_ID'],'source_commit':c['BACKUP_SOURCE_COMMIT']};receipt=state/(bid+'.json');ops.receipt(receipt,record)
  key=Path(c['BACKUP_AES_KEY_FILE']).read_bytes()
  if len(key)!=32:raise RunnerError('key_invalid')
  with tempfile.TemporaryDirectory(prefix='owned-backup-',dir=c['BACKUP_WORK_PATH']) as directory:
   work=Path(directory);dump,storage,head,stamp=collector(c,work)
   meta={'format':'FXS16GCM2','cipher':'AES-256-GCM','key_id':c['BACKUP_AES_KEY_ID'],'backup_id':bid,'kind':kind,'snapshot_at':stamp,'alembic_head':head,'source_commit':c['BACKUP_SOURCE_COMMIT']}
   files,dirs=inventory(storage,c['max_bytes']);entries={'postgres.dump':{'bytes':dump.stat().st_size,'sha256':bundle.sha(dump)}}
   entries.update({'storage/'+name:value for name,value in files.items()});manifest={**meta,'files':entries,'storage_directories':dirs}
   mfile=work/'manifest.json'
   if c.get('BACKUP_CAPTURE_MODE')=='online_v1':manifest.update(media_protocol=PROTOCOL,application_storage_path=c['BACKUP_APPLICATION_STORAGE_PATH'],snapshot_references=c['_snapshot_references'])
   data=json.dumps(manifest,sort_keys=True).encode()
   if len(data)>8*1024*1024:raise RunnerError('manifest_too_large')
   mfile.write_bytes(data);plain=work/'bundle.tar'
   projected=dump.stat().st_size+sum(v['bytes'] for v in files.values())+len(data)+1024*(len(files)+len(dirs)+20)
   if shutil.disk_usage(work).free < 4*projected+16*1024**2:raise RunnerError('staging_capacity_insufficient')
   with tarfile.open(plain,'w') as archive:
    archive.add(dump,arcname='postgres.dump');archive.add(storage,arcname='storage');archive.add(mfile,arcname='manifest.json')
   if plain.stat().st_size>c['max_bytes']:raise RunnerError('size_limit')
   bundle.verify_archive(plain,c['max_bytes']);cipher=work/'bundle.fxb2';digest=bundle.seal(plain,cipher,key,meta)
   remote=store or R2(c);object_name='backups/'+kind+'/'+bid+'.fxb2';record.update(object_name=object_name,encrypted_sha256=digest,encrypted_bytes=cipher.stat().st_size);ops.receipt(receipt,record)
   remote.put(object_name,cipher);download=work/'download.fxb2';remote.get(object_name,download)
   if bundle.sha(download)!=digest:raise RunnerError('remote_integrity_failed')
   recovered=work/'verified.tar';authenticated=bundle.unseal(download,recovered,key,c['BACKUP_AES_KEY_ID'],c['max_bytes']);verified=bundle.verify_archive(recovered,c['max_bytes'])
   if authenticated!=meta or verified!=manifest:raise RunnerError('manifest_mismatch')
   record.update(status='COMPLETE',snapshot_at=stamp,verified_at=now().isoformat(),alembic_head=head)
   ops.receipt(receipt,record)
  return record
 except Exception as error:
  code=str(error) if isinstance(error,RunnerError) else 'backup_failed'
  if code=='runner_disabled':return {'status':'DISABLED','code':code}
  # Validation errors may occur before config is ready; still try fixed-code alert.
  context=c or dict(env)
  if record:
   record.update(status='INCOMPLETE',error_code=code);ops.receipt(Path(context['BACKUP_STATE_PATH'])/(record['id']+'.json'),record)
  try:sent=notification(context,{'code':'BACKUP_FAILED','backup_id':record['id'] if record else None,'request_id':uuid4().hex}) is True
  except Exception:sent=False
  if record:
   record['alert_delivery']='ACKNOWLEDGED' if sent else 'FAILED';ops.receipt(Path(context['BACKUP_STATE_PATH'])/(record['id']+'.json'),record)
   return record
  return {'status':'BLOCKED','error_code':code,'alert_delivery':'ACKNOWLEDGED' if sent else 'FAILED'}
 finally:
  if lock is not None:release_lock(lock)

def check_health(env):
 if env.get('BACKUP_RUNNER_ENABLED','').lower()!='true':return [{'code':'RUNNER_DISABLED'}]
 state=Path(env['BACKUP_STATE_PATH']);records=[json.loads(p.read_text()) for p in state.glob('*.json') if re.fullmatch('[a-f0-9]{32}\\.json',p.name)];events=ops.health(records,now(),float(env.get('BACKUP_STALE_HOURS','24')))
 # Crash before runner receipt creation still leaves a reserved schedule marker.
 for path in state.glob('schedule-*.json'):
  marker=json.loads(path.read_text())
  if marker.get('status')=='ATTEMPTED' and 'reserved_at' in marker and now()-ops.utc(marker['reserved_at'])>timedelta(minutes=5):
   if not any(e['code']=='BACKUP_INCOMPLETE' for e in events):events.append(ops.event('BACKUP_INCOMPLETE'))
 if any(e['code']=='BACKUP_INCOMPLETE' for e in events):
  probe=acquire_lock(state/'runner.lock')
  if probe is not None:release_lock(probe)
  elif records:
   latest=max(records,key=lambda r:ops.utc(r['started_at']))
   if now()-ops.utc(latest['started_at'])<timedelta(seconds=int(env.get('BACKUP_MAX_RUN_SECONDS','1800'))):events=[e for e in events if e['code']!='BACKUP_INCOMPLETE']
 active={e['code'] for e in events}
 for path in state.glob('health-BACKUP_*.json'):
  previous=json.loads(path.read_text())
  if previous.get('active') and previous['code'] not in active:
   previous['active']=False;previous['resolved_at']=now().isoformat();ops.receipt(path,previous)
 for event in events:
  path=state/('health-'+event['code']+'.json');previous=json.loads(path.read_text()) if path.is_file() else {}
  identifier=previous.get('request_id') if previous.get('active') else uuid4().hex
  event['request_id']=identifier
  delivered=notify(env,event)
  ops.receipt(path,{'code':event['code'],'active':True,'request_id':identifier,'checked_at':now().isoformat(),'alert_delivery':'ACKNOWLEDGED' if delivered else 'FAILED'})
 return events

def watch(env):
 while True:
  if env.get('BACKUP_RUNNER_ENABLED','').lower()=='true':
   try:check_health(env)
   except Exception:
    # Monitor failure remains visible; no raw exception and no recursive alerts.
    print(json.dumps({'status':'HEALTH_FAILED'}),flush=True)
  time.sleep(30)

def schedule(env):
 from zoneinfo import ZoneInfo
 daily_time=env.get('BACKUP_DAILY_TIME','03:00')
 if not re.fullmatch(r'([01][0-9]|2[0-3]):[0-5][0-9]',daily_time):raise RunnerError('schedule_invalid')
 while True:
  if env.get('BACKUP_RUNNER_ENABLED','').lower()=='true' and env.get('BACKUP_SCHEDULE_ENABLED','').lower()=='true':
   local=now().astimezone(ZoneInfo(env.get('BACKUP_SCHEDULE_TIMEZONE','America/Santiago')));state=Path(env['BACKUP_STATE_PATH']);marker=state/('schedule-'+local.date().isoformat()+'.json')
   if local.strftime('%H:%M')>=daily_time and not marker.exists():
    # Reserve calendar slot BEFORE job so a restart never duplicates a daily attempt.
    try:
     with marker.open('x') as stream:
      json.dump({'status':'ATTEMPTED','reserved_at':now().isoformat()},stream);stream.flush();os.fsync(stream.fileno())
     result=backup(env,'daily');ops.receipt(marker,{'status':result['status']})
    except FileExistsError:pass
   try:check_health(env)
   except Exception:print(json.dumps({'status':'HEALTH_FAILED'}),flush=True)
  time.sleep(30)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['run','health','retention','schedule','watch']);parser.add_argument('--kind',choices=['daily','pre-release'],default='daily');args=parser.parse_args()
 try:
  if args.action=='run':result=backup(dict(os.environ),args.kind);print(json.dumps(result));return 0 if result['status']=='COMPLETE' else 1
  if args.action=='health':result=check_health(dict(os.environ));print(json.dumps(result));return 1 if result else 0
  if args.action=='retention':
   records=[json.loads(p.read_text()) for p in Path(os.environ['BACKUP_STATE_PATH']).glob('*.json') if re.fullmatch('[a-f0-9]{32}\\.json',p.name)];print(json.dumps(ops.retention_plan(records)));return 0
  if args.action=='watch':watch(dict(os.environ))
  else:schedule(dict(os.environ))
  return 0
 except Exception:print(json.dumps({'status':'BLOCKED','code':'runner_failed'}));return 2

if __name__=='__main__':raise SystemExit(main())
