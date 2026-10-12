"""Online collector fail-closed tests; integration uses real PostgreSQL separately."""
import unittest,tempfile,json
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
import pilot_backup_runner as runner
class OnlineTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.source=self.root/'source';self.source.mkdir();self.work=self.root/'work';self.work.mkdir();self.file=self.source/'training-images'/'photo.jpg';self.file.parent.mkdir();self.file.write_bytes(b'complete')
  self.c={'BACKUP_CAPTURE_MODE':'online_v1','STORAGE_PATH':str(self.source),'BACKUP_APPLICATION_STORAGE_PATH':'/data/storage','max_bytes':1048576,'timeout':10,'BACKUP_PG_SERVICE':'fixture','PGSERVICEFILE':'unused','PGPASSFILE':'unused'}
  @contextmanager
  def snapshot(c):yield None,'snapshot-fixed','head'
  self.addCleanup(patch.stopall);patch.object(runner,'snapshot',snapshot).start();patch.object(runner,'reference_files',return_value=['training-images/photo.jpg']).start()
 def dump(self,args,**kw):
  Path(next(a[7:] for a in args if a.startswith('--file='))).write_bytes(b'PGDMPfixture');return type('Result',(),{'returncode':0})()
 def test_missing_referenced_file_aborts(self):
  self.file.unlink()
  with self.assertRaisesRegex(runner.RunnerError,'referenced_media_missing'):runner.capture_online(self.c,self.work)
 def test_mutation_after_dump_aborts(self):
  def run(*args,**kw):
   result=self.dump(*args,**kw);self.file.write_bytes(b'changed');return result
  with patch.object(runner.subprocess,'run',side_effect=run):
   with self.assertRaisesRegex(runner.RunnerError,'referenced_media_changed'):runner.capture_online(self.c,self.work)
 def test_growth_does_not_change_snapshot_set(self):
  def run(*args,**kw):
   result=self.dump(*args,**kw);(self.source/'training-images/new.jpg').write_bytes(b'after-T');return result
  with patch.object(runner.subprocess,'run',side_effect=run):
   dump,storage,head,stamp=runner.capture_online(self.c,self.work)
  self.assertEqual(self.c['_snapshot_references'],['training-images/photo.jpg']);self.assertFalse((storage/'training-images/new.jpg').exists());self.assertEqual((storage/'training-images/photo.jpg').read_bytes(),b'complete')
 def test_symlink_aborts(self):
  self.file.unlink();self.file.symlink_to(self.source/'outside')
  with self.assertRaisesRegex(runner.RunnerError,'referenced_media_missing'):runner.capture_online(self.c,self.work)
 def test_online_gate_required(self):
  with self.assertRaisesRegex(runner.RunnerError,'online_protocol_not_verified'):runner.config({'BACKUP_CAPTURE_MODE':'online_v1'})
 def test_unknown_mode_rejected(self):
  with self.assertRaisesRegex(runner.RunnerError,'capture_mode_invalid'):runner.config({'BACKUP_CAPTURE_MODE':'unsafe'})
class ReferenceValidationTests(unittest.TestCase):
 def connection(self,table,row):
  class Connection:
   def execute(self,sql):return [row] if sql.endswith(' FROM '+table) else []
  return Connection()
 def test_empty_photo_or_whatsapp_reference_is_not_silently_skipped(self):
  for table in ['training_images','whatsapp_media']:
   with self.assertRaisesRegex(runner.RunnerError,'required_media_reference_empty'):
    runner.reference_files(self.connection(table,('',)),'/data/storage')
 def test_completed_analysis_requires_original_and_annotated(self):
  for row in [('',None,None,None,'COMPLETED'),('uploads/a.mp4','',None,None,'COMPLETED')]:
   with self.assertRaisesRegex(runner.RunnerError,'required_media_reference_empty'):
    runner.reference_files(self.connection('analyses',row),'/data/storage')
 def test_failed_upload_without_published_artifact_is_explicitly_allowed(self):
  self.assertEqual(runner.reference_files(self.connection('analyses',('',None,None,None,'FAILED')),'/data/storage'),[])
if __name__=='__main__':unittest.main()
