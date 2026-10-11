// Integrated browser + real HTTP + PostgreSQL + private media; no response mocks.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.S05_E2E_URL;
const container = process.env.S05_E2E_APP;
const evidence = process.env.S05_E2E_EVIDENCE;
assert.equal(process.env.S05_E2E_ISOLATED,'1');
assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);
assert.match(container,/^fluxio-s05-e2e-app-[a-f0-9]+$/);
const results=[];
const fixture=(action,id)=>JSON.parse(execFileSync('docker',['exec','-w','/tmp/s05-e2e',container,
  'python','-m','tests.e2e.s05_fixture',action,...(id?[id]:[])],{encoding:'utf8'}));
const pass=(id)=>{results.push({id,status:'PASS'});console.log(id+' PASS');};
const check=(condition)=>assert.ok(condition,'S05 integrated assertion failed');
const headers={Origin:base};
(async()=>{
 const browser=await chromium.launch({headless:true});
 let contexts=[];
 try{
  const errors=[],external=[];
  const context=async()=>{
   const c=await browser.newContext({viewport:{width:390,height:844},timezoneId:'America/Santiago'});contexts.push(c);
   // Block external egress only. Every localhost request reaches the actual server.
   await c.route('**/*',route=>{
    const url=new URL(route.request().url());
    if(url.origin!==base && !['data:','blob:'].includes(url.protocol)){external.push('external_request');return route.abort();}
    return route.continue();
   });
   return c;
  };
  const owner=await context(),other=await context(),anon=await context();
  const page=await owner.newPage();page.on('pageerror',()=>errors.push('browser_error'));
  await page.goto(base+'/login');
  await page.locator('#login-form').getByLabel('Usuario',{exact:true}).fill('s05-owner');
  await page.locator('#login-form').getByLabel('Contraseña',{exact:true}).fill('s05-synthetic-only');
  await page.getByRole('button',{name:'Entrar',exact:true}).click();
  await page.waitForURL(url=>url.pathname!='/login');
  const login=await other.request.post(base+'/api/auth/login',{headers,data:{username:'s05-other',password:'s05-synthetic-only'}});
  assert.equal(login.status(),200);
  await page.goto(base+'/training/new');
  await page.getByLabel('Foto de la pizarra').setInputFiles({name:'synthetic.png',mimeType:'image/png',buffer:Buffer.from(fixture('photo').png,'base64')});
  await page.getByText('Foto lista.',{exact:false}).waitFor();
  await page.getByLabel('Descripción del entrenamiento').fill('Synthetic manual workout');
  await page.getByRole('button',{name:'Completar manualmente',exact:true}).click();
  await page.locator('[name=title]').fill('Synthetic S05 workout');
  await page.getByRole('button',{name:'Guardar entrenamiento',exact:true}).click();
  await page.waitForURL(base+'/training');
  await page.locator('.weekly-compact-metrics dd').first().filter({hasText:'1'}).waitFor();
  const sessions=await (await owner.request.get(base+'/api/training-sessions')).json();
  assert.equal(sessions.items.length,1);const item=sessions.items[0];check(item.source_image_id);
  let audit=fixture('audit');assert.equal(audit.sessions,1);assert.equal(audit.shares,0);assert.equal(audit.images,1);check(audit.private_files_present);
  pass('S05-E01-save-private');

  const sheet=page.getByRole('dialog',{name:'Compartir esta semana'});
  const open=async()=>{await page.locator('.weekly-share-trigger').click();await sheet.waitFor();};
  await open();check(!(await sheet.getByRole('checkbox').isChecked()));
  await sheet.getByRole('button',{name:'Crear enlace para compartir',exact:true}).click();
  assert.equal(fixture('audit').shares,0);
  const rejected=await owner.request.post(base+'/api/training-week/shares',{headers,data:{consent:false,consent_version:'weekly-live-v1',request_id:crypto.randomUUID()}});
  assert.equal(rejected.status(),422);
  await sheet.getByRole('checkbox').check();
  await sheet.getByRole('button',{name:'Cancelar publicación',exact:true}).click();
  assert.equal(fixture('audit').shares,0);pass('S05-E03-reject-consent');

  let consentRequest;
  page.on('request',request=>{if(request.method()==='POST' && new URL(request.url()).pathname==='/api/training-week/shares')consentRequest=request.postDataJSON();});
  await open();check(!(await sheet.getByRole('checkbox').isChecked()));
  const notice=await sheet.locator('.weekly-sheet-hint').first().textContent();
  for(const term of ['después','fotografías','notas','revocarlo'])check(notice.includes(term));
  await sheet.getByRole('checkbox').check();
  await sheet.getByRole('button',{name:'Crear enlace para compartir',exact:true}).dblclick();
  const urlInput=sheet.getByLabel('Enlace para compartir',{exact:true});await urlInput.waitFor();
  const sharedUrl=await urlInput.inputValue();
  check(new URL(sharedUrl).origin===base);check(consentRequest.consent===true);
  audit=fixture('audit');assert.equal(audit.shares,1);check(audit.consents_valid);
  const publicPage=await anon.newPage();assert.equal((await publicPage.goto(sharedUrl)).status(),200);
  await publicPage.getByRole('heading',{name:'Tu semana en movimiento'}).waitFor();
  await publicPage.waitForFunction(()=>document.images.length>0 && [...document.images].every(i=>i.complete&&i.naturalWidth>0));
  const photoUrl=sharedUrl+'/images/'+item.source_image_id;
  assert.equal((await anon.request.get(photoUrl)).status(),200);
  pass('S05-E02-explicit-consent');

  const duplicateResults=await page.evaluate(async body=>Promise.all([1,2].map(async()=>{
   const r=await fetch('/api/training-week/shares',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
   return {status:r.status,body:await r.json()};
  })),consentRequest);
  for(const r of duplicateResults){assert.equal(r.status,201);assert.equal(r.body.already_created,true);assert.equal(r.body.path,null);}
  assert.equal(fixture('audit').shares,1);pass('S05-E09-duplicate-publication');

  for(const url of ['/api/training-sessions/'+item.id,'/api/training-sessions/images/'+item.source_image_id]){
   assert.equal((await other.request.get(base+url)).status(),404);
   assert.equal((await anon.request.get(base+url)).status(),401);
  }
  const foreignRevoke=await other.request.delete(base+'/api/training-week/shares/'+audit.share_ids[0],{headers});
  assert.equal(foreignRevoke.status(),404);
  const foreignShare=await other.request.post(base+'/api/training-week/shares',{headers,data:{consent:true,consent_version:'weekly-live-v1',request_id:crypto.randomUUID(),athlete_id:'00000000-0000-4000-8000-000000000101'}});
  assert.equal(foreignShare.status(),422);
  assert.equal((await (await other.request.get(base+'/api/training-sessions')).json()).items.length,0);
  assert.equal((await (await other.request.get(base+'/api/training-week')).json()).session_count,0);
  pass('S05-E08-ownership');

  // Capture private journal only after closing token-bearing share controls.
  await sheet.getByRole('button',{name:'Cerrar compartir semana',exact:true}).click();
  await page.screenshot({path:path.join(evidence,'journal-private.png'),fullPage:false});
  await open();
  await sheet.getByRole('button',{name:'Revocar enlaces de esta semana',exact:true}).click();
  await sheet.getByText('Los enlaces de esta semana ya no permiten acceder.',{exact:true}).waitFor();
  assert.equal((await publicPage.goto(sharedUrl)).status(),404);pass('S05-E04-revoke-html');
  assert.equal((await anon.request.get(photoUrl)).status(),404);pass('S05-E05-revoke-photo');
  await sheet.getByRole('button',{name:'Cerrar compartir semana',exact:true}).click();

  const createUI=async()=>{
   await open();await sheet.getByRole('checkbox').check();
   const responsePromise=page.waitForResponse(r=>r.request().method()==='POST' && new URL(r.url()).pathname==='/api/training-week/shares');
   await sheet.getByRole('button',{name:'Crear enlace para compartir',exact:true}).click();
   const response=await responsePromise;assert.equal(response.status(),201);
   const created=await response.json();check(created.path);
   const url=base+created.path;
   const input=sheet.getByLabel('Enlace para compartir',{exact:true});
   await page.waitForFunction(expected=>{
     const inputs=[...document.querySelectorAll('input[readonly]')];
     return inputs.some(i=>i.value===expected);
   },url);
   assert.equal(await input.inputValue(),url);
   await sheet.getByRole('button',{name:'Cerrar compartir semana',exact:true}).click();
   return {url,id:created.id};
  };
  const expired=await createUI();assert.equal((await anon.request.get(expired.url)).status(),200);
  fixture('expire',expired.id);
  assert.equal((await publicPage.goto(expired.url)).status(),404);
  assert.equal((await anon.request.get(expired.url+'/images/'+item.source_image_id)).status(),404);
  pass('S05-E06-expired');
  const disabled=await createUI();assert.equal((await anon.request.get(disabled.url)).status(),200);
  fixture('deactivate');
  assert.equal((await publicPage.goto(disabled.url)).status(),404);
  assert.equal((await anon.request.get(disabled.url+'/images/'+item.source_image_id)).status(),404);
  assert.equal((await owner.request.get(base+'/api/training-sessions')).status(),401);
  pass('S05-E07-inactive');
  audit=fixture('audit');assert.equal(audit.sessions,1);assert.equal(audit.images,1);check(audit.private_files_present);
  assert.equal(audit.provider_operations,0);assert.equal(audit.inbox,0);assert.equal(audit.outbox,0);
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  fs.writeFileSync(path.join(evidence,'results.json'),JSON.stringify({status:'PASS',cases:results,audit,browser_errors:0,external_requests:0},null,2));
  console.log('S05 integrated PASS: nine required cases; real browser/server/database/storage; no providers.');
 }finally{for(const context of contexts)await context.close();await browser.close();}
})().catch(error=>{
 fs.writeFileSync(path.join(evidence,'results.json'),JSON.stringify({status:'FAIL',cases:results,error_code:'integrated_assertion_or_environment_failure',error_type:error.name,assertion_actual:typeof error.actual==='number'?error.actual:null,assertion_expected:typeof error.expected==='number'?error.expected:null,fixture_line:Number((error.stack||'').match(/s05-integrated\.cjs:(\d+):/)?.[1]||0)},null,2));
 console.error('S05 integrated FAIL; private URLs, credentials and payloads suppressed.');process.exitCode=1;
});
