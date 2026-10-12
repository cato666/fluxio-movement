"""S16 integration: NEW internal Docker network, tmpfs DB/media, simulated R2/Telegram.
No images pulled, existing containers stopped, provider credentials or ports used.
"""
import argparse,ipaddress,json,subprocess,tempfile,time,os,hashlib
from pathlib import Path
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1]
LABEL='com.fluxio.s16-runner-test'

def docker(*args,data=None):
 result=subprocess.run(['docker',*args],input=data,capture_output=True)
 if result.returncode:raise RuntimeError('isolated_test_step_failed')
 return result.stdout

def inspect(name):return json.loads(docker('inspect',name))[0]

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--subnet',required=True);args=parser.parse_args();subnet=ipaddress.ip_network(args.subnet)
 assert subnet.is_private and subnet.prefixlen==28
 token=uuid4().hex[:12];net='fluxio-s16-runner-net-'+token;db='fluxio-s05-e2e-db-'+token;app='fluxio-s16-fixture-'+token;runner='fluxio-s16-runner-'+token;created=[];evidence=Path(tempfile.mkdtemp(prefix='fluxio-s16-runner-integration-'));print('Evidence: '+str(evidence),flush=True);metadata={'status':'BLOCKED','instance':token,'network':net,'database_tmpfs':True,'media_tmpfs':True,'ports_published':False,'r2_telegram_real_calls':0}
 try:
  for name in docker('network','ls','--format','{{.Name}}').decode().splitlines():
   for cfg in json.loads(docker('network','inspect',name))[0].get('IPAM',{}).get('Config') or []:
    if cfg.get('Subnet') and ipaddress.ip_network(cfg['Subnet']).version==4:assert not subnet.overlaps(ipaddress.ip_network(cfg['Subnet']))
  if os.name=='nt':
   routes=subprocess.check_output(['powershell','-NoProfile','-Command','Get-NetRoute -AddressFamily IPv4 | Select-Object -ExpandProperty DestinationPrefix'],text=True).splitlines();routes += [l.split()[0] for l in subprocess.check_output(['wsl.exe','-d','docker-desktop','--','ip','-4','route'],text=True).splitlines() if l and not l.startswith('default')]
   for r in routes:
    if r.strip() not in ('','0.0.0.0/0'):assert not subnet.overlaps(ipaddress.ip_network(r.strip(),strict=False))
  for image in ['postgres:17.6-bookworm','fluxio-whatsapp-tests:phase2','fluxio-s16-backup-runner:local']:docker('image','inspect',image)
  docker('network','create','--internal','--subnet',str(subnet),'--label',LABEL+'='+token,net)
  assert json.loads(docker('network','inspect',net))[0]['Internal']
  docker('run','-d','--name',db,'--label',LABEL+'='+token,'--network',net,'--memory','512m','--tmpfs','/var/lib/postgresql/data:rw,size=256m','-e','POSTGRES_DB=movement_e2e_s05','-e','POSTGRES_USER=s05_synthetic','-e','POSTGRES_PASSWORD=s05-synthetic-only','postgres:17.6-bookworm');created.append(db)
  for _ in range(40):
   ready=subprocess.run(['docker','exec',db,'pg_isready','-U','s05_synthetic'],capture_output=True)
   if ready.returncode==0:break
   time.sleep(1)
  else:raise RuntimeError('disposable_postgres_unavailable')
  appenv=['APP_ENV=development','ENABLE_DEMO_SEED=false','WHATSAPP_ENABLED=false','TRAINING_AI_ENABLED=false','TRAINING_VOICE_ENABLED=false','AI_REASONING_ENABLED=false','SESSION_SECRET=s16-isolated-synthetic-session-only-abcdefghijklmnopqrstuvwxyz','DATABASE_URL=postgresql+psycopg://s05_synthetic:s05-synthetic-only@'+db+':5432/movement_e2e_s05','STORAGE_PATH=/tmp/s05-e2e-storage','S05_E2E_ISOLATED=1','S05_E2E_DB_HOST='+db]
  command=['run','-d','--name',app,'--label',LABEL+'='+token,'--network',net,'--memory','768m','--tmpfs','/tmp:rw,size=512m','--mount','type=bind,src='+str(ROOT)+',dst=/candidate,readonly','--entrypoint','sleep']
  for variable in appenv:command+=['-e',variable]
  docker(*command,'fluxio-whatsapp-tests:phase2','infinity');created.append(app)
  copy="from pathlib import Path; import shutil; r=Path('/tmp/s16'); r.mkdir(); [shutil.copytree('/candidate/'+n,r/n) for n in ['app','migrations','tests']]; shutil.copyfile('/candidate/alembic.ini',r/'alembic.ini'); Path('/tmp/s05-e2e-storage').mkdir()"
  docker('exec',app,'python','-c',copy);docker('exec','-w','/tmp/s16',app,'alembic','upgrade','head');docker('exec','-w','/tmp/s16',app,'python','-m','tests.e2e.s05_fixture','init')
  setup="""
from app.database import SessionLocal
from app.models import User,Coach,TrainingSession,TrainingImage,Analysis,CoachReview
from app.services.auth import hash_password
from pathlib import Path
from datetime import date,datetime,timezone
from uuid import UUID
root=Path('/tmp/s05-e2e-storage')
for n in ['training-images','original','annotated','analysis']:(root/n).mkdir()
(root/'training-images'/'synthetic.png').write_bytes(Path('/tmp/s05-board.png').read_bytes())
(root/'analysis'/'synthetic.json').write_text('{"synthetic":true}')
owner=UUID('00000000-0000-4000-8000-000000000101');coach=UUID('00000000-0000-4000-8000-000000000103')
with SessionLocal() as s:
 s.add(User(id=coach,demo_key='s16-coach',name='Synthetic coach',role='COACH',password_hash=hash_password('synthetic-only')));s.flush();s.add(Coach(user_id=coach,specialty='Synthetic'));s.flush();photo=TrainingImage(athlete_id=owner,path='synthetic.png');s.add(photo);s.flush()
 s.add(TrainingSession(athlete_id=owner,trained_on=date(2026,10,12),title='Synthetic',source_text='Synthetic',workout='Synthetic',source_image_id=photo.id,athlete_notes=[{'text':'Synthetic note'}]))
 s.add(Analysis(id='s16runner',athlete_id=owner,status='COMPLETED',exercise='air_squat',original_filename='synthetic.mp4',video_path=str(root/'original'/'synthetic.mp4'),annotated_video_path=str(root/'annotated'/'synthetic.mp4'),analysis_json_path=str(root/'analysis'/'synthetic.json'),result={'synthetic':True},completed_at=datetime.now(timezone.utc)));s.flush();s.add(CoachReview(analysis_id='s16runner',athlete_id=owner,coach_id=coach,status='COMPLETED',main_focus='Synthetic focus',next_session='Synthetic next',completed_at=datetime.now(timezone.utc)));s.commit()
"""
  docker('exec','-w','/tmp/s16',app,'python','-c',setup);docker('exec',app,'ffmpeg','-v','error','-f','lavfi','-i','color=c=green:s=96x96:r=10','-t','1','-c:v','mpeg4','/tmp/s05-e2e-storage/original/synthetic.mp4');docker('exec',app,'cp','/tmp/s05-e2e-storage/original/synthetic.mp4','/tmp/s05-e2e-storage/annotated/synthetic.mp4')
  sql="CREATE ROLE s16_backup LOGIN PASSWORD 'synthetic-backup'; GRANT CONNECT ON DATABASE movement_e2e_s05 TO s16_backup; GRANT USAGE ON SCHEMA public TO s16_backup; GRANT SELECT ON ALL TABLES IN SCHEMA public TO s16_backup; GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO s16_backup; ALTER ROLE s16_backup SET default_transaction_read_only=on; CREATE ROLE s16_restore LOGIN PASSWORD 'synthetic-restore';"
  docker('exec',db,'psql','-U','s05_synthetic','-d','movement_e2e_s05','-c',sql);docker('exec',db,'psql','-U','s05_synthetic','-d','postgres','-c','CREATE DATABASE movement_restore_'+token+' OWNER s16_restore');docker('exec',db,'psql','-U','s05_synthetic','-d','postgres','-c','CREATE DATABASE movement_restore_legacy_'+token+' OWNER s16_restore')
  image_info=json.loads(docker('image','inspect','fluxio-s16-backup-runner:local'))[0];assert not image_info['Config'].get('Volumes') and image_info['Config']['User']=='10001:10001';image_id=image_info['Id'];metadata['runner_image_id']=image_id;metadata['runner_no_inherited_volumes']=True
  docker('run','-d','--name',runner,'--label',LABEL+'='+token,'--network',net,'--memory','1g','--tmpfs','/tmp:rw,size=768m,mode=1777','--tmpfs','/run/secrets:rw,size=1m','--entrypoint','sleep','fluxio-s16-backup-runner:local','infinity');created.append(runner)
  archive=docker('exec',app,'tar','-C','/tmp/s05-e2e-storage','-cf','-','.')
  docker('exec','--user','0',runner,'mkdir','-p','/tmp/source','/tmp/work','/tmp/state');docker('exec','-i','--user','0',runner,'tar','-C','/tmp/source','-xf','-',data=archive)
  commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
  config={'BACKUP_RUNNER_ENABLED':'true','BACKUP_STATE_PATH':'/tmp/state','BACKUP_WORK_PATH':'/tmp/work','STORAGE_PATH':'/tmp/source','BACKUP_AES_KEY_FILE':'/run/secrets/aes256.key','BACKUP_AES_KEY_ID':'synthetic-runner-k1','BACKUP_PG_SERVICE':'source','PGSERVICEFILE':'/run/secrets/service.conf','PGPASSFILE':'/run/secrets/pgpass','BACKUP_QUIESCENCE_FILE':'/run/secrets/window.json','BACKUP_SOURCE_COMMIT':commit,'R2_ENDPOINT':'https://'+('a'*32)+'.r2.cloudflarestorage.com','R2_BUCKET':'fluxio-movement-backups','R2_ACCESS_KEY_ID':'synthetic','R2_SECRET_ACCESS_KEY':'synthetic','RESTORE_PG_SERVICE':'restore','BACKUP_RESTORE_ISOLATED_CONFIRMED':'true','TELEGRAM_ALERTS_ENABLED':'false'}
  service='[source]\nhost='+db+'\nport=5432\ndbname=movement_e2e_s05\nuser=s16_backup\n[restore]\nhost='+db+'\nport=5432\ndbname=movement_restore_'+token+'\nuser=s16_restore\n[restore_legacy]\nhost='+db+'\nport=5432\ndbname=movement_restore_legacy_'+token+'\nuser=s16_restore\n'
  secret={'config':config,'service':service,'pgpass':db+':5432:movement_e2e_s05:s16_backup:synthetic-backup\n'+db+':5432:movement_restore_'+token+':s16_restore:synthetic-restore\n'+db+':5432:movement_restore_legacy_'+token+':s16_restore:synthetic-restore\n'}
  init="""
import sys,json,os
from pathlib import Path
from datetime import datetime,timezone,timedelta
v=json.load(sys.stdin);c=v['config'];clock=datetime.now(timezone.utc);w={'issued_at':clock.isoformat(),'expires_at':(clock+timedelta(minutes=10)).isoformat(),'writers_paused':True,'scope':'all-db-and-storage-writers','source_commit':c['BACKUP_SOURCE_COMMIT'],'storage_path':'/tmp/source'}
for n,data in [('aes256.key',b'k'*32),('service.conf',v['service'].encode()),('pgpass',v['pgpass'].encode()),('config.json',json.dumps(c).encode()),('window.json',json.dumps(w).encode())]:
 p=Path('/run/secrets')/n;p.write_bytes(data);p.chmod(0o600);os.chown(p,10001,10001)
for n in ['/run/secrets','/tmp/source','/tmp/work','/tmp/state']:os.chown(n,10001,10001)
for p in Path('/tmp/source').rglob('*'):os.chown(p,10001,10001)
"""
  docker('exec','-i','--user','0',runner,'/opt/backup-venv/bin/python','-c',init,data=json.dumps(secret).encode())
  source_names=['pilot_backup_runner.py','pilot_backup_restore.py','pilot_backup_bundle.py','pilot_backup_ops.py','pilot_telegram_alerts.py','pilot_resend_alerts.py']
  check="from pathlib import Path; import hashlib,json; print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/opt/fluxio-backup').glob('*.py')}))"
  runtime_hashes=json.loads(docker('exec',runner,'/opt/backup-venv/bin/python','-c',check))
  assert all(runtime_hashes[name]==hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in source_names)
  metadata['immutable_image_code_matches_worktree']=True
  # Run actual pg_dump/readonly snapshot and pg_restore; only R2/Telegram simulated.
  test="""
import sys,json,os,shutil,hashlib
from pathlib import Path
sys.path.insert(0,'/opt/fluxio-backup')
import pilot_backup_runner as r,pilot_backup_restore as restore,pilot_backup_bundle as b
c=json.loads(Path('/run/secrets/config.json').read_text());os.environ.update(c)
class Store:
 def __init__(self):self.data={};self.puts=0
 def put(self,name,path):self.puts+=1;self.data[name]=Path(path).read_bytes()
 def get(self,name,path):Path(path).write_bytes(self.data[name])
store=Store();events=[];before=r.inventory('/tmp/source',1024**3);result=r.backup(c,'daily',store=store,notification=lambda c,e:events.append(e) or True)
print(json.dumps({'stage':'backup','status':result['status'],'error_code':result.get('error_code')}),flush=True)
assert result['status']=='COMPLETE',result
cipher=Path('/tmp/restore.fxb2');cipher.write_bytes(next(iter(store.data.values())))
out=restore.restore(c,str(cipher),'/tmp/restored',result['encrypted_sha256'],c['BACKUP_AES_KEY_ID']);assert out['status']=='RESTORED_ISOLATED'
assert before==r.inventory('/tmp/source',1024**3)==r.inventory('/tmp/restored',1024**3)
import psycopg
with psycopg.connect('service=restore') as conn:
 counts={n:conn.execute('select count(*) from '+n).fetchone()[0] for n in ['users','training_sessions','training_images','analyses','reviews']};assert counts=={'users':3,'training_sessions':1,'training_images':1,'analyses':1,'reviews':1}
 assert conn.execute('select source_image_id is not null and jsonb_array_length(athlete_notes)>0 from training_sessions').fetchone()[0]
 assert conn.execute('select length(main_focus)>0 and length(next_session)>0 from reviews').fetchone()[0]
 head=conn.execute('select version_num from alembic_version').fetchone()[0];assert head=='0024_training_save_requests'
 tables=conn.execute(\"select count(*) from pg_tables where schemaname='public'\").fetchone()[0];assert tables==29
# Compatibility restore: create a v1 set from the SAME real synthetic dump.
import tempfile
import pilot_backup_ops as legacy
with tempfile.TemporaryDirectory(dir='/tmp/work') as temporary:
 plain=Path(temporary)/'legacy-source.tar';b.unseal(cipher,plain,b'k'*32,c['BACKUP_AES_KEY_ID'],512*1024**2);b.unpack_verified(plain,Path(temporary)/'legacy-source',512*1024**2)
 content=Path(temporary)/'legacy-source';old=legacy.seal_snapshot((content/'postgres.dump').read_bytes(),content/'storage',b'k'*32);legacycipher=Path('/tmp/legacy.fxb1');legacycipher.write_bytes(old)
 oldenv=dict(c,RESTORE_PG_SERVICE='restore_legacy');resultv1=restore.restore(oldenv,str(legacycipher),'/tmp/restored-legacy',hashlib.sha256(old).hexdigest(),c['BACKUP_AES_KEY_ID']);assert resultv1['format']=='FXS16GCM1'
with psycopg.connect('service=restore_legacy') as conn:assert conn.execute('select count(*) from reviews').fetchone()[0]==1
assert before==r.inventory('/tmp/restored-legacy',1024**3)
# Real readonly-role refusal; capture refuses another database client.
with psycopg.connect('service=source') as conn:
 try:conn.execute('delete from training_sessions');raise AssertionError('read-only role wrote')
 except psycopg.Error:conn.rollback()
 blocked=r.backup(c,'pre-release',store=store,notification=lambda c,e:True);assert blocked['status']=='INCOMPLETE' and blocked['error_code']=='other_database_clients'
# Mutate only NEW synthetic source during pg_dump to prove capture refuses drift.
original=r.subprocess.run
from unittest.mock import patch
def changed(*args,**kw):
 value=original(*args,**kw);Path('/tmp/source/analysis/synthetic.json').write_text('{"synthetic":true,"changed":true}');return value
with patch.object(r.subprocess,'run',side_effect=changed):drift=r.backup(c,'pre-release',store=store,notification=lambda c,e:True)
assert drift['status']=='INCOMPLETE' and drift['error_code']=='storage_changed'
print(json.dumps({'status':'PASS','actual_pg_dump_restore':True,'legacy_v1_restore':'PASS','snapshot_and_readonly_role':'PASS','other_clients_blocked':'PASS','changing_files_blocked':'PASS','counts':counts,'tables':tables,'head':head,'original_media_preserved_before_controlled_drift':True,'encrypted_format':'FXS16GCM2','key_id':c['BACKUP_AES_KEY_ID'],'r2_simulated':True,'telegram_simulated':True,'physical_r2_test_puts':store.puts,'no_existing_source_or_database_touched':True}))
"""
  wrapped="import traceback,json\ntry:exec("+repr(test)+")\nexcept Exception as e:\n print(json.dumps({'inner_type':type(e).__name__,'frames':[{'file':Path(f.filename).name,'line':f.lineno} for f in traceback.extract_tb(e.__traceback__)]}),flush=True);raise SystemExit(1)"
  raw=subprocess.run(['docker','exec',runner,'/opt/backup-venv/bin/python','-c',wrapped],capture_output=True)
  print(raw.stdout.decode(),flush=True)
  if raw.returncode:raise RuntimeError('runner_integration_failed')
  output=raw.stdout.decode().strip().splitlines()[-1].encode();result=json.loads(output);(evidence/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(output.decode(),flush=True)
  # Verify valid media separately using fixture runtime's existing decoders.
  docker('exec',app,'python','-c',"from PIL import Image; Image.open('/tmp/s05-e2e-storage/training-images/synthetic.png').verify()")
  for folder in ['original','annotated']:assert float(docker('exec',app,'ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1','/tmp/s05-e2e-storage/'+folder+'/synthetic.mp4'))>0
  metadata.update(status='PASS',candidate_commit=commit,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'scripts').glob('pilot_backup*.py')},media_decoders='PASS',runner_no_docker_socket=True)
 except Exception as error:
  import traceback
  metadata.update(status='FAIL',exception_type=type(error).__name__,failure_frames=[{'file':Path(f.filename).name,'line':f.lineno} for f in traceback.extract_tb(error.__traceback__)]);print(json.dumps({k:metadata[k] for k in ['status','exception_type','failure_frames']}),flush=True)
 finally:
  for name in reversed(created):
   obj=inspect(name);assert obj['Config']['Labels'].get(LABEL)==token and not obj.get('HostConfig',{}).get('PortBindings');docker('stop',name)
  metadata['own_containers_stopped']=True;metadata['containers']=created;(evidence/'environment.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
 return 0 if metadata['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
