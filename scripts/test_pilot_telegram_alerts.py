import tempfile,unittest,json,io,contextlib
from unittest.mock import patch
import pilot_telegram_chat_id as helper
from pathlib import Path
from datetime import datetime,timezone,timedelta
from concurrent.futures import ThreadPoolExecutor
import pilot_telegram_alerts as tg
import pilot_backup_ops as ops

class TelegramTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.state=Path(self.tmp.name);self.calls=[];self.now=datetime.now(timezone.utc)
  self.env={'TELEGRAM_BOT_TOKEN':'123456:'+('x'*32),'TELEGRAM_CHAT_ID':'123456789','TELEGRAM_ALERTS_ENABLED':'true'}
 def transport(self,token,body,timeout):self.calls.append(body);return 200,{'ok':True,'result':{'message_id':1,'chat':{'id':123456789}}}
 def send(self,**changes):
  args=dict(code='BACKUP_ALERT_TEST',backup_id=None,timestamp=self.now.isoformat(),request_id='a'*32,state=self.state,env=self.env,authorized=True,send=self.transport,now=self.now);args.update(changes);return tg.send_once(**args)
 def test_disabled(self):
  with self.assertRaises(tg.AlertError):self.send(authorized=False)
  self.assertEqual(self.calls,[])
 def test_env_disabled(self):
  self.env['TELEGRAM_ALERTS_ENABLED']='false'
  with self.assertRaises(tg.AlertError):self.send()
 def test_missing_token(self):
  self.env.pop('TELEGRAM_BOT_TOKEN')
  with self.assertRaises(tg.AlertError):self.send()
 def test_invalid_chat(self):
  self.env['TELEGRAM_CHAT_ID']='@public'
  with self.assertRaises(tg.AlertError):self.send()
 def test_success_not_receipt(self):
  r=self.send();self.assertEqual(r['status'],'ACCEPTED');self.assertFalse(r['receipt_confirmed'])
 def test_duplicate(self):self.send();self.send();self.assertEqual(len(self.calls),1)
 def test_changed_payload(self):
  self.send()
  with self.assertRaises(tg.AlertError):self.send(code='BACKUP_FAILED')
 def test_no_sensitive_content_in_logs(self):
  r=self.send();record=json.dumps(r);self.assertNotIn(self.env['TELEGRAM_BOT_TOKEN'],record);self.assertNotIn(self.env['TELEGRAM_CHAT_ID'],record);self.assertNotIn('Gastón',self.calls[0]['text'])
 def test_timeout_uncertain_no_retry(self):
  def fail(*args):raise TimeoutError('token private URL')
  self.assertEqual(self.send(send=fail)['status'],'UNCERTAIN');self.send();self.assertEqual(self.calls,[])
 def test_json_error_code(self):self.assertEqual(self.send(send=lambda *a:(200,{'ok':False,'error_code':403}))['status'],'REJECTED')
 def test_5xx_uncertain(self):self.assertEqual(self.send(send=lambda *a:(503,{'description':'private'}))['status'],'UNCERTAIN')
 def test_403_rejected(self):self.assertEqual(self.send(send=lambda *a:(403,{'ok':False}))['status'],'REJECTED')
 def test_429_cooldown(self):
  self.send(send=lambda *a:(429,{'parameters':{'retry_after':120}}))
  self.assertEqual(self.send(request_id='b'*32,now=self.now+timedelta(seconds=61))['status'],'RATE_LIMITED');self.assertEqual(self.calls,[])
 def test_min_interval(self):
  self.send();self.assertEqual(self.send(request_id='b'*32)['status'],'RATE_LIMITED')
 def test_interval_recovers(self):
  self.send();self.assertEqual(self.send(request_id='b'*32,now=self.now+timedelta(seconds=60))['status'],'ACCEPTED')
 def test_daily_limit(self):
  self.env['TELEGRAM_ALERT_DAILY_LIMIT']='1';self.send();self.assertEqual(self.send(request_id='b'*32,now=self.now+timedelta(seconds=61))['status'],'RATE_LIMITED')
 def test_daily_reset(self):
  self.env['TELEGRAM_ALERT_DAILY_LIMIT']='1';self.send();self.assertEqual(self.send(request_id='b'*32,now=self.now+timedelta(days=1))['status'],'ACCEPTED')
 def test_wrong_chat_in_response(self):self.assertEqual(self.send(send=lambda *a:(200,{'ok':True,'result':{'message_id':1,'chat':{'id':999}}}))['status'],'UNCERTAIN')
 def test_malformed_success(self):self.assertEqual(self.send(send=lambda *a:(200,{'ok':True}))['status'],'UNCERTAIN')
 def test_busy(self):
  (self.state/'telegram.lock').mkdir();self.assertEqual(self.send()['status'],'BUSY');self.assertEqual(self.calls,[])
 def test_concurrent_limit(self):
  with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda n:self.send(request_id=n*32),['a','b']))
  self.assertEqual(len(self.calls),1)
 def test_unknown_code(self):
  with self.assertRaises(tg.AlertError):self.send(code='private workout text')
 def test_limits_validated(self):
  self.env['TELEGRAM_ALERT_TIMEOUT_SECONDS']='0'
  with self.assertRaises(tg.AlertError):self.send()
 def test_worker_restore_codes(self):
  for code in ['WORKER_DOWN','WORKER_STALE','RESTORE_FAILED','RESTORE_COMPLETE','CRITICAL_ERROR']:self.assertIn(code,tg.text(code,None,self.now.isoformat()))
 def test_callback_duplicate(self):
  notify=tg.notifier(self.state,self.env,True,self.transport);e={'code':'BACKUP_FAILED','backup_id':'b'*32};self.assertTrue(notify(e));self.assertTrue(notify(e));self.assertEqual(len(self.calls),1)
 def test_notify_failure_does_not_escape_backup(self):
  notify=tg.notifier(self.state,self.env,True,lambda *a:(_ for _ in ()).throw(TimeoutError('secret')))
  def collect():raise RuntimeError('synthetic backup failure')
  r=ops.run_job(self.state/'backup','daily',collect,lambda *a:None,lambda *a:None,b'x'*32,notify)
  self.assertEqual(r['status'],'INCOMPLETE');self.assertEqual(r['alert_delivery'],'FAILED')
 def test_callback_disabled_not_exception(self):self.assertFalse(tg.notifier(self.state,self.env,False,self.transport)({'code':'BACKUP_FAILED','backup_id':'b'*32}))


class ChatDiscoveryTests(unittest.TestCase):
 def run_helper(self,body):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);path=Path(temp.name)/'chat.env';output=io.StringIO()
  class Opener:
   def open(self,*args,**kwargs):return io.BytesIO(json.dumps(body).encode())
  with patch('sys.argv',['helper','--output',str(path)]),patch.dict('os.environ',{'TELEGRAM_BOT_TOKEN':'123:'+('x'*32)}),patch.object(helper.urllib.request,'build_opener',return_value=Opener()),contextlib.redirect_stdout(output):
   code=helper.main()
  self.assertNotIn('123456789',output.getvalue());self.assertNotIn('x'*32,output.getvalue())
  return code,path
 def test_private_chat_saved_without_printing(self):
  code,path=self.run_helper({'ok':True,'result':[{'message':{'chat':{'id':123456789,'type':'private'},'text':'private message'}}]});self.assertEqual(code,0);self.assertEqual(path.read_text(),'TELEGRAM_CHAT_ID=123456789\n')
 def test_ambiguous_chat_blocks(self):
  code,path=self.run_helper({'ok':True,'result':[{'message':{'chat':{'id':n,'type':'private'}}} for n in [1,2]]});self.assertEqual(code,1);self.assertFalse(path.exists())
 def test_group_not_selected(self):
  code,path=self.run_helper({'ok':True,'result':[{'message':{'chat':{'id':-1,'type':'group'}}}]});self.assertEqual(code,1);self.assertFalse(path.exists())
 def test_provider_failure_redacted(self):
  code,path=self.run_helper({'ok':False,'description':'private token'});self.assertEqual(code,1);self.assertFalse(path.exists())

if __name__=='__main__':unittest.main()
