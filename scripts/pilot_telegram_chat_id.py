"""Manual getUpdates discovery; never prints token, chat ID, URL or payload."""
import argparse,getpass,json,os,urllib.request
from pathlib import Path
from pilot_resend_alerts import NoRedirect

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
 try:
  token=os.environ.get('TELEGRAM_BOT_TOKEN') or getpass.getpass('Token Telegram (entrada oculta): ')
  import re
  if not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]{20,}',token):raise ValueError()
  output=Path(args.output)
  if not output.is_absolute() or not output.parent.is_dir() or output.exists():raise ValueError()
  req=urllib.request.Request('https://api.telegram.org/bot'+token+'/getUpdates',data=b'{"timeout":0,"limit":100}',method='POST',headers={'Content-Type':'application/json'})
  with urllib.request.build_opener(NoRedirect).open(req,timeout=10) as response:
   body=json.loads(response.read(262144))
  if body.get('ok') is not True:raise ValueError()
  chats={m['chat']['id'] for update in body.get('result',[]) for m in [update.get('message',{})] if m.get('chat',{}).get('type')=='private' and type(m['chat'].get('id')) is int}
  if len(chats)!=1:
   print('BLOCKED: se requiere exactamente un chat privado identificable; no se muestran datos.');return 1
  # Manual helper only; no offset/ack, deleteWebhook or sendMessage calls.
  with output.open('x',encoding='utf-8') as stream:
   os.chmod(output,0o600);stream.write('TELEGRAM_CHAT_ID='+str(next(iter(chats)))+'\n')
  print('CHAT_ID guardado en el archivo privado indicado. Confirma que corresponde a tu chat; no se envió mensaje.');return 0
 except Exception:
  print('BLOCKED: no se pudo obtener el Chat ID; token/URL/respuesta ocultos.');return 1

if __name__=='__main__':raise SystemExit(main())
