"""Offline S16 tests: no database, network, provider credentials or user data."""
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pilot_backup_ops', ROOT/'scripts'/'pilot_backup_ops.py')
ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)

class BackupOpsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.storage=self.root/'storage';self.storage.mkdir()
  for name in ops.REQUIRED:(self.storage/name).mkdir()
  (self.storage/'training-images'/'test.png').write_bytes(b'synthetic')
  self.key=os.urandom(32);self.dump=b'PGDMPsynthetic';self.now=datetime.now(timezone.utc)
 def bundle(self):return ops.seal_snapshot(self.dump,self.storage,self.key)
 def collector(self):return self.dump,self.storage
 def runjob(self,**overrides):
  objects={};args=dict(state=self.root/'state',kind='daily',collect=self.collector,put=lambda name,blob:objects.update({name:blob}),get=lambda name:objects[name],key=self.key,notify=lambda value:True)
  args.update(overrides);return ops.run_job(**args)
 def test_roundtrip_database_and_storage(self):
  payload=ops.verify_bundle(self.bundle(),self.key);self.assertEqual(payload['postgres.dump'],self.dump);self.assertEqual(ops.members(payload['storage.tar'])['training-images/test.png'],b'synthetic')
 def test_random_nonce(self):self.assertNotEqual(self.bundle(),self.bundle())
 def test_wrong_key(self):
  with self.assertRaises(ops.BackupError):ops.verify_bundle(self.bundle(),os.urandom(32))
 def test_corruption(self):
  blob=self.bundle()
  with self.assertRaises(ops.BackupError):ops.verify_bundle(blob[:-1]+bytes([blob[-1]^1]),self.key)
 def test_incomplete_storage(self):
  (self.storage/'original').rmdir()
  with self.assertRaises(ops.BackupError):self.bundle()
 def test_invalid_dump(self):
  with self.assertRaises(ops.BackupError):ops.seal_snapshot(b'not_dump',self.storage,self.key)
 def test_oversized_storage(self):
  with patch.object(ops,'MAX_BYTES',1):
   with self.assertRaises(ops.BackupError):self.bundle()
 def test_symlink_denied(self):
  try:(self.storage/'link').symlink_to(self.root)
  except OSError:self.skipTest('Windows symlink privilege unavailable; covered by Linux isolated runner')
  with self.assertRaises(ops.BackupError):self.bundle()
 def test_archive_traversal_denied(self):
  with self.assertRaises(ops.BackupError):ops.members(ops.archive_bytes({'../private':b'no'}))
 def test_legacy_tar_directories_compatible(self):
  blob=ops.archive_bytes({'./original/synthetic.mp4':b'video'},directories=['.','./original'])
  self.assertEqual(ops.members(blob),{'original/synthetic.mp4':b'video'})
 def test_normalized_duplicate_denied(self):
  with self.assertRaises(ops.BackupError):ops.members(ops.archive_bytes({'a':b'one','./a':b'two'}))
 def test_missing_bundle_member(self):
  nonce=os.urandom(12);blob=ops.MAGIC+nonce+AESGCM(self.key).encrypt(nonce,ops.archive_bytes({'manifest.json':b'{}'}),ops.AAD)
  with self.assertRaises(ops.BackupError):ops.verify_bundle(blob,self.key)
 def test_daily_remote_roundtrip(self):
  value=self.runjob();self.assertEqual(value['status'],'COMPLETE');self.assertEqual(len(list((self.root/'state').glob('*.json'))),1)
 def test_pre_release_preserved(self):self.assertEqual(self.runjob(kind='pre-release')['kind'],'pre-release')
 def test_remote_corruption_stays_incomplete(self):self.assertEqual(self.runjob(get=lambda name:b'bad')['status'],'INCOMPLETE')
 def test_transport_uncertain_no_retry_no_delete(self):
  attempts=[]
  def put(name,blob):attempts.append(name);raise TimeoutError('private payload should never leak')
  value=self.runjob(put=put);self.assertEqual(len(attempts),1);self.assertEqual(value['status'],'INCOMPLETE');self.assertNotIn('private',json.dumps(value))
 def test_failure_delivered_to_local_receiver(self):
  receiver=[]
  def notify(value):receiver.append(value);return True
  def collect():raise RuntimeError('sensitive path')
  value=self.runjob(collect=collect,notify=notify);self.assertEqual(value['alert_delivery'],'ACKNOWLEDGED');self.assertEqual(receiver,[ops.event('BACKUP_FAILED',value['id'])]);self.assertNotIn('sensitive',json.dumps(receiver))
 def test_failed_delivery_is_recorded(self):
  def fail():raise RuntimeError()
  value=self.runjob(collect=fail,notify=lambda e:False);self.assertEqual(value['alert_delivery'],'FAILED')
 def test_overlapping_job_cannot_collect(self):
  state=self.root/'state';state.mkdir();(state/'backup.lock').mkdir()
  def fail():self.fail('must not collect')
  self.assertEqual(self.runjob(collect=fail)['code'],'BACKUP_BUSY')
 def test_crashed_incomplete_receipt_health(self):
  record={'id':'a'*32,'kind':'daily','status':'INCOMPLETE','started_at':self.now.isoformat()};codes={v['code'] for v in ops.health([record],self.now)};self.assertEqual(codes,{'BACKUP_INCOMPLETE','BACKUP_MISSING'})
 def record(self,age,kind='daily'):
  stamp=(self.now-timedelta(hours=age)).isoformat();return {'id':str(age).zfill(32),'kind':kind,'status':'COMPLETE','snapshot_at':stamp,'started_at':stamp}
 def test_missing_first_backup(self):self.assertEqual(ops.health([],self.now),[ops.event('BACKUP_MISSING')])
 def test_stale_boundary(self):self.assertEqual(ops.health([self.record(24)],self.now),[ops.event('BACKUP_STALE')])
 def test_recent_backup(self):self.assertEqual(ops.health([self.record(23)],self.now),[])
 def test_future_date_denied(self):
  with self.assertRaises(ops.BackupError):ops.health([self.record(-1)],self.now)
 def test_seven_daily_and_all_pre_release_no_delete(self):
  records=[self.record(i*24) for i in range(9)]+[dict(self.record(999,'pre-release'),id='f'*32)];plan=ops.retention_plan(records);self.assertEqual(len(plan['keep']),8);self.assertEqual(len(plan['proposed_manual_review']),2);self.assertFalse(plan['automatic_deletion'])
 def test_event_rejects_private_data(self):
  with self.assertRaises(ops.BackupError):ops.event('BACKUP_FAILED','phone or secret')
 def test_configuration_disabled_before_adapter_load(self):
  path=self.root/'config.json';path.write_text('{}')
  with self.assertRaises(ops.BackupError):ops.configured_run(path,'daily')
 def test_modified_adapter_hash_rejected(self):
  adapter=self.root/'adapter.py';adapter.write_text('raise Exception("never execute")')
  config={'execution_enabled':True,'scheduler_enabled':True,'approval':{'infrastructure_approved':True},'destination':{'private_access_verified':True},'credentials':{'least_privilege_verified':True},'recovery_secrets':{'independent_recovery_verified':True},'operational_adapter':{'path':str(adapter),'sha256':'bad'}}
  path=self.root/'config.json';path.write_text(json.dumps(config))
  with self.assertRaises(ops.BackupError):ops.configured_run(path,'daily')

if __name__=='__main__':unittest.main()
