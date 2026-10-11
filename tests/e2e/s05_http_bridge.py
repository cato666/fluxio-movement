"""One real HTTP request over Docker stdin/stdout; fixed loopback target."""
import base64
import http.client
import json
import os
import sys

if os.environ.get('S05_E2E_ISOLATED') != '1':
    raise SystemExit('Isolation guard rejected HTTP bridge')
raw = sys.stdin.buffer.read(16*1024*1024 + 1)
if len(raw)>16*1024*1024:
    raise SystemExit('Bridge input exceeds limit')
request=json.loads(raw)
if request['method'] not in {'GET','HEAD','POST','PUT','PATCH','DELETE'} or not request['path'].startswith('/') or request['path'].startswith('//'):
    raise SystemExit('Bridge target rejected')
connection=http.client.HTTPConnection('127.0.0.1',8000,timeout=30)
connection.request(request['method'],request['path'],body=base64.b64decode(request['body']),headers=request['headers'])
response=connection.getresponse()
print(json.dumps({'status':response.status,'headers':response.getheaders(),'body':base64.b64encode(response.read()).decode()}))
connection.close()
