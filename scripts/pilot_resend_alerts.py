"""S16 Resend adapter. Disabled by default; no sends on import or CLI startup."""
import hashlib
import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

CODES={'BACKUP_FAILED','BACKUP_MISSING','BACKUP_STALE','BACKUP_INCOMPLETE','ALERT_DELIVERY_FAILED','BACKUP_ALERT_TEST'}
ENDPOINT='https://api.resend.com/emails'

class AlertError(Exception):
    pass

def payload(code, backup_id, timestamp, sender, recipient):
    if code not in CODES:
        raise AlertError('invalid_event')
    if backup_id is not None and not re.fullmatch(r'[a-f0-9]{32}',backup_id):
        raise AlertError('invalid_id')
    stamp=datetime.fromisoformat(timestamp)
    if stamp.tzinfo is None:
        raise AlertError('invalid_timestamp')
    for address in [sender,recipient]:
        if not isinstance(address,str) or not re.fullmatch(r'[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+',address):
            raise AlertError('invalid_address')
    test=code=='BACKUP_ALERT_TEST'
    subject='Fluxio Pilot A — '+('prueba de alerta S16' if test else 'alerta de respaldo '+code)
    text=('Prueba controlada; no corresponde a un fallo real.\n' if test else 'Se requiere revisar el estado del respaldo.\n')
    text+='Evento: '+code+'\nFecha UTC: '+stamp.astimezone(timezone.utc).isoformat()+'\nID operativo: '+(backup_id or 'no aplica')+'\n'
    text+='Gastón: confirma la recepción para validar el canal.'
    return {'from':sender,'to':[recipient],'subject':subject,'text':text}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None

def transport(body,api_key,request_id):
    request=urllib.request.Request(ENDPOINT,data=json.dumps(body).encode(),method='POST',headers={'Authorization':'Bearer '+api_key,'Content-Type':'application/json','Idempotency-Key':request_id})
    # Never forward Authorization or private addresses to a redirect destination.
    opener=urllib.request.build_opener(NoRedirect)
    with opener.open(request,timeout=15) as response:
        return response.status,json.loads(response.read(4096))

def save(path,value):
    # Caller created the exclusive request directory, so this write cannot
    # overwrite another sender's attempt. No addresses/payload/key persisted.
    with Path(path).open('w',encoding='utf-8') as stream:
        os.chmod(path,0o600)
        json.dump(value,stream)
        stream.flush();os.fsync(stream.fileno())

def send_once(code,backup_id,timestamp,request_id,state,env=None,authorized=False,send=transport):
    env=os.environ if env is None else env
    if not authorized or env.get('BACKUP_ALERTS_ENABLED','').lower()!='true':
        raise AlertError('send_not_authorized')
    if env.get('BACKUP_ALERT_DOMAIN_VERIFIED','').lower()!='true':
        raise AlertError('domain_not_confirmed')
    key=env.get('RESEND_API_KEY')
    if not key:
        raise AlertError('configuration_missing')
    if not re.fullmatch(r'[a-f0-9]{32}',request_id):
        raise AlertError('invalid_request_id')
    body=payload(code,backup_id,timestamp,env.get('BACKUP_ALERT_FROM'),env.get('BACKUP_ALERT_TO'))
    digest=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
    state=Path(state)
    if state.is_symlink() or not state.is_dir():
        raise AlertError('private_state_required')
    attempt=state/request_id
    try:
        attempt.mkdir(mode=0o700)
    except FileExistsError:
        # Never repeat an accepted, failed, uncertain or in-progress attempt.
        path=attempt/'result.json'
        if not path.is_file():return {'status':'UNCERTAIN','request_id':request_id}
        record=json.loads(path.read_text(encoding='utf-8'))
        if record['payload_hash']!=digest:raise AlertError('idempotency_conflict')
        return record
    path=attempt/'result.json'
    record={'status':'UNCERTAIN','request_id':request_id,'payload_hash':digest,'receipt_confirmed':False}
    save(path,record)  # Durable before entering external transport; crash stays uncertain.
    try:
        status,response=send(body,key,request_id)
        if status in (200,201,202) and isinstance(response,dict):
            identifier=str(UUID(response['id']))
            record.update(status='ACCEPTED',provider_id=identifier)
        else:
            record['status']='UNCERTAIN'
    except urllib.error.HTTPError as error:
        # Provider body/headers are intentionally neither read nor recorded.
        record['status']='REJECTED' if error.code in (400,401,403,404,422,429) else 'UNCERTAIN'
        record['http_status']=error.code
    except Exception:
        record['status']='UNCERTAIN'
    save(path,record)
    return record
