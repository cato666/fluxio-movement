"""Offline runner tests: all DB/R2/Telegram interactions are simulated here."""
import unittest,tempfile,json,os,sys,subprocess,time,io,tarfile,threading
from pathlib import Path
from datetime import datetime,timezone,timedelta
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from contextlib import contextmanager
import pilot_backup_runner as runner
import pilot_backup_bundle as bundle
import pilot_backup_restore as restore
import pilot_backup_ops as ops

class Store:
 def __init__(self):self.objects={};self.puts=0
 def put(self,name,path):self.puts+=1;self.objects[name]=Path(path).read_bytes()
 def get(self,name,path):Path(path).write_bytes(self.objects[name])

class RunnerTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.source=self.root/'source';self.work=self.root/'work';self.state=self.root/'state'
  for path in [self.source,self.work,self.state]:path.mkdir()
  for name in ops.REQUIRED:(self.source/name).mkdir()
  (self.source/'training-images'/'synthetic.png').write_bytes(b'synthetic-photo');(self.source/'original'/'synthetic.mp4').write_bytes(b'synthetic-video')
  for name,value in [('key',b'k'*32),('service',b'synthetic'),('pass',b'synthetic')]:p=self.root/name;p.write_bytes(value);p.chmod(0o600)
  self.env={'BACKUP_RUNNER_ENABLED':'true','BACKUP_STATE_PATH':str(self.state),'BACKUP_WORK_PATH':str(self.work),'STORAGE_PATH':str(self.source),'BACKUP_AES_KEY_FILE':str(self.root/'key'),'BACKUP_AES_KEY_ID':'synthetic-k1','BACKUP_PG_SERVICE':'synthetic','PGSERVICEFILE':str(self.root/'service'),'PGPASSFILE':str(self.root/'pass'),'BACKUP_QUIESCENCE_FILE':str(self.root/'window.json'),'BACKUP_SOURCE_COMMIT':'a'*40,'R2_ENDPOINT':'https://'+('a'*32)+'.r2.cloudflarestorage.com','R2_BUCKET':'fluxio-movement-backups','R2_ACCESS_KEY_ID':'fake','R2_SECRET_ACCESS_KEY':'fake','BACKUP_MAX_SET_BYTES':str(512*1024**2)}
  self.window();self.events=[];self.store=Store()
 def window(self,**changes):
  value={'issued_at':datetime.now(timezone.utc).isoformat(),'expires_at':(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat(),'writers_paused':True,'scope':'all-db-and-storage-writers','source_commit':'a'*40,'storage_path':str(self.source)};value.update(changes);(self.root/'window.json').write_text(json.dumps(value))
 def collector(self,c,work):
  dest=work/'storage';import shutil;shutil.copytree(self.source,dest);dump=work/'postgres.dump';dump.write_bytes(b'PGDMPsynthetic');return dump,dest,'0024_training_save_requests',datetime.now(timezone.utc).isoformat()
 def alert(self,c,event):self.events.append(event);return True
 def run_backup(self,**changes):
  args={'env':self.env,'kind':'daily','store':self.store,'collector':self.collector,'notification':self.alert};args.update(changes);return runner.backup(**args)
 def test_complete_streaming_bundle(self):
  result=self.run_backup();self.assertEqual(result['status'],'COMPLETE');self.assertEqual(result['key_id'],'synthetic-k1');self.assertEqual(self.store.puts,1);self.assertFalse(list(self.work.iterdir()))
 def test_pre_release(self):self.assertEqual(self.run_backup(kind='pre-release')['status'],'COMPLETE')
 def test_source_media_unchanged(self):
  before=runner.inventory(self.source,512*1024**2);self.run_backup();self.assertEqual(before,runner.inventory(self.source,512*1024**2))
 def test_missing_secret(self):
  self.env.pop('R2_SECRET_ACCESS_KEY');self.assertEqual(self.run_backup()['status'],'BLOCKED');self.assertEqual(self.store.puts,0)
 def test_disabled_no_notifications(self):
  self.env['BACKUP_RUNNER_ENABLED']='false';self.assertEqual(self.run_backup()['status'],'DISABLED');self.assertEqual(self.events,[])
 def test_bad_key(self):
  (self.root/'key').write_bytes(b'bad');self.assertEqual(self.run_backup()['status'],'INCOMPLETE');self.assertEqual(len(self.events),1)
 def test_postgres_failure(self):
  def fail(*args):raise runner.RunnerError('postgres_failed')
  result=self.run_backup(collector=fail);self.assertEqual(result['status'],'INCOMPLETE');self.assertEqual(result['error_code'],'postgres_failed')
 def test_r2_failure_no_retry(self):
  class Fail(Store):
   def put(self,name,path):self.puts+=1;raise TimeoutError('private url token')
  store=Fail();r=self.run_backup(store=store);self.assertEqual(r['status'],'INCOMPLETE');self.assertEqual(store.puts,1);self.assertNotIn('token',json.dumps(r))
 def test_r2_corruption(self):
  class Bad(Store):
   def get(self,name,path):Path(path).write_bytes(b'corrupt')
  self.assertEqual(self.run_backup(store=Bad())['status'],'INCOMPLETE')
 def test_encryption_failure(self):
  with patch.object(bundle,'seal',side_effect=ValueError('private data')):r=self.run_backup()
  self.assertEqual(r['status'],'INCOMPLETE');self.assertEqual(self.store.puts,0)
 def test_telegram_failure_nonfatal(self):
  def fail(*args):raise runner.RunnerError('postgres_failed')
  def notify(*args):raise TimeoutError('secret')
  result=self.run_backup(collector=fail,notification=notify);self.assertEqual(result['status'],'INCOMPLETE');self.assertEqual(result['alert_delivery'],'FAILED')
 def test_concurrent(self):
  def collect(c,w):time.sleep(.1);return self.collector(c,w)
  with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda _:self.run_backup(collector=collect),range(2)))
  self.assertEqual(sum(r['status']=='COMPLETE' for r in results),1);self.assertEqual(self.store.puts,1)
 def test_recovery_after_process_interruption(self):
  program="import sys,time;sys.path.insert(0,sys.argv[1]);import pilot_backup_runner as r;s=r.acquire_lock(sys.argv[2]);print('LOCKED',flush=True);time.sleep(60)"
  child=subprocess.Popen([sys.executable,'-c',program,str(Path(runner.__file__).parent),str(self.state/'runner.lock')],stdout=subprocess.PIPE,text=True)
  try:
   self.assertEqual(child.stdout.readline().strip(),'LOCKED');self.assertEqual(self.run_backup()['code'],'BACKUP_BUSY')
  finally:child.kill();child.wait();child.stdout.close()
  self.assertEqual(self.run_backup()['status'],'COMPLETE')
 def test_stale_and_incomplete(self):
  with patch.object(runner,'notify',side_effect=lambda c,e:self.alert(c,e)):
   self.assertTrue(runner.check_health(self.env));self.assertEqual(self.events[-1]['code'],'BACKUP_MISSING')
  stamp=(datetime.now(timezone.utc)-timedelta(hours=25)).isoformat();ops.receipt(self.state/('b'*32+'.json'),{'id':'b'*32,'kind':'daily','status':'COMPLETE','snapshot_at':stamp,'started_at':stamp})
  with patch.object(runner,'notify',return_value=False):self.assertIn('BACKUP_STALE',[e['code'] for e in runner.check_health(self.env)])
 def test_expired_window(self):
  self.window(issued_at=(datetime.now(timezone.utc)-timedelta(minutes=10)).isoformat(),expires_at=(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat())
  with self.assertRaises(runner.RunnerError):runner.window(self.env)
 def test_pause_not_confirmed(self):
  self.window(writers_paused=False)
  with self.assertRaises(runner.RunnerError):runner.window(self.env)
 def test_health_incident_id_stable_without_retry(self):
  with patch.object(runner,'notify',return_value=False) as notify:
   runner.check_health(self.env);first=notify.call_args[0][1]['request_id'];runner.check_health(self.env);self.assertEqual(first,notify.call_args[0][1]['request_id'])
 def test_watchdog_does_not_call_active_job_incomplete(self):
  clock=datetime.now(timezone.utc).isoformat();ops.receipt(self.state/('c'*32+'.json'),{'id':'c'*32,'kind':'daily','status':'INCOMPLETE','started_at':clock})
  lock=runner.acquire_lock(self.state/'runner.lock')
  try:
   with patch.object(runner,'notify',return_value=False):self.assertNotIn('BACKUP_INCOMPLETE',[e['code'] for e in runner.check_health(self.env)])
  finally:runner.release_lock(lock)
  with patch.object(runner,'notify',return_value=False):self.assertIn('BACKUP_INCOMPLETE',[e['code'] for e in runner.check_health(self.env)])
 def test_reserved_schedule_crash_detected(self):
  stamp=(datetime.now(timezone.utc)-timedelta(minutes=6)).isoformat();ops.receipt(self.state/'schedule-test.json',{'status':'ATTEMPTED','reserved_at':stamp})
  with patch.object(runner,'notify',return_value=False):codes=[e['code'] for e in runner.check_health(self.env)]
  self.assertIn('BACKUP_INCOMPLETE',codes)
 def test_schedule_catchup_and_no_duplicate(self):
  self.env.update(BACKUP_SCHEDULE_ENABLED='true',BACKUP_DAILY_TIME='00:00',BACKUP_SCHEDULE_TIMEZONE='UTC')
  for repeat in range(2):
   with patch.object(runner,'backup',return_value={'status':'COMPLETE'}) as job,patch.object(runner,'check_health',return_value=[]),patch.object(runner.time,'sleep',side_effect=RuntimeError('stop test loop')):
    with self.assertRaises(RuntimeError):runner.schedule(self.env)
    self.assertEqual(job.call_count,1 if repeat==0 else 0)
 def test_staging_space_fail_closed(self):
  class Usage:free=0
  with patch.object(runner.shutil,'disk_usage',return_value=Usage()):result=self.run_backup()
  self.assertEqual(result['error_code'],'staging_capacity_insufficient');self.assertEqual(self.store.puts,0)
 def test_captured_manifest_and_legacy_format_unchanged(self):
  self.assertEqual(ops.MAGIC,b'FXS16GCM1');result=self.run_backup();self.assertEqual(result['alembic_head'],'0024_training_save_requests')
 def test_source_symlink(self):
  try:(self.source/'link').symlink_to(self.root)
  except OSError:self.skipTest('Windows symlink privilege')
  self.assertEqual(self.run_backup()['status'],'INCOMPLETE')
 def test_mount_overlap(self):
  self.env['BACKUP_STATE_PATH']=str(self.source)
  self.assertEqual(self.run_backup()['status'],'BLOCKED')
 def test_r2_bucket_scope_enforced(self):
  self.env['R2_BUCKET']='another-bucket'
  with self.assertRaises(runner.RunnerError):runner.R2(self.env)
 def test_r2_signed_streaming_http_simulated(self):
  objects={}
  class Response(io.BytesIO):
   status=200
  class Opener:
   def open(inner,request,timeout):
    self.assertTrue(request.full_url.startswith('https://'));self.assertIn('AWS4-HMAC-SHA256',request.get_header('Authorization'))
    if request.get_method()=='PUT':
     body=b''.join(request.data);self.assertEqual(int(request.get_header('Content-length')),len(body));self.assertEqual(request.get_header('X-amz-content-sha256'),__import__('hashlib').sha256(body).hexdigest());objects[request.full_url]=body;return Response(b'')
    return Response(objects[request.full_url])
  source=self.root/'encrypted-file';source.write_bytes(b'encrypted-synthetic-fixture');target=self.root/'download-file'
  with patch.object(runner.urllib.request,'build_opener',return_value=Opener()):
   r2=runner.R2(runner.config(self.env));r2.put('backups/daily/synthetic.fxb2',source);r2.get('backups/daily/synthetic.fxb2',target)
  self.assertEqual(target.read_bytes(),source.read_bytes())
 def test_r2_redirects_disabled(self):self.assertIsNone(runner.NoRedirect().redirect_request(None,None,302,None,None,None))
 def test_r2_http_rejected(self):
  self.env['R2_ENDPOINT']='http://'+('a'*32)+'.r2.cloudflarestorage.com'
  with self.assertRaises(runner.RunnerError):runner.R2(self.env)
 def test_gcm_tampering_and_key_id(self):
  result=self.run_backup();cipher=self.root/'cipher';cipher.write_bytes(next(iter(self.store.objects.values())))
  with self.assertRaises(bundle.BundleError):bundle.unseal(cipher,self.root/'wrong',b'k'*32,'another-key',512*1024**2)
  raw=cipher.read_bytes();cipher.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
  with self.assertRaises(Exception):bundle.unseal(cipher,self.root/'tampered',b'k'*32,'synthetic-k1',512*1024**2)
 def test_streaming_beyond_legacy_128_mib(self):
  plain=self.root/'large';size=129*1024**2
  with plain.open('wb') as stream:stream.seek(size-1);stream.write(b'x')
  metadata={'format':'FXS16GCM2','cipher':'AES-256-GCM','key_id':'synthetic-k1'};cipher=self.root/'large.enc';recovered=self.root/'large.out';bundle.seal(plain,cipher,b'k'*32,metadata);bundle.unseal(cipher,recovered,b'k'*32,'synthetic-k1',512*1024**2);self.assertEqual(bundle.sha(plain),bundle.sha(recovered))
 def test_unsafe_archive(self):
  file=self.root/'unsafe.tar'
  with tarfile.open(file,'w') as archive:
   info=tarfile.TarInfo('../escape');info.size=1;archive.addfile(info,io.BytesIO(b'x'))
  with self.assertRaises(bundle.BundleError):bundle.verify_archive(file,512*1024**2)
 def test_restore_guard_before_database_access(self):
  with self.assertRaises(ValueError):restore.restore({},'anything',str(self.root/'new'),'a'*64,'synthetic-k1')
 def test_lock_cleanup_without_source_deletion(self):
  self.run_backup();self.assertTrue((self.state/'runner.lock').exists());self.assertTrue((self.source/'original'/'synthetic.mp4').exists())

if __name__=='__main__':unittest.main()
