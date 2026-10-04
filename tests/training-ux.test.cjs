// Run with PLAYWRIGHT_MODULE pointing to Playwright when it is not installed locally.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const read = name => fs.readFileSync(require.resolve('../app/static/' + name), 'utf8');
const draft = {title:'AMRAP 12',workout:'10 thrusters, 12 burpees',result_text:'5 rondas',adaptations:'25 kg',rpe:8,questions:['¿Completaste las series?'],blocks:[{title:'Metcon',format:'amrap',prescription:'12 minutos',movements:[{name:'Thrusters',prescription:'10 · 30 kg'}]}]};
async function harness(run, options = {}) {
  const browser = await chromium.launch({headless:true,args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']});
  try {
    const context = await browser.newContext({permissions:['microphone'],viewport:{width:390,height:844},...options});
    const page = await context.newPage();
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.route('http://localhost:18767/**', route => route.fulfill({contentType:'text/html',body:'<main><section id="training-view"></section></main>'}));
    await page.goto('http://localhost:18767');
    await page.addStyleTag({content:read('styles.css')+read('training.css')+read('visual-v2.css')+read('weekly-expanded.css')});
    await page.addScriptTag({content:'function takeFlash(){return sessionStorage.getItem("flash")} function setFlash(v){sessionStorage.setItem("flash",v)}'});
    await page.addScriptTag({content:read('training-voice.js')});
    await page.addScriptTag({content:read('training.js')});
    await page.evaluate(()=>window.setupTraining('new'));
    await run(page, context);
    assert.deepEqual(errors,[]);
  } finally { await browser.close(); }
}
test('capture then manual review; optional context stays folded and return preserves the draft',()=>harness(async page=>{
  assert.equal(await page.locator('.training-form').isVisible(),false);
  await page.getByLabel('Descripción del entrenamiento').fill('5x5 sentadillas 60 kg');
  await page.getByRole('button',{name:'Completar manualmente'}).click();
  assert.equal(await page.locator('[name=workout]').inputValue(),'5x5 sentadillas 60 kg');
  assert.equal(await page.locator('.training-form').isVisible(),true);
  assert.equal(await page.locator('[name=adaptations]').isVisible(),false);
  await page.locator('[name=title]').fill('Fuerza');
  await page.getByRole('button',{name:'Volver a mi descripción'}).click();
  assert.equal(await page.getByLabel('Descripción del entrenamiento').inputValue(),'5x5 sentadillas 60 kg');
  await page.getByRole('button',{name:'Completar manualmente'}).click();
  assert.equal(await page.locator('[name=title]').inputValue(),'Fuerza');
}));
test('chat composer integrates labelled photo, microphone and interpretation on one mobile row',()=>harness(async page=>{
  const toolbar=page.locator('.training-composer .training-chat-toolbar');
  for(const name of ['Añadir foto de la pizarra','Dictar entrenamiento','Interpretar WOD']) assert.equal(await toolbar.getByRole('button',{name,exact:true}).count(),1);
  for(const width of [320,390,430]) {
    await page.setViewportSize({width,height:844});
    const positions=await toolbar.locator('button').evaluateAll(buttons=>buttons.map(button=>button.getBoundingClientRect().top));
    assert.ok(Math.max(...positions)-Math.min(...positions)<2);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  }
}));
test('new title defaults to training day/date; changing date updates only the default; AI preserves custom title',()=>harness(async page=>{
  await page.getByRole('button',{name:'Completar manualmente'}).click();
  assert.ok((await page.locator('[name=title]').inputValue()).length>10);
  await page.locator('[name=trained_on]').fill('2026-10-02');
  await page.locator('[name=trained_on]').dispatchEvent('change');
  assert.equal(await page.locator('[name=title]').inputValue(),'Viernes, 2 de octubre de 2026');
  await page.locator('[name=title]').fill('Mi sesión de fuerza');
  await page.locator('[name=trained_on]').fill('2026-10-01');
  await page.locator('[name=trained_on]').dispatchEvent('change');
  assert.equal(await page.locator('[name=title]').inputValue(),'Mi sesión de fuerza');
  await page.getByRole('button',{name:'Volver a mi descripción'}).click();
  await page.getByLabel('Descripción del entrenamiento').fill('AMRAP 12');
  await page.route('**/api/training-sessions/interpret',route=>route.fulfill({json:draft}));
  await page.getByRole('button',{name:'Interpretar WOD',exact:true}).click();
  await page.getByRole('heading',{name:'Revisa tu entrenamiento'}).waitFor();
  assert.equal(await page.locator('[name=title]').inputValue(),'Mi sesión de fuerza');
}));
test('AI draft reveals review, keeps text collapsed and opens incomplete required blocks on submit',()=>harness(async page=>{
  await page.route('**/api/training-sessions/interpret',route=>route.fulfill({json:draft}));
  await page.getByLabel('Descripción del entrenamiento').fill('AMRAP 12');
  await page.getByRole('button',{name:'Interpretar WOD',exact:true}).click();
  await page.getByRole('heading',{name:'Revisa tu entrenamiento'}).waitFor();
  assert.equal(await page.locator('[name=workout]').isVisible(),false);
  assert.equal(await page.locator('[name=adaptations]').isVisible(),true);
  assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Revisa tu entrenamiento');
  await page.locator('.training-blocks summary').click();
  await page.getByLabel('Nombre del bloque').fill('');
  await page.locator('.training-blocks summary').click();
  await page.getByRole('button',{name:'Guardar entrenamiento',exact:true}).click();
  assert.equal(await page.getByLabel('Nombre del bloque').isVisible(),true);
  assert.equal(await page.evaluate(()=>document.activeElement.validity.valid),false);
}));
test('failed save preserves source and payload; retry succeeds with feedback',()=>harness(async page=>{
  const bodies=[];let fail=true;
  await page.route('**/api/training-sessions',route=>{
    if(route.request().method()==='POST') {bodies.push(route.request().postDataJSON());return route.fulfill({status:fail?503:200,json:fail?{detail:'Servicio temporalmente no disponible.'}:{id:'saved'}});}
    return route.fulfill({json:{items:[]}});
  });
  await page.getByLabel('Descripción del entrenamiento').fill('5x5 sentadillas');
  await page.getByRole('button',{name:'Completar manualmente'}).click();
  await page.locator('[name=title]').fill('Fuerza');
  await page.getByRole('button',{name:'Guardar entrenamiento',exact:true}).click();
  await page.getByText('Tu borrador se conserva',{exact:false}).waitFor();
  assert.equal(await page.locator('[name=title]').inputValue(),'Fuerza');
  assert.equal(bodies[0].source_text,'5x5 sentadillas');assert.equal(bodies[0].rpe,null);
  fail=false;await page.getByRole('button',{name:'Guardar entrenamiento',exact:true}).click();
  await page.waitForURL('**/training');
  assert.deepEqual(bodies[0],bodies[1]);
  assert.match(await page.evaluate(()=>sessionStorage.getItem('flash')),/Entrenamiento guardado/);
}));
test('offline interpretation keeps capture editable and provides recovery',()=>harness(async page=>{
  await page.route('**/api/training-sessions/interpret',route=>route.abort('internetdisconnected'));
  await page.getByLabel('Descripción del entrenamiento').fill('AMRAP 12');
  await page.getByRole('button',{name:'Interpretar WOD',exact:true}).click();
  await page.getByText('Revisa tu conexión',{exact:false}).waitFor();
  assert.equal(await page.getByLabel('Descripción del entrenamiento').inputValue(),'AMRAP 12');
  assert.equal(await page.getByRole('button',{name:'Completar manualmente'}).isEnabled(),true);
}));
test('320–430px and desktop: no overflow; accessible controls; keyboard and reduced motion',()=>harness(async page=>{
  await page.getByRole('button',{name:'Completar manualmente'}).click();
  for(const width of [320,390,430,768,1440]) {
    await page.setViewportSize({width,height:900});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    assert.ok(await page.locator('[name=title]').evaluate(el=>parseFloat(getComputedStyle(el).fontSize)>=16));
    assert.ok(await page.getByRole('button',{name:'Guardar entrenamiento',exact:true}).evaluate(el=>el.getBoundingClientRect().height>=44));
  }
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.locator('.training-save-actions').evaluate(el=>getComputedStyle(el).position),'sticky');
  await page.evaluate(()=>document.body.classList.add('mobile-keyboard-open'));
  assert.equal(await page.locator('.training-save-actions').evaluate(el=>getComputedStyle(el).position),'static');
  await page.emulateMedia({reducedMotion:'reduce'});
  assert.equal(await page.getByRole('button',{name:'Guardar entrenamiento',exact:true}).evaluate(el=>getComputedStyle(el).transitionDuration),'0s');
}));
test('list has actionable empty and recoverable error states',()=>harness(async page=>{
  await page.route('**/api/training-sessions',route=>route.fulfill({json:{items:[]}}));
  await page.evaluate(()=>window.setupTraining());
  assert.equal(await page.getByRole('link',{name:'Registrar mi primer entrenamiento'}).getAttribute('href'),'/training/new');
  await page.route('**/api/training-sessions',route=>route.fulfill({status:403,json:{detail:'Acceso rechazado.'}}));
  await page.evaluate(()=>window.setupTraining());
  assert.equal(await page.getByRole('button',{name:'Reintentar'}).isVisible(),true);
  assert.equal(await page.getByText('No tienes permiso',{exact:false}).isVisible(),true);
  await page.route('**/api/training-sessions',route=>route.fulfill({status:401,json:{detail:'Not authenticated'}}));
  await page.evaluate(()=>window.setupTraining());
  const login=page.getByRole('link',{name:'Iniciar sesión en otra pestaña'});
  assert.equal(await login.getAttribute('target'),'_blank');
  assert.match(await login.getAttribute('href'),/^\/login\?next=/);
}));
test('processing shows immediate feedback and prevents repeated interpretation',()=>harness(async page=>{
  let release, requests=0;
  const pending=new Promise(resolve=>{release=resolve});
  await page.route('**/api/training-sessions/interpret',async route=>{requests++;await pending;await route.fulfill({json:draft});});
  await page.getByLabel('Descripción del entrenamiento').fill('AMRAP 12');
  await page.getByRole('button',{name:'Interpretar WOD',exact:true}).click();
  await page.getByRole('button',{name:'Interpretando…',exact:true}).waitFor();
  assert.equal(await page.getByLabel('Descripción del entrenamiento').isEnabled(),false);
  assert.equal(await page.locator('.training-layout').getAttribute('aria-busy'),'true');
  await page.evaluate(()=>document.querySelector('.training-capture-actions button:last-child').onclick());
  release();await page.getByRole('heading',{name:'Revisa tu entrenamiento'}).waitFor();
  assert.equal(requests,1);
}));
test('voice failure preserves recording; retry appends editable text; denied microphone unlocks capture',()=>harness(async page=>{
  await page.getByLabel('Descripción del entrenamiento').fill('AMRAP 12');
  await page.getByRole('button',{name:'Dictar entrenamiento'}).click();
  await page.getByText('Grabando. Termina la grabación',{exact:false}).waitFor();
  await page.waitForTimeout(1200);
  assert.equal(await page.locator('.training-recording-time').getAttribute('aria-hidden'),'true');
  await page.getByRole('button',{name:'Terminar grabación'}).click();
  await page.getByText('Grabación lista.',{exact:false}).waitFor();
  await page.route('**/api/training-sessions/transcribe',route=>route.fulfill({status:502,json:{detail:'No se pudo transcribir.'}}));
  await page.getByRole('button',{name:'Transcribir audio',exact:true}).click();
  await page.getByText('La grabación se conserva',{exact:false}).waitFor();
  assert.equal(await page.locator('.training-voice audio').isVisible(),true);
  await page.route('**/api/training-sessions/transcribe',route=>route.fulfill({json:{text:'Hice cinco rondas.'}}));
  await page.getByRole('button',{name:'Transcribir audio',exact:true}).click();
  await page.getByText('Texto agregado.',{exact:false}).waitFor();
  assert.equal(await page.getByLabel('Descripción del entrenamiento').inputValue(),'AMRAP 12\n\nHice cinco rondas.');
  assert.equal(await page.locator('.training-voice audio').isVisible(),false);
  await page.evaluate(()=>{navigator.mediaDevices.getUserMedia=()=>Promise.reject(new DOMException('Denied','NotAllowedError'));});
  await page.getByRole('button',{name:'Dictar entrenamiento'}).click();
  await page.getByText('No se permitió el micrófono.',{exact:false}).waitFor();
  assert.equal(await page.getByLabel('Descripción del entrenamiento').isEnabled(),true);
}));
test('photo capture uses the existing upload and preserves its reference in the saved payload',()=>harness(async page=>{
  let upload=false, payload;
  await page.route('**/api/training-sessions/images',route=>{
    upload=route.request().method()==='POST'&&route.request().headers()['content-type'].includes('multipart/form-data');
    return route.fulfill({json:{id:'photo-id',url:'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aK2kAAAAASUVORK5CYII='}});
  });
  await page.getByLabel('Foto de la pizarra').setInputFiles({name:'pizarra.png',mimeType:'image/png',buffer:Buffer.from('fixture')});
  await page.getByText('Foto lista.',{exact:false}).waitFor();assert.equal(upload,true);
  assert.equal(await page.locator('.training-photo').isVisible(),true);
  await page.route('**/api/training-sessions/interpret',route=>route.fulfill({json:draft}));
  await page.getByRole('button',{name:'Interpretar WOD',exact:true}).click();
  await page.getByRole('heading',{name:'Revisa tu entrenamiento'}).waitFor();
  await page.route('**/api/training-sessions',route=>{payload=route.request().postDataJSON();return route.fulfill({json:{id:'saved'}})});
  await page.getByRole('button',{name:'Guardar entrenamiento',exact:true}).click();await page.waitForURL('**/training');
  assert.equal(payload.source_image_id,'photo-id');assert.deepEqual(payload.blocks,draft.blocks);
}));
test('existing session opens as a note, preserves edits between views and uses the unchanged PUT route',()=>harness(async page=>{
  let request;
  await page.route('**/api/training-sessions/session-id',route=>{
    if(route.request().method()==='PUT'){request=route.request();return route.fulfill({json:{id:'session-id'}});}
    return route.fulfill({json:{...draft,id:'session-id',trained_on:'2026-10-01',source_text:'Mi WOD',video_links:[],source_image_id:null}});
  });
  await page.evaluate(()=>window.setupTraining('session-id'));
  assert.equal(await page.locator('.training-form').isVisible(),false);
  assert.equal(await page.locator('.training-note').isVisible(),true);
  assert.equal(await page.locator('.training-note').getByRole('heading',{name:'AMRAP 12'}).isVisible(),true);
  assert.equal(await page.locator('.training-note').getByText('5 rondas',{exact:true}).isVisible(),true);
  await page.getByRole('button',{name:'Editar entrenamiento'}).click();
  assert.equal(await page.locator('.training-form').isVisible(),true);
  await page.locator('[name=title]').fill('AMRAP confirmado');
  await page.getByRole('button',{name:'Volver al resumen'}).click();
  assert.equal(await page.getByText('Tienes cambios sin guardar en el detalle.').isVisible(),true);
  assert.equal(await page.locator('.training-note').getByRole('heading',{name:'AMRAP 12'}).isVisible(),true);
  await page.getByRole('button',{name:'Editar entrenamiento'}).click();
  assert.equal(await page.locator('[name=title]').inputValue(),'AMRAP confirmado');
  await page.getByRole('button',{name:'Guardar cambios',exact:true}).click();await page.waitForURL('**/training');
  assert.equal(request.method(),'PUT');assert.equal(request.postDataJSON().title,'AMRAP confirmado');
  assert.equal(request.postDataJSON().source_text,'Mi WOD');
}));
test('saved note supports long content, absent optional data and 320–430px',()=>harness(async page=>{
  const workout='Sentadilla 5x5 · 60 kg\n'.repeat(80);
  await page.route('**/api/training-sessions/long-session',route=>route.fulfill({json:{id:'long-session',title:'Un entrenamiento con nombre largo '.repeat(5),trained_on:'2026-10-01',workout,result_text:'',adaptations:'',rpe:null,blocks:[],video_links:[],source_text:''}}));
  await page.evaluate(()=>window.setupTraining('long-session'));
  assert.equal(await page.getByText('Todavía no anotaste tu resultado.',{exact:false}).isVisible(),true);
  assert.equal(await page.locator('.training-note-meta').count(),0);
  const more=page.getByText('Leer lo que entrené completo',{exact:true});
  await more.click();assert.equal(await page.locator('.training-note details p').textContent(),workout);
  for(const width of [320,390,430,768,1440]){
    await page.setViewportSize({width,height:900});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    assert.ok(await page.getByRole('button',{name:'Editar entrenamiento'}).evaluate(el=>el.getBoundingClientRect().height>=44));
  }
  await page.emulateMedia({reducedMotion:'reduce'});
  assert.equal(await page.getByRole('button',{name:'Editar entrenamiento'}).evaluate(el=>getComputedStyle(el).transitionDuration),'0s');
}));
test('private thumbnails appear only for attached photos in list and note; missing image has a fallback',()=>harness(async page=>{
  const session={...draft,id:'photo-session',trained_on:'2026-10-01',source_image_id:'private-photo',video_links:[],source_text:''};
  await page.route('**/api/training-sessions/images/private-photo',route=>route.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aK2kAAAAASUVORK5CYII=','base64')}));
  await page.route('**/api/training-sessions',route=>route.fulfill({json:{items:[session,{...session,id:'no-photo',source_image_id:null}]}}));
  await page.evaluate(()=>window.setupTraining());
  assert.equal(await page.locator('.training-entry .training-thumbnail').count(),2);
  assert.equal(await page.locator('a.training-thumbnail').getAttribute('href'),'/training/photo-session');
  assert.equal(await page.getByRole('img',{name:'Entrenamiento sin foto',exact:true}).count(),1);
  const sizes=await page.locator('.training-entry .training-thumbnail').evaluateAll(nodes=>nodes.map(node=>[node.getBoundingClientRect().width,node.getBoundingClientRect().height]));
  assert.deepEqual(sizes[0],sizes[1]);
  for(const width of [320,390,430,1440]){
    await page.setViewportSize({width,height:900});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  }
  await page.route('**/api/training-sessions/photo-session',route=>route.fulfill({json:session}));
  await page.evaluate(()=>window.setupTraining('photo-session'));
  const thumbnail=page.locator('.training-note .training-thumbnail');
  assert.equal(await thumbnail.getAttribute('href'),'/api/training-sessions/images/private-photo');
  assert.equal(await thumbnail.getAttribute('target'),'_blank');
  await page.route('**/api/training-sessions/images/private-photo*',route=>route.fulfill({status:404}));
  await page.evaluate(()=>{document.querySelector('.training-note .training-thumbnail img').src+='?missing=1'});
  await page.getByText('Imagen no disponible',{exact:true}).waitFor();
  assert.equal(await thumbnail.getAttribute('href'),null);
}));
test('chronology, weekly counts and read-only blocks use stored data; reading and editing stay distinct',()=>harness(async page=>{
  const today=await page.evaluate(()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`});
  const title=await page.evaluate(date=>new Intl.DateTimeFormat('es-CL',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date(date+'T12:00:00')),today);
  const session={...draft,id:'chronology',trained_on:today,title,video_links:[{analysis_id:'linked',movement:'Thrusters',context:'Ronda 1'}],source_image_id:null};
  await page.route('**/api/training-week',r=>r.fulfill({json:{week_start:today,week_end:today,session_count:2,active_days:1,average_rpe:8,rpe_count:2,items:[session,session]}}));
  await page.route('**/api/training-week/shares?*',r=>r.fulfill({json:{items:[]}}));
  await page.route('**/api/training-sessions',r=>r.fulfill({json:{items:[session,{...session,id:'second'}, {...session,id:'old',trained_on:'2000-01-01',title:'Fuerza'}]}}));
  await page.evaluate(()=>window.setupTraining());
  assert.equal(await page.locator('.training-day').count(),2);
  assert.equal(await page.locator('.training-day').first().locator('article').count(),2);
  assert.deepEqual(await page.locator('.weekly-compact-metrics dd').allTextContents(),['2','1','8/10']);
  assert.equal(await page.locator('.training-entry-content > a').first().textContent(),'Metcon');
  const options = page.getByLabel('Opciones del entrenamiento',{exact:true}).first();
  assert.equal(await page.locator('.training-entry-actions').first().isVisible(),false);
  await options.press('Enter');
  assert.equal(await page.locator('.training-entry-actions').first().isVisible(),true);
  assert.equal(await page.locator('.training-entry-actions').first().getByRole('link',{name:'Editar entrenamiento'}).getAttribute('href'),'/training/chronology?edit=1');
  await options.press('Escape');
  assert.equal(await page.locator('.training-entry-actions').first().isVisible(),false);
  assert.equal(await options.evaluate(node=>node===document.activeElement),true);
  await options.click();
  await page.getByRole('heading',{name:'Mi bitácora',exact:true}).click();
  assert.equal(await page.locator('.training-entry-actions').first().isVisible(),false);
  for(const width of [320,390,430,768,1440]) {
    await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  }
  await page.screenshot({path:'.impeccable/training-evolution-list-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:'.impeccable/training-evolution-list-mobile.png',fullPage:true});
  await page.route('**/api/training-sessions/chronology',r=>r.fulfill({json:session}));
  await page.evaluate(()=>window.setupTraining('chronology'));
  assert.equal(await page.locator('.training-reading-blocks details').first().getAttribute('open'),'');
  assert.equal(await page.locator('.training-reading-blocks input').count(),0);
  assert.equal(await page.locator('.training-note a[href="/analyses/linked"]').count(),1);
  await page.screenshot({path:'.impeccable/training-evolution-detail-mobile.png',fullPage:true});
  await page.getByRole('button',{name:'Editar entrenamiento',exact:true}).click();
  assert.equal(await page.getByRole('heading',{name:'Editar entrenamiento',exact:true}).count(),1);
  assert.equal(await page.locator('[name=title]').inputValue(),title);
  await page.screenshot({path:'.impeccable/training-evolution-edit-mobile.png',fullPage:true});
  await page.evaluate(()=>{history.replaceState({},'', '/training/chronology?edit=1');return window.setupTraining('chronology')});
  assert.equal(await page.locator('.training-form').isVisible(),true);
  assert.equal(await page.locator('.training-note').isVisible(),false);
}));
test('delete confirms, preserves a failed session and prevents duplicate requests',()=>harness(async page=>{
  const session={...draft,id:'delete-session',trained_on:'2026-10-02',source_image_id:null,video_links:[]};
  let calls=0,fail=true,accept=false;
  await page.route('**/api/training-sessions',r=>r.fulfill({json:{items:[session]}}));
  await page.route('**/api/training-sessions/delete-session',r=>{calls++;return r.fulfill({status:fail?503:200,json:fail?{detail:'No disponible'}:{deleted:true}})});
  page.on('dialog',dialog=>accept?dialog.accept():dialog.dismiss());
  await page.evaluate(()=>window.setupTraining());
  await page.getByLabel('Opciones del entrenamiento',{exact:true}).click();
  await page.getByRole('button',{name:'Eliminar entrenamiento',exact:true}).click();assert.equal(calls,0);
  accept=true;await page.getByRole('button',{name:'Eliminar entrenamiento',exact:true}).click();
  await page.getByText('El entrenamiento sigue en esta pantalla',{exact:false}).waitFor();assert.equal(calls,1);assert.equal(await page.locator('.training-entry').count(),1);
  fail=false;await page.getByRole('button',{name:'Eliminar entrenamiento',exact:true}).dblclick();
  await page.waitForURL('**/training');assert.equal(calls,2);assert.match(await page.evaluate(()=>sessionStorage.getItem('flash')),/Entrenamiento eliminado/);
}));
test('saving confirmed session removes the separate audio leave warning; failed saves keep it',()=>harness(async page=>{
 await page.getByLabel('Descripción del entrenamiento').fill('Sentadilla 5x5');
 await page.getByRole('button',{name:'Dictar entrenamiento'}).click();
 await page.getByText('Grabando. Termina la grabación',{exact:false}).waitFor();await page.waitForTimeout(1200);
 await page.getByRole('button',{name:'Terminar grabación'}).click();await page.getByText('Grabación lista.',{exact:false}).waitFor();
 await page.getByRole('button',{name:'Completar manualmente'}).click();
 let fail=true;await page.route('**/api/training-sessions',r=>r.fulfill({status:fail?503:200,json:fail?{detail:'No disponible'}:{id:'saved'}}));
 await page.getByRole('button',{name:'Guardar entrenamiento',exact:true}).click();await page.getByText('Tu borrador se conserva',{exact:false}).waitFor();
 assert.equal(await page.evaluate(()=>{const e=new Event('beforeunload',{cancelable:true});window.dispatchEvent(e);return e.defaultPrevented}),true);
 const dialogs=[];page.on('dialog',async dialog=>{dialogs.push(dialog.type());await dialog.dismiss()});
 fail=false;await page.getByRole('button',{name:'Guardar entrenamiento',exact:true}).click();await page.waitForURL('**/training');assert.deepEqual(dialogs,[]);
}));

test('weekly expanded summary keeps navigation compact and share metadata persists across remount',()=>harness(async page=>{
 const item={...draft,id:'weekly-item',trained_on:'2026-10-02',source_image_id:null,video_links:[]};
 let shares=[{id:'persisted-one',expires_at:'2099-10-11T12:00:00Z'},{id:'persisted-two',expires_at:'2099-10-10T12:00:00Z'}];
 await page.route(/\/api\/training-week(?:\?|$)/,r=>r.fulfill({json:{week_start:'2026-09-28',week_end:'2026-10-04',session_count:1,active_days:1,average_rpe:8,rpe_count:1,items:[item]}}));
 await page.route('**/api/training-sessions',r=>r.fulfill({json:{items:[item]}}));
 await page.route('**/api/training-week/shares?*',r=>r.fulfill({json:{items:shares}}));
 await page.route('**/api/training-week/shares/persisted-one',r=>{shares=shares.filter(row=>row.id!=='persisted-one');return r.fulfill({json:{ok:true}})});
 await page.evaluate(()=>window.setupTraining());
 const summary=page.locator('.weekly-disclosure > summary');await summary.press('Enter');
 assert.equal(await page.locator('.weekly-session-row').getAttribute('href'),'/training/weekly-item');
 assert.equal(await page.getByRole('button',{name:'Crear enlace para compartir',exact:true}).isVisible(),false);
 const trigger=page.locator('.weekly-share-trigger');await trigger.press('Enter');
 const sheet=page.getByRole('dialog',{name:'Compartir esta semana'});assert.equal(await sheet.isVisible(),true);
 assert.equal(await sheet.locator('.weekly-link-row').count(),2);
 assert.equal(await sheet.getByRole('button',{name:'Copiar enlace',exact:true}).count(),0);
 await page.keyboard.press('Escape');assert.equal(await sheet.isVisible(),false);assert.equal(await trigger.evaluate(el=>el===document.activeElement),true);
 await page.evaluate(()=>window.setupTraining());await page.locator('.weekly-disclosure > summary').press('Enter');
 await page.locator('.weekly-share-trigger').press('Enter');assert.equal(await sheet.locator('.weekly-link-row').count(),2);
 await sheet.getByRole('button',{name:'Revocar enlace',exact:true}).first().click();await sheet.getByText('Enlace revocado. Ya no permite acceder.',{exact:true}).waitFor();assert.equal(await sheet.locator('.weekly-link-row').count(),1);
 await sheet.getByRole('button',{name:'Cerrar compartir semana'}).click();
 for(const width of [1440,768,430,390,320]){
  await page.setViewportSize({width,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  const tops=await page.locator('.weekly-navigation > .weekly-icon-button').evaluateAll(nodes=>nodes.map(el=>el.getBoundingClientRect().top));assert.ok(Math.max(...tops)-Math.min(...tops)<3);
  for(const size of await page.locator('.weekly-navigation').locator('button,summary').evaluateAll(nodes=>nodes.map(el=>el.getBoundingClientRect().height)))assert.ok(size>=44);
  await page.locator('.weekly-share-trigger').click();assert.equal(await sheet.evaluate(el=>el.scrollWidth<=el.clientWidth),true);await page.keyboard.press('Escape');
 }
}));

test('weekly sheet preserves failed revocation and copying falls back to the correct new URL',()=>harness(async page=>{
 let active=[{id:'old-share',expires_at:'2099-10-11T12:00:00Z'}],fail=true;
 await page.route(/\/api\/training-week(?:\?|$)/,r=>r.fulfill({json:{week_start:'2026-09-28',week_end:'2026-10-04',session_count:0,active_days:0,average_rpe:null,rpe_count:0,items:[]}}));
 await page.route('**/api/training-sessions',r=>r.fulfill({json:{items:[]}}));
 await page.route('**/api/training-week/shares?*',r=>r.fulfill({json:{items:active}}));
 await page.route('**/api/training-week/shares/old-share',r=>fail?r.fulfill({status:503,json:{detail:'Temporalmente no disponible'}}):r.fulfill({json:{ok:true}}));
 await page.route('**/api/training-week/shares',r=>r.fulfill({status:201,json:{id:'new-share',path:'/shared/week/'+'a'.repeat(43),expires_at:'2099-10-11T12:00:00Z'}}));
 await page.evaluate(()=>window.setupTraining());await page.locator('.weekly-disclosure > summary').press('Enter');await page.locator('.weekly-share-trigger').press('Enter');
 const sheet=page.getByRole('dialog');await sheet.getByRole('button',{name:'Revocar enlace',exact:true}).click();await sheet.getByText('Puedes reintentar la revocación.',{exact:false}).waitFor();assert.equal(await sheet.locator('.weekly-link-row').count(),1);
 await sheet.getByRole('button',{name:'Crear enlace para compartir',exact:true}).click();await sheet.getByRole('button',{name:'Copiar enlace',exact:true}).waitFor();
 await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw Error('Denied')}}}));
 await sheet.getByRole('button',{name:'Copiar enlace',exact:true}).click();assert.equal(await sheet.getByLabel('Enlace para compartir',{exact:true}).inputValue(),'http://localhost:18767/shared/week/'+'a'.repeat(43));
 await page.keyboard.press('Escape');
}));
