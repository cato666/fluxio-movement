"""No network/real email or credentials; Resend transport is always injected."""
import tempfile,unittest,json,urllib.error
from pathlib import Path
import pilot_resend_alerts as alerts

class ResendTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.state=Path(self.tmp.name);self.calls=[]
  self.env={'BACKUP_ALERTS_ENABLED':'true','BACKUP_ALERT_DOMAIN_VERIFIED':'true','RESEND_API_KEY':'synthetic-only','BACKUP_ALERT_FROM':'backup@example.invalid','BACKUP_ALERT_TO':'admin@example.invalid'}
 def sender(self,body,key,request):self.calls.append(body);return 200,{'id':'00000000-0000-4000-8000-000000000001'}
 def send(self,**kw):
  args=dict(code='BACKUP_ALERT_TEST',backup_id=None,timestamp='2026-10-11T12:00:00+00:00',request_id='a'*32,state=self.state,env=self.env,authorized=True,send=self.sender);args.update(kw);return alerts.send_once(**args)
 def test_redirects_not_followed(self):
  self.assertIsNone(alerts.NoRedirect().redirect_request(None,None,302,None,None,None))
 def test_disabled_without_authorization(self):
  with self.assertRaises(alerts.AlertError):self.send(authorized=False)
  self.assertEqual(self.calls,[])
 def test_environment_disabled(self):
  self.env['BACKUP_ALERTS_ENABLED']='false'
  with self.assertRaises(alerts.AlertError):self.send()
 def test_missing_key(self):
  self.env.pop('RESEND_API_KEY')
  with self.assertRaises(alerts.AlertError):self.send()
 def test_unverified_domain(self):
  self.env['BACKUP_ALERT_DOMAIN_VERIFIED']='false'
  with self.assertRaises(alerts.AlertError):self.send()
 def test_acceptance_is_not_receipt(self):
  r=self.send();self.assertEqual(r['status'],'ACCEPTED');self.assertFalse(r['receipt_confirmed'])
 def test_duplicate_does_not_send_again(self):
  self.send();self.send();self.assertEqual(len(self.calls),1)
 def test_changed_payload_conflict(self):
  self.send()
  with self.assertRaises(alerts.AlertError):self.send(code='BACKUP_FAILED')
 def test_timeout_stays_uncertain_without_retry(self):
  calls=[]
  def fail(*args):calls.append(1);raise TimeoutError('private provider secret')
  r=self.send(send=fail);self.assertEqual(r['status'],'UNCERTAIN');self.send();self.assertEqual(len(calls),1);self.assertEqual(self.calls,[])
 def test_429_is_not_automatically_retried(self):
  def fail(*args):raise urllib.error.HTTPError('https://api.resend.com/emails',429,'private body',None,None)
  r=self.send(send=fail);self.assertEqual(r['status'],'REJECTED');self.send();self.assertEqual(self.calls,[])
 def test_5xx_uncertain(self):
  def fail(*args):raise urllib.error.HTTPError('https://api.resend.com/emails',503,'secret',None,None)
  self.assertEqual(self.send(send=fail)['status'],'UNCERTAIN')
 def test_malformed_success_uncertain(self):self.assertEqual(self.send(send=lambda *args:(200,{'id':'bad'}))['status'],'UNCERTAIN')
 def test_crash_marker_no_replay(self):
  (self.state/('a'*32)).mkdir();self.assertEqual(self.send()['status'],'UNCERTAIN');self.assertEqual(self.calls,[])
 def test_injected_content_rejected(self):
  with self.assertRaises(alerts.AlertError):self.send(backup_id='private training content')
 def test_header_injection_rejected(self):
  self.env['BACKUP_ALERT_FROM']='x@example.invalid\nBcc: other@example.invalid'
  with self.assertRaises(alerts.AlertError):self.send()
 def test_no_credentials_addresses_in_record(self):
  record=json.dumps(self.send());self.assertNotIn('synthetic-only',record);self.assertNotIn('example.invalid',record)

if __name__=='__main__':unittest.main()
