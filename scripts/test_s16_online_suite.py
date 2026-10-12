"""Full regressions on a new disposable PostgreSQL instance; no provider network."""
import json,subprocess,tempfile,time,ipaddress,argparse
from pathlib import Path
from uuid import uuid4
from test_pilot_backup_runner_integration import docker,inspect,ROOT

def main():
 token=uuid4().hex[:12];label='com.fluxio.s16-suite';net='fluxio-s16-suite-'+token;db='fluxio-s16-suite-db-'+token;app='fluxio-s16-suite-app-'+token
 evidence=Path(tempfile.mkdtemp(prefix='fluxio-s16-suite-'));created=[];result={'status':'BLOCKED','network':net,'database_tmpfs':True,'no_ports':True,'real_provider_calls':0}
 parser=argparse.ArgumentParser();parser.add_argument('--subnet',default='10.253.24.0/28');args=parser.parse_args();subnet=ipaddress.ip_network(args.subnet)
 assert subnet.is_private and subnet.prefixlen==28
 try:
  for name in docker('network','ls','--format','{{.Name}}').decode().splitlines():
   for cfg in json.loads(docker('network','inspect',name))[0].get('IPAM',{}).get('Config') or []:
    if cfg.get('Subnet') and ipaddress.ip_network(cfg['Subnet']).version==4:assert not subnet.overlaps(ipaddress.ip_network(cfg['Subnet']))
  docker('network','create','--internal','--subnet',str(subnet),'--label',label+'='+token,net)
  docker('run','-d','--name',db,'--label',label+'='+token,'--network',net,'--memory','512m','--tmpfs','/var/lib/postgresql/data:rw,size=256m','-e','POSTGRES_DB=movement_test','-e','POSTGRES_USER=movement','-e','POSTGRES_PASSWORD=movement','postgres:17.6-bookworm');created.append(db)
  for _ in range(40):
   if subprocess.run(['docker','exec',db,'pg_isready','-U','movement'],capture_output=True).returncode==0:break
   time.sleep(1)
  else:raise RuntimeError('isolated_postgres_unavailable')
  env=['APP_ENV=development','ENABLE_DEMO_SEED=true','DEMO_PASSWORD=demo1234','WHATSAPP_ENABLED=false','TEST_DATABASE_RESET=1','SESSION_SECRET=synthetic-suite-session-abcdefghijklmnopqrstuvwxyz','DATABASE_URL=postgresql+psycopg://movement:movement@'+db+':5432/movement_test','STORAGE_PATH=/tmp/media','PYTHONDONTWRITEBYTECODE=1']
  command=['run','-d','--name',app,'--label',label+'='+token,'--network',net,'--memory','1536m','--tmpfs','/tmp:rw,exec,size=1024m','--mount','type=bind,src='+str(ROOT)+',dst=/candidate,readonly','--entrypoint','sleep']
  for value in env:command+=['-e',value]
  docker(*command,'fluxio-whatsapp-tests:phase2','infinity');created.append(app)
  docker('exec',app,'python','-c',"from pathlib import Path;import shutil;r=Path('/tmp/suite');r.mkdir();[shutil.copytree('/candidate/'+n,r/n) for n in ['app','migrations','tests','scripts']];shutil.copyfile('/candidate/alembic.ini',r/'alembic.ini');shutil.copytree('/app/models',r/'models')")
  directed=subprocess.run(['docker','exec','-w','/tmp/suite',app,'python','-m','pytest','-q','tests/test_s16_media_consistency.py'],capture_output=True)
  (evidence/'directed.log').write_bytes(directed.stdout+directed.stderr);print(directed.stdout.decode(),flush=True)
  if directed.returncode:raise RuntimeError('directed_regression_failed')
  full=subprocess.run(['docker','exec','-w','/tmp/suite',app,'python','-m','pytest','-q'],capture_output=True)
  (evidence/'python.log').write_bytes(full.stdout+full.stderr);print(full.stdout.decode()[-7000:],flush=True)
  result['status']='PASS' if full.returncode==0 else 'FAIL';result['full_exit_code']=full.returncode
 except Exception as error:result.update(status='FAIL',error_type=type(error).__name__,code=str(error) if isinstance(error,RuntimeError) else 'harness_failed')
 finally:
  for name in reversed(created):
   info=inspect(name);assert info['Config']['Labels'].get(label)==token and not info['HostConfig'].get('PortBindings');docker('stop',name)
  result['owned_containers_stopped']=True;(evidence/'results.json').write_text(json.dumps(result,indent=2));print('Evidence: '+str(evidence),flush=True);print(json.dumps(result),flush=True)
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
