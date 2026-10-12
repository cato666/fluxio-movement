"""Restore only to explicitly authorized NEW isolated database/storage."""
import argparse,json,os,re,subprocess,tempfile,tarfile,io
from pathlib import Path
import psycopg
import pilot_backup_bundle as bundle
import pilot_backup_ops as legacy

def restore(env,source,destination,expected_sha,key_id):
 if env.get('BACKUP_RESTORE_ISOLATED_CONFIRMED','').lower()!='true':raise ValueError('restore_not_authorized')
 source=Path(source);destination=Path(destination)
 if not source.is_file() or source.is_symlink() or destination.exists() or not destination.is_absolute():raise ValueError('target_invalid')
 if not re.fullmatch('[a-f0-9]{64}',expected_sha) or bundle.sha(source)!=expected_sha:raise ValueError('ciphertext_integrity_failed')
 keypath=Path(env['BACKUP_AES_KEY_FILE'])
 if keypath.is_symlink():raise ValueError('key_invalid')
 key=keypath.read_bytes()
 if len(key)!=32:raise ValueError('key_invalid')
 service=env['RESTORE_PG_SERVICE']
 if not re.fullmatch('[A-Za-z0-9_-]{1,64}',service):raise ValueError('service_invalid')
 with psycopg.connect('service='+service,application_name='fluxio-isolated-restore',connect_timeout=10) as connection:
  if not connection.info.dbname.startswith('movement_restore_'):raise ValueError('database_name_guard')
  if connection.execute("select count(*) from pg_tables where schemaname not in ('pg_catalog','information_schema')").fetchone()[0]:raise ValueError('database_not_empty')
 with tempfile.TemporaryDirectory(prefix='owned-restore-',dir=env['BACKUP_WORK_PATH']) as directory:
  work=Path(directory)
  with source.open('rb') as stream:magic=stream.read(9)
  if magic==bundle.MAGIC:
   plain=work/'verified.tar';metadata=bundle.unseal(source,plain,key,key_id,int(env.get('BACKUP_MAX_SET_BYTES',str(4*1024**3))));manifest=bundle.unpack_verified(plain,work/'unpacked',int(env.get('BACKUP_MAX_SET_BYTES',str(4*1024**3))))
   if any(manifest.get(k)!=v for k,v in metadata.items()):raise ValueError('metadata_mismatch')
   dump=work/'unpacked'/'postgres.dump';storage=work/'unpacked'/'storage'
  elif magic==legacy.MAGIC:
   # Legacy bounded format, external key_id association and ciphertext checksum.
   parts=legacy.verify_bundle(source.read_bytes(),key);dump=work/'postgres.dump';dump.write_bytes(parts['postgres.dump']);storage=work/'storage';storage.mkdir()
   with tarfile.open(fileobj=io.BytesIO(parts['storage.tar'])) as archive:bundle.extract_entries(archive,storage)
   metadata={'format':'FXS16GCM1','key_id':key_id,'legacy_key_id_source':'operator_external_manifest'}
  else:raise ValueError('format_invalid')
  private_env=dict(os.environ);private_env.update(PGSERVICEFILE=env['PGSERVICEFILE'],PGPASSFILE=env['PGPASSFILE'],PGAPPNAME='fluxio-isolated-restore')
  result=subprocess.run(['pg_restore','--dbname=service='+service,'--no-owner','--no-acl','--exit-on-error',str(dump)],env=private_env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=int(env.get('BACKUP_COMMAND_TIMEOUT_SECONDS','600')))
  if result.returncode:raise ValueError('restore_failed')
  # A target was verified NEW before work; never merges with existing media.
  import shutil
  if magic==bundle.MAGIC and manifest.get('media_protocol'):
   from pilot_backup_runner import reference_files, checked_source, PROTOCOL
   if manifest['media_protocol']!=PROTOCOL:raise ValueError('media_protocol_unknown')
   with psycopg.connect('service='+service) as connection:
    refs=reference_files(connection,manifest['application_storage_path'])
   if refs!=manifest['snapshot_references']:raise ValueError('restored_references_mismatch')
   for relative in refs:checked_source(storage,relative)
  shutil.copytree(storage,destination)
  return {'status':'RESTORED_ISOLATED','format':metadata['format'],'key_id':key_id,'source_commit':metadata.get('source_commit'),'production_restore':False}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--storage-destination',required=True);parser.add_argument('--expected-sha256',required=True);parser.add_argument('--key-id',required=True);args=parser.parse_args()
 try:
  result=restore(dict(os.environ),args.source,args.storage_destination,args.expected_sha256,args.key_id);print(json.dumps(result));return 0
 except Exception:print(json.dumps({'status':'BLOCKED','code':'isolated_restore_failed'}));return 1
if __name__=='__main__':raise SystemExit(main())
