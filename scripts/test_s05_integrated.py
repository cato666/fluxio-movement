"""Run S05 integrated E2E using ONLY newly created, isolated Docker resources.

No existing network/DB/volume is reused. Leaves own containers stopped for
inspection; tmpfs data disappears at stop. No images, volumes or existing
containers are deleted. Requires cached images, Node and Playwright locally.
"""
import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import time
from urllib.request import urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'com.fluxio.s05-e2e'


def docker(*args):
    completed = subprocess.run(['docker', *args], capture_output=True, text=True)
    if completed.returncode:
        # Never print Docker arguments/env or arbitrary error output.
        raise RuntimeError('isolated_docker_operation_failed')
    return completed.stdout.strip()


def inspect(name):
    return json.loads(docker('inspect', name))[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--node', required=True)
    parser.add_argument('--subnet', required=True)
    args = parser.parse_args()
    if not Path(args.node).is_file():
        raise RuntimeError('local_node_not_available')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip() != 'codex/pilot-v1-stabilization':
        raise RuntimeError('S05 E2E requires the stabilization worktree')
    token = uuid4().hex[:12]
    network, db, app = [f'fluxio-s05-e2e-{kind}-{token}' for kind in ('net','db','app')]
    evidence = Path(tempfile.mkdtemp(prefix='fluxio-s05-integrated-'))
    print('Evidence directory: ' + str(evidence), flush=True)
    created = []
    bridge = None
    label = LABEL + '=' + token
    metadata = {'instance':token,'network':network,'containers':[], 'status':'BLOCKED'}
    try:
        # Inspect existing cached image IDs, never pull/build/download images.
        pg_image = json.loads(docker('image','inspect','postgres:17.6-bookworm'))[0]['Id']
        app_image = json.loads(docker('image','inspect','fluxio-whatsapp-tests:phase2'))[0]['Id']
        subnet = ipaddress.ip_network(args.subnet, strict=True)
        private = [ipaddress.ip_network(x) for x in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16')]
        if subnet.version != 4 or not 24 <= subnet.prefixlen <= 28 or not any(subnet.subnet_of(x) for x in private):
            raise RuntimeError('invalid_isolated_subnet')
        occupied=[]
        for name in docker('network','ls','--format','{{.Name}}').splitlines():
            for cfg in json.loads(docker('network','inspect',name))[0].get('IPAM',{}).get('Config') or []:
                if cfg.get('Subnet'):occupied.append(ipaddress.ip_network(cfg['Subnet']))
        if os.name == 'nt':
            host_routes = subprocess.check_output(['powershell','-NoProfile','-Command',
                'Get-NetRoute -AddressFamily IPv4 | Select-Object -ExpandProperty DestinationPrefix'],text=True).splitlines()
            docker_routes = subprocess.check_output(['wsl.exe','-d','docker-desktop','--','ip','-4','route'],text=True).splitlines()
            host_routes += [line.split()[0] for line in docker_routes if line.strip() and not line.startswith('default')]
        else:
            host_routes = [r['dst'] for r in json.loads(subprocess.check_output(['ip','-j','-4','route'],text=True)) if r.get('dst')!='default']
        occupied += [ipaddress.ip_network(x.strip(),strict=False) for x in host_routes if x.strip() and x.strip()!='0.0.0.0/0']
        if any(x.version==4 and x.overlaps(subnet) for x in occupied):
            raise RuntimeError('isolated_subnet_overlaps_existing_route')
        metadata['isolated_subnet'] = str(subnet)
        docker('network','create','--internal','--subnet',str(subnet),'--label',label,network)
        net = json.loads(docker('network','inspect',network))[0]
        if not net['Internal'] or net.get('Containers'):
            raise RuntimeError('network_not_new_and_internal')
        docker('run','-d','--name',db,'--label',label,'--network',network,
            '--memory','512m','--cpus','1','--pids-limit','128',
            '--tmpfs','/var/lib/postgresql/data:rw,size=256m',
            '-e','POSTGRES_DB=movement_e2e_s05','-e','POSTGRES_USER=s05_synthetic',
            '-e','POSTGRES_PASSWORD=s05-synthetic-only',pg_image)
        created.append(db)
        for _ in range(60):
            if subprocess.run(['docker','exec',db,'pg_isready','-U','s05_synthetic','-d','movement_e2e_s05'],capture_output=True).returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('disposable_database_not_ready')
        env = {'DATABASE_URL':f'postgresql+psycopg://s05_synthetic:s05-synthetic-only@{db}:5432/movement_e2e_s05',
            'S05_E2E_ISOLATED':'1','S05_E2E_DB_HOST':db,'APP_ENV':'test',
            'STORAGE_PATH':'/tmp/s05-e2e-storage','SESSION_SECRET':secrets.token_urlsafe(48),
            'OPENAI_API_KEY':'','KAPSO_API_KEY':'','WHATSAPP_ENABLED':'false',
            'TRAINING_AI_ENABLED':'false','TRAINING_VOICE_ENABLED':'false',
            'AI_REASONING_ENABLED':'false','ENABLE_DEMO_SEED':'false',
            'PYTHONDONTWRITEBYTECODE':'1','FORWARDED_ALLOW_IPS':''}
        env_args = [item for key,value in env.items() for item in ('-e',key+'='+value)]
        setup = """import shutil,time
from pathlib import Path
root=Path('/tmp/s05-e2e');root.mkdir()
for name in ('app','tests','migrations'):
 shutil.copytree('/candidate/'+name,root/name)
shutil.copy('/candidate/alembic.ini',root/'alembic.ini')
(root/'models').mkdir()
shutil.copy('/app/models/pose_landmarker_lite.task',root/'models/pose_landmarker_lite.task')
time.sleep(86400)
"""
        docker('create','--name',app,'--label',label,'--network',network,
            '--read-only','--memory','1g','--cpus','2','--pids-limit','128',
            '--tmpfs','/tmp:rw,size=256m',
            '--mount',f'type=bind,source={ROOT},target=/candidate,readonly',
            *env_args,'--entrypoint','python',app_image,'-c',setup)
        created.append(app)
        a, d = inspect(app), inspect(db)
        if d['Mounts'] or d['HostConfig']['PortBindings']:
            raise RuntimeError('database_persistent_or_published')
        if not d['HostConfig'].get('Tmpfs',{}).get('/var/lib/postgresql/data'):
            raise RuntimeError('database_not_tmpfs')
        if len(a['Mounts']) != 1 or a['Mounts'][0]['RW'] or a['Mounts'][0]['Destination'] != '/candidate':
            raise RuntimeError('unexpected_app_mount')
        for item in (a,d):
            if set(item['NetworkSettings']['Networks']) != {network}:
                raise RuntimeError('unexpected_network_attachment')
        if a['HostConfig']['PortBindings']:
            raise RuntimeError('unexpected_published_port')
        docker('start',app)
        for _ in range(30):
            if subprocess.run(['docker','exec',app,'test','-f','/tmp/s05-e2e/models/pose_landmarker_lite.task'],capture_output=True).returncode==0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('source_copy_not_ready')
        class Handler(BaseHTTPRequestHandler):
            protocol_version='HTTP/1.1'
            def log_message(self,*args):
                pass  # Never log private paths, tokens or payloads.
            def forward(self):
                try:
                    size=int(self.headers.get('Content-Length','0'))
                    if not 0 <= size <= 8*1024*1024:
                        raise RuntimeError('request_too_large')
                    blocked={'connection','transfer-encoding','keep-alive','upgrade','proxy-authorization'}
                    envelope={'method':self.command,'path':self.path,
                        'headers':{k:v for k,v in self.headers.items() if k.lower() not in blocked},
                        'body':base64.b64encode(self.rfile.read(size)).decode()}
                    completed=subprocess.run(['docker','exec','-i','-w','/tmp/s05-e2e',app,
                        'python','-m','tests.e2e.s05_http_bridge'],input=json.dumps(envelope),
                        capture_output=True,text=True,timeout=45)
                    if completed.returncode:
                        raise RuntimeError('http_bridge_failed')
                    result=json.loads(completed.stdout)
                    payload=base64.b64decode(result['body'])
                    self.send_response(result['status'])
                    for key,value in result['headers']:
                        if key.lower() not in blocked|{'content-length','server','date'}:
                            self.send_header(key,value)
                    self.send_header('Content-Length',str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception:
                    self.send_response(502)
                    self.send_header('Content-Length','0')
                    self.end_headers()
            do_GET=do_HEAD=do_POST=do_PUT=do_PATCH=do_DELETE=forward
        bridge=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        bridge.daemon_threads=True
        base='http://127.0.0.1:'+str(bridge.server_address[1])
        threading.Thread(target=bridge.serve_forever,daemon=True).start()
        hash_code = """from pathlib import Path
import hashlib,json
print(json.dumps({p.relative_to(Path('app')).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('app').rglob('*')) if p.is_file() and '__pycache__' not in p.parts}))
"""
        actual_hashes=json.loads(docker('exec','-w','/tmp/s05-e2e',app,'python','-c',hash_code))
        expected_hashes={str(p.relative_to(ROOT/'app')).replace(os.sep,'/'):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT/'app').rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
        if actual_hashes != expected_hashes:
            raise RuntimeError('candidate_runtime_source_mismatch')
        metadata['runtime_source_matches_candidate']=True
        metadata['runtime_source_file_count']=len(actual_hashes)
        origin = 'WEB_ALLOWED_ORIGINS=' + base
        docker('exec','-w','/tmp/s05-e2e','-e',origin,app,'alembic','upgrade','head')
        docker('exec','-w','/tmp/s05-e2e',app,'python','-m','tests.e2e.s05_fixture','init')
        docker('exec','-d','-w','/tmp/s05-e2e','-e',origin,app,'uvicorn','app.main:app',
            '--host','0.0.0.0','--port','8000','--no-access-log','--no-proxy-headers')
        for _ in range(45):
            try:
                with urlopen(base+'/health',timeout=2) as response:
                    if response.status==200:
                        break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError('loopback_server_not_ready')
        metadata.update({'status':'READY','internal_network':True,'loopback_only':True,
            'database_tmpfs':True,'storage_tmpfs':True,'source_mount_readonly':True,'docker_ports_published':False,'transport':'ephemeral_loopback_http_to_docker_stdio_to_real_http',
            'database_name':'movement_e2e_s05','pg_image_id':pg_image,'runtime_image_id':app_image,
            'worker_started':False,'providers_enabled':False,'app_origin':base,
            'containers':[db,app],
            'source_sha256':{str(p.relative_to(ROOT)).replace(os.sep,'/'):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((ROOT/'app').rglob('*')) if p.is_file() and '__pycache__' not in p.parts},
            'candidate_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()})
        (evidence/'environment.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        node_env = os.environ | {'S05_E2E_ISOLATED':'1','S05_E2E_URL':base,'S05_E2E_APP':app,'S05_E2E_EVIDENCE':str(evidence)}
        result = subprocess.run([args.node,str(ROOT/'tests/e2e/s05-integrated.cjs')],cwd=ROOT,env=node_env,
            capture_output=True,text=True)
        # The test suppresses raw assertion URLs, payloads and credentials.
        (evidence/'execution.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        print(result.stdout, end='',flush=True)
        if result.returncode:
            raise RuntimeError('integrated_test_failed')
        metadata['status']='PASS'
    except Exception as error:
        allowed={'isolated_docker_operation_failed','network_not_new_and_internal','disposable_database_not_ready',
            'database_persistent_or_published','database_not_tmpfs','unexpected_app_mount','unexpected_network_attachment',
            'application_not_loopback_only','source_copy_not_ready','loopback_server_not_ready','integrated_test_failed'}
        code=str(error) if str(error) in allowed else 'isolated_environment_failure'
        metadata.update({'status':'BLOCKED' if code!='integrated_test_failed' else 'FAIL','error_code':code,'exception_type':type(error).__name__})
        print('S05 E2E ' + metadata['status'] + ': ' + code,flush=True)
    finally:
        if bridge is not None:
            bridge.shutdown()
            bridge.server_close()
        for name in reversed(created):
            if inspect(name)['Config']['Labels'].get(LABEL) != token:
                raise RuntimeError('refusing_to_stop_unowned_container')
            docker('stop',name)
        metadata['containers']=created
        metadata['own_containers_stopped']=True
        (evidence/'environment.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    return 0 if metadata['status']=='PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
