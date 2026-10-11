"""S16 outbound Telegram only. No webhook or sends on import."""
import json,os,re,hashlib,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
from pilot_resend_alerts import AlertError,NoRedirect,save

CODES={'BACKUP_FAILED','BACKUP_MISSING','BACKUP_STALE','BACKUP_INCOMPLETE','ALERT_DELIVERY_FAILED','BACKUP_ALERT_TEST','RESTORE_FAILED','RESTORE_COMPLETE','WORKER_DOWN','WORKER_STALE','CRITICAL_ERROR'}

def text(code,backup_id,timestamp):
 if code not in CODES or (backup_id is not None and not re.fullmatch('[a-f0-9]{32}',backup_id)):
  raise AlertError('invalid_event')
 stamp=datetime.fromisoformat(timestamp)
 if stamp.tzinfo is None:raise AlertError('invalid_timestamp')
 return ('Fluxio Pilot A — '+code+'\n'+('Prueba controlada; no es un fallo real.\n' if code=='BACKUP_ALERT_TEST' else '')+'Fecha UTC: '+stamp.astimezone(timezone.utc).isoformat()+'\nID operativo: '+(backup_id or 'no aplica')+'\nRevisar el estado operativo. Sin datos de atletas.')

def transport(token,body,timeout):
 # The Telegram token is necessarily in the API path; never log URL/errors.
 req=urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage',data=json.dumps(body).encode(),method='POST',headers={'Content-Type':'application/json'})
 opener=urllib.request.build_opener(NoRedirect)
 try:
  with opener.open(req,timeout=timeout) as r:return r.status,json.loads(r.read(65536))
 except urllib.error.HTTPError as error:
  retry=0
  if error.code==429:
   try:retry=int(json.loads(error.read(4096)).get('parameters',{}).get('retry_after',0))
   except Exception:pass
  # No exception body, description, chat data, token or URL escapes here.
  return error.code,{'ok':False,'parameters':{'retry_after':max(0,retry)}}

def send_once(code,backup_id,timestamp,request_id,state,env=None,authorized=False,send=transport,now=None):
 env=os.environ if env is None else env
 if not authorized or env.get('TELEGRAM_ALERTS_ENABLED','').lower()!='true':raise AlertError('send_not_authorized')
 token=env.get('TELEGRAM_BOT_TOKEN','');chat=env.get('TELEGRAM_CHAT_ID','')
 if not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]{20,}',token) or not re.fullmatch(r'-?[1-9][0-9]*',chat):raise AlertError('configuration_invalid')
 if not re.fullmatch('[a-f0-9]{32}',request_id):raise AlertError('invalid_request_id')
 timeout=int(env.get('TELEGRAM_ALERT_TIMEOUT_SECONDS','10'));interval=int(env.get('TELEGRAM_ALERT_MIN_INTERVAL_SECONDS','60'));daily=int(env.get('TELEGRAM_ALERT_DAILY_LIMIT','20'))
 if not 1<=timeout<=30 or not 1<=interval<=86400 or not 1<=daily<=100:raise AlertError('limits_invalid')
 body={'chat_id':chat,'text':text(code,backup_id,timestamp),'protect_content':True,'link_preview_options':{'is_disabled':True}}
 digest=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
 state=Path(state)
 if state.is_symlink() or not state.is_dir():raise AlertError('private_state_required')
 lock=state/'telegram.lock'
 try:lock.mkdir(mode=0o700)
 except FileExistsError:return {'status':'BUSY','receipt_confirmed':False}
 try:
  attempt=state/('telegram-'+request_id)
  if attempt.exists():
   if attempt.is_symlink():raise AlertError('unsafe_state')
   file=attempt/'result.json'
   if not file.is_file():return {'status':'UNCERTAIN','receipt_confirmed':False}
   record=json.loads(file.read_text(encoding='utf-8'))
   if record['payload_hash']!=digest:raise AlertError('idempotency_conflict')
   return record
  clock=now or datetime.now(timezone.utc)
  if clock.tzinfo is None:raise AlertError('invalid_clock')
  clock=clock.astimezone(timezone.utc);seconds=clock.timestamp();day=clock.date().isoformat()
  limiter=state/'telegram-rate.json'
  limit=json.loads(limiter.read_text(encoding='utf-8')) if limiter.is_file() else {'day':day,'count':0,'last':0,'blocked_until':0}
  if seconds<limit['last']:raise AlertError('clock_regressed')
  if seconds<limit['blocked_until'] or (limit['last'] and seconds-limit['last']<interval) or (limit['day']==day and limit['count']>=daily):
   return {'status':'RATE_LIMITED','receipt_confirmed':False}
  attempt.mkdir(mode=0o700)
  file=attempt/'result.json';record={'status':'UNCERTAIN','request_id':request_id,'payload_hash':digest,'timestamp':timestamp,'receipt_confirmed':False}
  save(file,record)
  limit.update(day=day,count=(limit['count'] if limit['day']==day else 0)+1,last=seconds)
  save(limiter,limit) # reserve before provider; ambiguous sends still consume limit
  try:
   status,response=send(token,body,timeout)
   if isinstance(response,dict) and response.get('ok') is False and type(response.get('error_code')) is int:
    status=response['error_code']
   record['http_status']=int(status)
   if status==200 and isinstance(response,dict) and response.get('ok') is True:
    result=response.get('result',{});mid=result.get('message_id');rid=result.get('chat',{}).get('id')
    if type(mid) is int and mid>0 and str(rid)==chat:record.update(status='ACCEPTED',provider_message_id=mid)
   elif status in (400,401,403,404,409,422,429):
    record['status']='REJECTED'
    if status==429:
     retry=response.get('parameters',{}).get('retry_after',interval)
     if type(retry) is not int or retry<0:retry=interval
     limit['blocked_until']=seconds+max(interval,retry);save(limiter,limit)
  except Exception:record['status']='UNCERTAIN'
  save(file,record)
  return record
 finally:lock.rmdir()

def notifier(state,env=None,authorized=False,send=transport):
 """Existing backup notify hook: False on failure, never raises into backup job."""
 def notify(event):
  try:
   identifier=event.get('request_id')
   if not identifier:
    if not event.get('backup_id'):return False  # watchdog must supply durable event ID
    identifier=hashlib.sha256((event['code']+':'+event['backup_id']).encode()).hexdigest()[:32]
   file=Path(state)/('telegram-'+identifier)/'result.json'
   stamp=json.loads(file.read_text(encoding='utf-8'))['timestamp'] if file.is_file() else datetime.now(timezone.utc).isoformat()
   result=send_once(event['code'],event.get('backup_id'),stamp,identifier,state,env=env,authorized=authorized,send=send)
   return result['status']=='ACCEPTED'  # transport acceptance, NOT human receipt
  except Exception:return False
 return notify
